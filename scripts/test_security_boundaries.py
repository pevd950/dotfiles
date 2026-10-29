"""Exercise security boundaries with disposable repositories and synthetic values only."""
import os
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / '.agents/skills/ops/onepassword-project-setup/scripts/build-env-op.py'
PREFLIGHT = ROOT / '.config/zsh/custom/bin/onepassword-dev-preflight'
MEDIA = ROOT / '.agents/skills/development/babysit-pr/references/github-media-evidence.md'
DIAGNOSTICS = ROOT / '.agents/skills/development/gh-connectivity-preflight/scripts/git_diagnostics.py'


class IsolatedTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='dotfiles-security-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.env = {'HOME': str(self.home), 'ZDOTDIR': str(self.home),
                    'PATH': str(self.bin) + os.pathsep + '/usr/bin:/bin:/usr/sbin:/sbin',
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': str(self.home / '.gitconfig'),
                    'GIT_TERMINAL_PROMPT': '0', 'AGENT_HOST_ALIAS': 'fixture'}
        self.git = shutil.which('git')
        self.run_command([self.git, 'init', '-q', str(self.repo)])

    def run_command(self, args, **kwargs):
        return subprocess.run(args, env=self.env, cwd=self.repo, capture_output=True,
                              text=True, timeout=15, **kwargs)

    def stub(self, name, body):
        path = self.bin / name
        path.write_text('#!' + sys.executable + '\n' + body)
        path.chmod(0o700)
        return path


class EnvOutputTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.calls = self.root / 'op-calls'
        self.stub('op', "from pathlib import Path\n"
                  f"with Path({str(self.calls)!r}).open('a') as f: f.write('called\\n')\n"
                  "print('[]')\n")
        self.literal = 'CONFIG="hello world" # keep\nMULTI=\'one\ntwo\'\n'
        (self.repo / '.env').write_text(self.literal)

    def build(self, *args):
        return self.run_command([sys.executable, str(BUILDER), '--repo', str(self.repo),
                                 '--project', 'fixture', '--vault', 'Fixture', *args])

    def sentinel(self):
        path = self.root / 'startup'
        path.write_text('untouched\n')
        path.chmod(0o640)
        return path

    def assert_rejected(self, target, *args):
        result = self.build(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(target.read_text(), 'untouched\n')
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)
        self.assertFalse(self.calls.exists(), 'unsafe output must fail before provider access')

    def test_regular_output_and_existing_exclusions(self):
        exclude = self.repo / '.git/info/exclude'
        exclude.write_text('existing-entry\n')
        for _ in range(2):
            result = self.build()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(self.literal, (self.repo / '.env.op').read_text())
            self.assertEqual((self.repo / '.env.op').stat().st_mode & 0o777, 0o600)
        self.assertEqual(exclude.read_text().splitlines(), ['existing-entry', '.env.op', '.envrc'])

    def test_output_symlink_cannot_overwrite_startup(self):
        target = self.sentinel()
        (self.repo / '.env.op').symlink_to(target)
        (self.repo / '.env').write_text('CONFIG=$(touch ignored-marker)\n')
        self.assert_rejected(target)

    def test_dry_run_rejects_output_symlink(self):
        target = self.sentinel()
        (self.repo / '.env.op').symlink_to(target)
        self.assert_rejected(target, '--dry-run')

    def test_hardlinked_output_is_rejected(self):
        target = self.sentinel()
        os.link(target, self.repo / '.env.op')
        self.assert_rejected(target)

    def test_parent_symlink_is_rejected(self):
        target = self.sentinel()
        (self.repo / 'nested').symlink_to(self.root, target_is_directory=True)
        self.assert_rejected(target, '--out', 'nested/startup')

    def test_outside_output_is_rejected(self):
        target = self.sentinel()
        self.assert_rejected(target, '--out', '../startup')

    def test_exclusion_symlink_is_rejected_before_output_or_provider(self):
        target = self.sentinel()
        exclude = self.repo / '.git/info/exclude'
        exclude.unlink()
        exclude.symlink_to(target)
        self.assert_rejected(target)
        self.assertFalse((self.repo / '.env.op').exists())

    def test_dangling_symlink_does_not_create_target(self):
        target = self.root / 'absent'
        (self.repo / '.env.op').symlink_to(target)
        result = self.build()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())
        self.assertFalse(self.calls.exists())

    def test_nested_output_and_dry_run_remain_supported(self):
        (self.repo / 'config').mkdir()
        result = self.build('--out', 'config/local.env', '--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / 'config/local.env').exists())
        result = self.build('--out', 'config/local.env')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.literal, (self.repo / 'config/local.env').read_text())

    def test_linked_worktree_keeps_shared_exclusions_untouched(self):
        shutil.rmtree(self.repo / '.git')
        (self.repo / '.git').write_text('gitdir: /unopened/shared/metadata\n')
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(self.literal, (self.repo / '.env.op').read_text())

    def test_git_info_parent_symlink_is_rejected(self):
        target = self.sentinel()
        shutil.rmtree(self.repo / '.git/info')
        (self.root / 'exclude').symlink_to(target)
        (self.repo / '.git/info').symlink_to(self.root, target_is_directory=True)
        self.assert_rejected(target)

    def test_secret_reference_and_forced_literal_are_preserved(self):
        self.stub('op', 'import json, sys\n'
                  'if sys.argv[1:3] == ["item", "list"]:\n'
                  '    print(json.dumps([{"id": "fixture", "category": "API_CREDENTIAL"}]))\n'
                  'elif sys.argv[1:3] == ["item", "get"]:\n'
                  '    print(json.dumps({"title": "Fixture", "fields": [{"value": "synthetic-value", '
                  '"label": "credential", "type": "CONCEALED", "reference": "op://fixture/item/credential"}]}))\n'
                  'else: raise SystemExit("unexpected provider write")\n')
        (self.repo / '.env').write_text('API_TOKEN=synthetic-value\nCONFIG_TOKEN="literal" # retain\n')
        result = self.build('--config', 'CONFIG_TOKEN')
        self.assertEqual(result.returncode, 0, result.stderr)
        content = (self.repo / '.env.op').read_text()
        self.assertIn('API_TOKEN="op://fixture/item/credential"', content)
        self.assertIn('CONFIG_TOKEN="literal" # retain', content)
        self.assertNotIn('synthetic-value', content + result.stdout + result.stderr)

    def test_parent_swap_cannot_redirect_atomic_write(self):
        spec = importlib.util.spec_from_file_location('safe_output', BUILDER.with_name('safe_output.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parent = self.repo / 'nested'
        parent.mkdir()
        target = self.sentinel()
        output = module.SafeOutput(self.repo, 'nested/startup')
        self.addCleanup(output.close)
        parent.rename(self.repo / 'original-parent')
        parent.symlink_to(self.root, target_is_directory=True)
        output.write('new content')
        self.assertEqual(target.read_text(), 'untouched\n')
        self.assertEqual((self.repo / 'original-parent/startup').read_text(), 'new content')

    def test_destination_replaced_after_open_is_rejected(self):
        spec = importlib.util.spec_from_file_location('safe_output', BUILDER.with_name('safe_output.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        output = module.SafeOutput(self.repo, '.env.op')
        self.addCleanup(output.close)
        target = self.sentinel()
        (self.repo / '.env.op').symlink_to(target)
        with self.assertRaises(ValueError):
            output.write('new content')
        self.assertEqual(target.read_text(), 'untouched\n')


class CredentialOutputTests(IsolatedTest):
    def setUp(self):
        super().setUp()
        self.secret = 'SYNTHETIC-DO-NOT-DISPLAY'
        self.run_command([self.git, 'config', '--global', 'credential.helper',
                          '!printf "password=' + self.secret + '\\n"'])
        self.run_command([self.git, 'remote', 'add', 'origin',
                          'https://user:' + self.secret + '@example.invalid/private.git'])

    @unittest.skipUnless(shutil.which('zsh'), 'zsh required')
    def test_developer_preflight_does_not_print_helper(self):
        for name in ('op', 'codex', 'ssh', 'ssh-add', 'gh'):
            self.stub(name, 'raise SystemExit(1)\n')
        result = self.run_command([shutil.which('zsh'), '-f', str(PREFLIGHT)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(self.secret, result.stdout + result.stderr)
        self.assertIn('git credential.helper', result.stdout)
        self.assertRegex(result.stdout, r'git credential.helper\s+configured')

    def test_git_diagnostics_only_emit_classifications(self):
        result = self.run_command([sys.executable, str(DIAGNOSTICS)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(self.secret, result.stdout + result.stderr)
        self.assertNotIn('private.git', result.stdout + result.stderr)
        self.assertIn('https', result.stdout)
        self.assertIn('custom-shell-helper', result.stdout)

    def test_multiline_and_scoped_helpers_are_opaque(self):
        self.run_command([self.git, 'config', '--add', 'credential.https://example.invalid.helper',
                          'custom\n' + self.secret])
        self.run_command([self.git, 'config', '--add', 'credential.helper', 'osxkeychain'])
        result = self.run_command([sys.executable, str(DIAGNOSTICS)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(self.secret, result.stdout + result.stderr)
        self.assertIn('custom-helper', result.stdout)
        self.assertIn('osxkeychain', result.stdout)

    def test_probe_discards_output_and_disables_inherited_trace_files(self):
        trace = self.root / 'raw-trace'
        self.env.update(GIT_TRACE=str(trace), GIT_TRACE2_EVENT=str(trace), GIT_CURL_VERBOSE='1')
        self.stub('git', 'import os, sys\n'
                  'assert not any((k.startswith("GIT_TRACE") or k == "GIT_CURL_VERBOSE") and v != "0" for k, v in os.environ.items())\n'
                  f'print({self.secret!r}, file=sys.stderr)\n'
                  'if "ls-remote" in sys.argv:\n'
                  f'    print({self.secret!r})\n'
                  '    raise SystemExit(1)\n'
                  'raise SystemExit(1)\n')
        result = self.run_command([sys.executable, str(DIAGNOSTICS), '--probe'])
        self.assertEqual(result.returncode, 1)
        self.assertNotIn(self.secret, result.stdout + result.stderr)
        self.assertIn('origin transport probe: unavailable', result.stdout)
        self.assertFalse(trace.exists())

    def test_local_origin_transport_and_missing_helpers(self):
        self.run_command([self.git, 'config', '--global', '--unset-all', 'credential.helper'])
        self.run_command([self.git, 'remote', 'set-url', 'origin', str(self.repo / '.git')])
        result = self.run_command([sys.executable, str(DIAGNOSTICS), '--probe'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('origin transport probe: ok', result.stdout)
        self.assertIn('credential helpers: missing', result.stdout)

    def configure_trace(self):
        trace = self.root / 'configured-trace'
        self.run_command([self.git, 'config', '--global', 'trace2.configParams', 'credential.helper'])
        self.run_command([self.git, 'config', '--global', 'trace2.eventTarget', str(trace)])
        return trace

    def test_git_config_cannot_enable_sensitive_trace_capture(self):
        trace = self.configure_trace()
        result = self.run_command([sys.executable, str(DIAGNOSTICS)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(trace.exists(), 'Git configuration must not enable raw trace output')

    @unittest.skipUnless(shutil.which('zsh'), 'zsh required')
    def test_preflight_cannot_log_helpers_through_trace_configuration(self):
        for name in ('op', 'codex', 'ssh', 'ssh-add', 'gh'):
            self.stub(name, 'raise SystemExit(1)\n')
        trace = self.configure_trace()
        result = self.run_command([shutil.which('zsh'), '-f', str(PREFLIGHT)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(trace.exists(), 'Git configuration must not log helper values')


class MediaBodyTests(IsolatedTest):
    def test_documented_fetch_and_upload_do_not_follow_checkout_symlink(self):
        media = self.repo / 'evidence'
        media.mkdir()
        config = self.repo / '.git/config'
        before = config.read_bytes()
        (media / 'body.md').symlink_to(config)
        self.stub('gh', 'import pathlib, sys\n'
                  'if sys.argv[1:3] == ["pr", "view"]:\n'
                  '    print("[core]\\n    fsmonitor = ./payload.sh")\n'
                  'else:\n'
                  '    p = pathlib.Path(sys.argv[sys.argv.index("--body-file") + 1])\n'
                  '    assert p.is_absolute() and p.stat().st_mode & 0o077 == 0\n'
                  f'    pathlib.Path({str(self.root / "uploaded")!r}).write_text(p.read_text())\n'
                  f'    pathlib.Path({str(self.root / "body-path")!r}).write_text(str(p))\n')
        blocks = re.findall(r'```sh\n(.*?)```', MEDIA.read_text(), re.S)
        result = subprocess.run(['/bin/sh', '-c', blocks[0] + '\n' + blocks[1]],
                                env=self.env, cwd=media, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(config.read_bytes(), before)
        self.assertIn('fsmonitor', (self.root / 'uploaded').read_text())
        self.assertFalse(Path((self.root / 'body-path').read_text()).exists(), 'temporary body cleaned up')

    def test_failed_body_fetch_stops_before_upload(self):
        record = self.root / 'unexpected-upload'
        self.stub('gh', 'from pathlib import Path\nimport sys\n'
                  'if sys.argv[1:3] == ["pr", "edit"]:\n'
                  f'    Path({str(record)!r}).touch()\n'
                  'raise SystemExit(1)\n')
        blocks = re.findall(r'```sh\n(.*?)```', MEDIA.read_text(), re.S)
        result = self.run_command(['/bin/sh', '-c', blocks[0] + '\n' + blocks[1]])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(record.exists())


if __name__ == '__main__':
    unittest.main()
