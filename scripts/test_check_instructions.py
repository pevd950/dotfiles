import tempfile
from pathlib import Path
import unittest
import subprocess
from unittest.mock import patch

from check_instructions import local_links, metadata, validate, tracked_files


class InstructionChecks(unittest.TestCase):
    def test_yaml_handles_quotes_and_folded_descriptions(self):
        self.assertEqual(metadata('---\nname: sample\ndescription: >\n  Fix CI:\n  inspect first.\n---\n')['description'], 'Fix CI: inspect first.\n')

    def test_rejects_missing_empty_and_duplicate_metadata(self):
        for text in ('no header', '---\nname: x', '---\nname: x\ndescription: false\n---', '---\nname: x\nname: y\ndescription: z\n---'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                metadata(text)

    def test_links_ignore_examples_and_external_sources(self):
        text = '[local](references/a.md#section) [web](https://example.com) [anchor](#here)\n```md\n[example](missing.md)\n```\n`[code](fake.md)`\n\n[ref]: <reference%20file.md>\n'
        self.assertEqual(list(local_links(text)), ['reference file.md', 'references/a.md'])

    def test_duplicate_names_and_untracked_targets_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for name in ('one', 'two'):
                p = root / name / 'SKILL.md'
                p.parent.mkdir()
                p.write_text('---\nname: same\ndescription: example\n---\n[missing](missing.md)\n')
                paths.append(p)
            (paths[0].parent / 'missing.md').write_text('Untracked files cannot satisfy a published link.')
            errors = validate(root, paths)
            self.assertEqual(len(errors), 3)
            self.assertTrue(any('duplicate skill name' in error for error in errors))

    def test_tracked_reference_resolves(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'SKILL.md'
            p.write_text('---\nname: example\ndescription: example\n---\n[reference](reference.md)\n')
            ref = root / 'reference.md'
            ref.write_text('Reference')
            self.assertEqual(validate(root, [p, ref]), [])

    def test_invocation_metadata_rejects_string_boolean(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'agents/openai.yaml'
            p.parent.mkdir()
            p.write_text('policy:\n  allow_implicit_invocation: "false"\n')
            self.assertTrue(validate(root, [p]))
            p.write_text('policy:\n  allow_implicit_invocation: false\n')
            self.assertEqual(validate(root, [p]), [])

    def test_reference_can_target_other_tracked_repository_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            p = root / 'SKILL.md'
            p.write_text('---\nname: example\ndescription: example\n---\n[script](check.py)\n')
            target = root / 'check.py'
            target.write_text('# Checker')
            self.assertEqual(validate(root, [p], [p, target]), [])

class ReviewRegressions(unittest.TestCase):
    def test_commonmark_titles_parentheses_and_code(self):
        text = "[one](missing.md 'details') [two](guide(v2).md \"title\") [three](last.md (title))"
        self.assertEqual(list(local_links(text)), ['missing.md', 'guide(v2).md', 'last.md'])
        self.assertEqual(list(local_links('    [code](ignored.md)\n')), [])

    def test_external_symlink_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            root = base / 'repo'
            root.mkdir()
            secret = base / 'outside.md'
            secret.write_text('PRIVATE SENTINEL')
            link = root / 'SKILL.md'
            link.symlink_to(secret)
            with patch.object(Path, 'read_text', side_effect=AssertionError('must not read')):
                errors = validate(root, [link])
            self.assertEqual(len(errors), 1)
            self.assertNotIn('PRIVATE SENTINEL', str(errors))

    def test_third_duplicate_names_original(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = []
            for name in ('first', 'second', 'third'):
                p = root / name / 'SKILL.md'
                p.parent.mkdir()
                p.write_text('---\nname: same\ndescription: example\n---\n')
                paths.append(p)
            errors = validate(root, paths)
            self.assertEqual(len(errors), 2)
            self.assertTrue(all('(first/SKILL.md)' in e for e in errors))

    def test_clone_and_yadm_index_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve() / 'worktree'
            repo = Path(folder).resolve() / 'repo.git'
            root.mkdir()
            subprocess.run(['git', 'init', '-q', '--separate-git-dir', str(repo), str(root)], check=True)
            (root / 'AGENTS.md').write_text('Instructions')
            subprocess.run(['git', '-C', str(root), 'add', 'AGENTS.md'], check=True)
            self.assertIn('AGENTS.md', tracked_files(root))
            (root / '.git').unlink()
            subprocess.run(['git', '--git-dir='+str(repo), 'config', 'core.worktree', str(root)], check=True)
            real = subprocess.check_output
            def discovery(command, **kwargs):
                if command == ['yadm', 'introspect', 'repo']:
                    env = kwargs['env']
                    count = int(env['GIT_CONFIG_COUNT']) - 1
                    self.assertEqual(env[f'GIT_CONFIG_VALUE_{count}'], 'false')
                    return str(repo) + '\n'
                return real(command, **kwargs)
            with patch('check_instructions.subprocess.check_output', side_effect=discovery):
                self.assertIn('AGENTS.md', tracked_files(root))
                with self.assertRaises(ValueError):
                    tracked_files(root / 'wrong')


if __name__ == '__main__':
    unittest.main()
