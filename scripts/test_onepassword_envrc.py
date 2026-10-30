"""Exercise the real project envrc with isolated credentials and a fake op CLI."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TEMPLATE = Path(__file__).resolve().parents[1] / '.agents/skills/ops/onepassword-project-setup/templates/envrc'


class ProjectEnvironmentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='project-env-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.project = self.root / 'project'
        self.project.mkdir()
        self.token = self.home / '.config/op/sa/example-local.token'
        self.token.parent.mkdir(parents=True)
        self.token.write_text('fixture-bootstrap-token')
        self.token.chmod(0o600)
        self.envrc = self.project / '.envrc'
        self.envrc.write_text(TEMPLATE.read_text().replace('PROJECT', 'example'))
        (self.project / '.env.op').write_text('OPENAI_API_KEY=op://Fixture/key/credential\n')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.op = self.bin / 'op'
        self.op.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
root=pathlib.Path(os.environ['FIXTURE_ROOT'])
(root/'op-called').touch()
assert os.environ['OP_SERVICE_ACCOUNT_TOKEN']=='fixture-bootstrap-token'
if os.environ.get('FIXTURE_FAIL'):
    print('touch '+str(root/'injected'))
    sys.exit(17)
assert '--no-masking' in sys.argv
assert '--env-file' in sys.argv and '.env.op' in sys.argv
os.environ['OPENAI_API_KEY']=os.environ['FIXTURE_SECRET']
os.environ['ANTHROPIC_API_KEY']='fixture-anthropic-key'
os.environ['GEMINI_API_KEY']='fixture-gemini-key'
child=sys.argv[sys.argv.index('--')+1:]
os.execvp(child[0], child)
''')
        self.op.chmod(0o755)
        self.child = self.root / 'child.py'
        self.child.write_text('''import os,pathlib
root=pathlib.Path(os.environ['FIXTURE_ROOT'])
(root/'child-called').touch()
assert os.environ['OPENAI_API_KEY']==os.environ['FIXTURE_SECRET']
assert os.environ['ANTHROPIC_API_KEY']=='fixture-anthropic-key'
assert os.environ['GEMINI_API_KEY']=='fixture-gemini-key'
assert os.environ['OP_SERVICE_ACCOUNT_TOKEN']=='fixture-bootstrap-token'
assert not (root/'injected').exists()
print('resolved environment verified')
''')
        self.env = {
            'HOME': str(self.home),
            'PATH': str(self.bin)+os.pathsep+str(Path(sys.executable).parent)+os.pathsep+os.defpath,
            'FIXTURE_ROOT': str(self.root),
            'FIXTURE_SECRET': "quote'\" $() `text`\nmultiline café $(touch "+str(self.root/'injected')+")",
            'FIXTURE_PYTHON': sys.executable,
        }

    def load(self):
        return subprocess.run([shutil.which('bash'), '-c', '''
has() { command -v "$1" >/dev/null 2>&1; }
watch_file() { :; }
log_error() { printf '%s\\n' "$*" >&2; }
source .envrc || exit $?
exec "$FIXTURE_PYTHON" "$FIXTURE_ROOT/child.py"
'''], cwd=self.project, env=self.env, capture_output=True, text=True, timeout=15)

    def test_resolves_values_for_ordinary_children_without_shell_injection(self):
        result = self.load()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'resolved environment verified')
        self.assertNotIn(self.env['FIXTURE_SECRET'], result.stdout+result.stderr)
        self.assertFalse((self.root/'injected').exists())

    def test_failed_resolution_never_evaluates_partial_output_or_runs_child(self):
        self.env['FIXTURE_FAIL']='1'
        result = self.load()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'injected').exists())
        self.assertFalse((self.root/'child-called').exists())

    def test_readable_token_is_rejected_before_op_or_the_child_runs(self):
        self.token.chmod(0o644)
        result = self.load()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'op-called').exists())
        self.assertFalse((self.root/'child-called').exists())

    def test_missing_token_is_rejected_before_op_or_the_child_runs(self):
        self.token.unlink()
        result = self.load()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'op-called').exists())
        self.assertFalse((self.root/'child-called').exists())

    def test_missing_reference_file_is_rejected_before_op_or_the_child_runs(self):
        (self.project/'.env.op').unlink()
        result = self.load()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root/'op-called').exists())
        self.assertFalse((self.root/'child-called').exists())


if __name__ == '__main__':
    unittest.main()
