"""The host shared-keys renderer writes stored values as data that shells can source safely."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / '.agents/skills/ops/onepassword-project-setup/scripts/setup-host-agent-env.sh'
ZSH = shutil.which('zsh')

FAKE_OP = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Stand-in for `op inject -i IN -o OUT --force`: replaces each reference with its mapped value."""
    import json, os, re, sys
    args = sys.argv[1:]
    source, target = args[args.index('-i') + 1], args[args.index('-o') + 1]
    values = json.load(open(os.environ['FAKE_OP_MAP']))
    text = open(source).read()
    text = re.sub(r'op://[^\\n]*', lambda m: values.get(m.group(0), m.group(0)), text)
    open(target, 'w').write(text)
''')


@unittest.skipUnless(ZSH, 'zsh required')
class HostAgentEnvTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='dotfiles-agent-env-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.bin = self.root / 'bin'
        self.home.mkdir()
        self.bin.mkdir()
        for name, body in (('op', FAKE_OP), ('launchctl', '#!/bin/sh\nexit 0\n'), ('systemctl', '#!/bin/sh\nexit 0\n')):
            path = self.bin / name
            path.write_text(body)
            path.chmod(0o755)
        self.map = self.root / 'values.json'
        self.map.write_text('{}')
        self.env = {'HOME': str(self.home), 'PATH': f'{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin', 'FAKE_OP_MAP': str(self.map)}
        token = self.home / '.config/op/sa/testhost-agents.token'
        token.parent.mkdir(parents=True)
        token.write_text('synthetic-token')
        subprocess.run(['bash', str(SETUP), '--alias', 'testhost'], env=self.env, check=True, capture_output=True, text=True)
        self.template = self.home / '.config/op/env/testhost-agent.env.tpl'
        self.rendered = self.home / '.config/op/env/testhost-agent.env'
        self.refresh = self.home / '.local/bin/refresh-agent-env'

    def render(self, template, values):
        self.template.write_text(template)
        self.map.write_text(json.dumps(values))
        return subprocess.run([str(self.refresh)], env=self.env, capture_output=True, text=True)

    def loaded(self, names, shell='zsh'):
        """What a new shell exports after reading the installed loader (zsh) or sourcing the file (bash)."""
        prints = ' '.join(f'"${{{name}-<unset>}}"' for name in names)
        if shell == 'zsh':
            command = [ZSH, '-f', '-c', f'source "$HOME/.zshenv.local"; printf "%s\\0" {prints}']
        else:
            command = ['bash', '-c', f'set -a; . "{self.rendered}"; set +a; printf "%s\\0" {prints}']
        result = subprocess.run(command, env=self.env, capture_output=True, text=True, check=True)
        return dict(zip(names, result.stdout.split('\0')))

    def test_stored_values_load_exactly_and_never_run(self):
        marker = self.root / 'EXECUTED'
        values = {
            'op://Vault One/id1/credential': 'plain-token_123',
            'op://Vault One/id2/credential': f'$(touch {marker})',
            'op://Vault One/id3/credential': f'`touch {marker}`',
            'op://Vault One/id4/credential': f'x; touch {marker}; y',
            'op://Vault One/id5/credential': 'it\'s "quoted" $HOME \\ # ~ * & | < > ( ) !',
            'op://Vault One/id6/credential': '  spaces kept  ',
        }
        names = ['PLAIN', 'SUBSHELL', 'BACKTICK', 'SEMICOLON', 'MIXED', 'SPACES']
        template = ''.join(f'{name}={ref}\n' for name, ref in zip(names, values))
        result = self.render(template, values)
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = dict(zip(names, values.values()))
        self.assertEqual(self.loaded(names), expected)
        self.assertEqual(self.loaded(names, shell='bash'), expected)
        self.assertFalse(marker.exists(), 'a stored value ran as shell code')
        self.assertEqual(self.rendered.stat().st_mode & 0o777, 0o600)

    def test_template_conveniences_are_not_part_of_the_value(self):
        template = textwrap.dedent('''\
            # a comment line

            ONE=op://Vault One/id1/credential
            export TWO=op://Vault One/id2/credential
            THREE="op://Vault One/id3/credential"  # Provider API
            FOUR=op://Vault One/id4/credential  # trailing title
            FIVE=literal-value
        ''')
        values = {f'op://Vault One/id{n}/credential': f'value-{n}' for n in range(1, 5)}
        result = self.render(template, values)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.loaded(['ONE', 'TWO', 'THREE', 'FOUR', 'FIVE']),
                         {'ONE': 'value-1', 'TWO': 'value-2', 'THREE': 'value-3', 'FOUR': 'value-4', 'FIVE': 'literal-value'})

    def assert_refused(self, template, values, message):
        good = self.render('KEEP=op://Vault One/id1/credential\n', {'op://Vault One/id1/credential': 'previous'})
        self.assertEqual(good.returncode, 0, good.stderr)
        before = self.rendered.read_text()
        result = self.render(template, values)
        self.assertEqual(result.returncode, 1)
        self.assertIn(message, result.stderr)
        self.assertIn('keeping previous file', result.stderr)
        self.assertEqual(self.rendered.read_text(), before)
        self.assertEqual(list(self.rendered.parent.glob('testhost-agent.env.*')), [self.template])

    def test_value_spanning_lines_is_refused(self):
        ref = 'op://Vault One/id1/credential'
        self.assert_refused(f'A={ref}\n', {ref: 'first\nINJECTED=second'}, 'spans several lines')

    def test_unresolved_reference_is_refused(self):
        self.assert_refused('A=op://Vault One/missing/credential\n', {}, 'unresolved reference for A')

    def test_line_that_is_not_an_assignment_is_refused(self):
        self.assert_refused('touch /tmp/should-not-run\n', {}, 'not NAME=reference')

    def test_duplicate_variable_is_refused(self):
        ref = 'op://Vault One/id1/credential'
        self.assert_refused(f'A={ref}\nA={ref}\n', {ref: 'x'}, 'appears twice')


if __name__ == '__main__':
    unittest.main()
