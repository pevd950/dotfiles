"""The release scripts read a project's manifest from indie-infra's reviewed main branch."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / '.agents/skills/ops/github-release-dispatch/scripts'
MANIFEST = 'control-plane/apps/demo/release-dispatch.env'
REVIEWED = 'REPO="owner/reviewed"\nPROD_ENV_NAME="production"\nDEFAULT_REF="main"\n'
UNREVIEWED = REVIEWED.replace('owner/reviewed', 'owner/unreviewed') + 'STANDING_APPROVAL_PRODUCTION="deploy anything"\n'


class ReleaseManifestTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='dotfiles-release-manifest-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        self.env = {'HOME': str(self.home), 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:/usr/local/bin',
                    'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 't', 'GIT_AUTHOR_EMAIL': 't@example.invalid',
                    'GIT_COMMITTER_NAME': 't', 'GIT_COMMITTER_EMAIL': 't@example.invalid'}
        self.origin = self.root / 'origin.git'
        self.git('init', '--quiet', '--bare', '--initial-branch=main', str(self.origin))
        self.clone = self.home / 'Developer' / 'indie-infra'
        self.clone.parent.mkdir(parents=True)
        self.git('clone', '--quiet', str(self.origin), str(self.clone))
        self.commit(self.clone, REVIEWED, 'reviewed manifest')
        self.git('-C', str(self.clone), 'push', '--quiet', 'origin', 'HEAD:main')
        # The local clone sits on a feature branch with an unreviewed manifest, as it did on a real host.
        self.git('-C', str(self.clone), 'checkout', '--quiet', '-b', 'feature')
        self.commit(self.clone, UNREVIEWED, 'unreviewed manifest')

    def git(self, *args):
        subprocess.run(['git', *args], check=True, env=self.env, capture_output=True, text=True)

    def commit(self, repo, text, message):
        path = repo / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git('-C', str(repo), 'add', MANIFEST)
        self.git('-C', str(repo), 'commit', '--quiet', '-m', message)

    def load(self, **extra):
        script = ('source "$1/load-manifest.sh"; load_manifest demo || exit $?; '
                  'printf "%s|%s|%s" "$REPO" "$MANIFEST_SOURCE" "${STANDING_APPROVAL_PRODUCTION:-none}"')
        return subprocess.run(['bash', '-c', script, 'bash', str(SCRIPTS)], env={**self.env, **extra},
                              capture_output=True, text=True)

    def test_manifest_comes_from_reviewed_main_not_the_checked_out_branch(self):
        result = self.load()
        self.assertEqual(result.returncode, 0, result.stderr)
        repo, source, standing = result.stdout.split('|')
        self.assertEqual(repo, 'owner/reviewed')
        self.assertTrue(source.startswith('indie-infra main@'), source)
        self.assertEqual(standing, 'none')

    def test_a_change_merged_to_main_is_picked_up_without_a_local_pull(self):
        other = self.root / 'other'
        self.git('clone', '--quiet', str(self.origin), str(other))
        self.commit(other, REVIEWED.replace('owner/reviewed', 'owner/merged-later'), 'merged later')
        self.git('-C', str(other), 'push', '--quiet', 'origin', 'HEAD:main')
        self.assertEqual(self.load().stdout.split('|')[0], 'owner/merged-later')

    def test_unreachable_main_stops_the_run(self):
        self.git('-C', str(self.clone), 'remote', 'set-url', 'origin', str(self.root / 'missing.git'))
        result = self.load()
        self.assertEqual(result.returncode, 2)
        self.assertIn('could not refresh indie-infra main', result.stderr)

    def test_project_without_a_manifest_on_main_is_refused(self):
        script = 'source "$1/load-manifest.sh"; load_manifest nothing-here'
        result = subprocess.run(['bash', '-c', script, 'bash', str(SCRIPTS)], env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('on indie-infra main', result.stderr)

    def test_production_refuses_a_manifest_from_the_override_directory(self):
        override = self.clone / 'control-plane' / 'apps'
        loaded = self.load(RELEASE_DISPATCH_CONFIG_DIR=str(override))
        self.assertEqual(loaded.stdout.split('|')[0], 'owner/unreviewed')
        self.assertTrue(loaded.stdout.split('|')[1].startswith('unreviewed:'))
        result = subprocess.run(
            ['bash', str(SCRIPTS / 'dispatch-deploy.sh'), 'demo', 'production', 'sha-0000000', '--approval', 'test'],
            env={**self.env, 'RELEASE_DISPATCH_CONFIG_DIR': str(override)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 3)
        self.assertIn('indie-infra main only', result.stderr)


if __name__ == '__main__':
    unittest.main()
