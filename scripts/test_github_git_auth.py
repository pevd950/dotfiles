import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).parent
HELPER = SCRIPT_DIR / "github-credential-helper.py"
SETUP = SCRIPT_DIR / "setup-github-git-auth.py"
spec = importlib.util.spec_from_file_location("github_auth_helper", HELPER)
helper_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper_module)
setup_spec = importlib.util.spec_from_file_location("github_auth_setup", SETUP)
setup_module = importlib.util.module_from_spec(setup_spec)
setup_spec.loader.exec_module(setup_module)


class GitHubGitAuthTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="github-git-auth-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.gh = self.bin / "gh"
        self.gh.write_text(
            f"#!{sys.executable}\n"
            "import os, pathlib, sys\n"
            "assert not os.environ.get('GH_TOKEN')\n"
            "assert not os.environ.get('GITHUB_TOKEN')\n"
            "assert os.environ.get('GH_PROMPT_DISABLED') == '1'\n"
            "assert not sys.stdin.isatty()\n"
            "root = pathlib.Path(__file__).parent.parent\n"
            "if (root / 'deny').exists():\n"
            "    print('secret-provider-diagnostic', file=sys.stderr)\n"
            "    sys.exit(1)\n"
            "if sys.argv[1:3] == ['api', 'user']:\n"
            "    print('fixture-user')\n"
            "else:\n"
            "    assert sys.argv[1:] == ['auth', 'git-credential', 'get']\n"
            "    assert 'host=github.com' in sys.stdin.read()\n"
            "    print('username=fixture-user\\npassword=fixture-secret\\n')\n"
        )
        self.gh.chmod(0o700)
        self.env = {"HOME": str(self.home), "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                    "GH_TOKEN": "ignored-fixture-override", "GITHUB_TOKEN": "ignored-fixture-override",
                    "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"}
        self.git = shutil.which("git")
        self.call_git("init", "-q")
        self.call_git("remote", "add", "origin", "https://github.com/example/private.git")

    def call_git(self, *args, input_data=None, check=True):
        return subprocess.run([self.git, "-C", str(self.repo), *args], input=input_data,
                              capture_output=True, text=True, env=self.env, check=check)

    def helper(self, operation="get", request="protocol=https\nhost=github.com\n\n"):
        return subprocess.run([sys.executable, str(HELPER), "--gh", str(self.gh), operation],
                              input=request, capture_output=True, text=True, env=self.env, timeout=5)

    def test_get_uses_existing_gh_identity_without_shell_tokens(self):
        result = self.helper()
        self.assertEqual(result.returncode, 0)
        self.assertIn("password=fixture-secret", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_store_and_erase_do_not_change_existing_identity(self):
        self.gh.unlink()
        for operation in ("store", "erase", "capability"):
            with self.subTest(operation=operation):
                result = self.helper(operation)
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))

    def test_unsupported_host_fails_without_calling_provider(self):
        self.gh.unlink()
        result = self.helper(request="protocol=https\nhost=unrelated.example\n\n")
        self.assertEqual(result.stdout, "quit=1\n\n")

    def test_provider_error_does_not_leak_or_prompt(self):
        (self.root / "deny").touch()
        result = self.helper()
        self.assertEqual(result.stdout, "quit=1\n\n")
        self.assertNotIn("secret-provider-diagnostic", result.stdout + result.stderr)

    def test_git_does_not_fall_back_after_missing_credential(self):
        (self.root / "deny").touch()
        sentinel = self.root / "unexpected-fallback"
        bounded = "!" + shlex.join([sys.executable, str(HELPER), "--gh", str(self.gh)])
        self.call_git("config", "credential.https://github.com.helper", "")
        self.call_git("config", "--add", "credential.https://github.com.helper", bounded)
        self.call_git("config", "--add", "credential.https://github.com.helper", f"!touch {shlex.quote(str(sentinel))}")
        self.call_git("config", "core.askPass", f"touch {shlex.quote(str(sentinel))}")
        result = self.call_git("credential", "fill", input_data="protocol=https\nhost=github.com\n\n", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(sentinel.exists())
        self.assertNotIn("secret-provider-diagnostic", result.stdout + result.stderr)

    def test_timeout_is_bounded_and_stops_its_child(self):
        sentinel = self.root / "child-finished"
        child = f"import time,pathlib; time.sleep(1); pathlib.Path({str(sentinel)!r}).touch()"
        parent = f"import subprocess,time; subprocess.Popen([{sys.executable!r}, '-c', {child!r}]); time.sleep(5)"
        start = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            helper_module.bounded_run([sys.executable, "-c", parent], timeout=0.2)
        self.assertLess(time.monotonic() - start, 1.0)
        time.sleep(1.1)
        self.assertFalse(sentinel.exists())

    def setup_script(self, *args):
        # Avoid network while still exercise real config parsing/writes. The live
        # acceptance test separately reads a real private GitHub origin.
        git_proxy = self.bin / "git-proxy"
        git_proxy.write_text(
            f"#!{sys.executable}\nimport os,sys\n"
            "if 'ls-remote' in sys.argv:\n"
            "    print('fixture-head HEAD')\n"
            "    sys.exit(0)\n"
            f"os.execv({self.git!r}, [{self.git!r}] + sys.argv[1:])\n"
        )
        git_proxy.chmod(0o700)
        return subprocess.run([sys.executable, str(SETUP), "--repository", str(self.repo),
                               "--git", str(git_proxy), *args], capture_output=True, text=True, env=self.env, timeout=5)

    def test_configure_is_idempotent_preserves_other_hosts_and_survives_no_global_config(self):
        self.call_git("config", "credential.https://elsewhere.example.helper", "existing-provider")
        first = self.setup_script("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        config = (self.repo / ".git/config").read_bytes()
        second = self.setup_script("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.repo / ".git/config").read_bytes(), config)
        self.assertEqual(self.call_git("config", "credential.https://elsewhere.example.helper").stdout.strip(), "existing-provider")
        self.assertFalse((self.home / ".gitconfig").exists())
        installed = self.home / ".local/libexec/dotfiles/github-credential-helper.py"
        self.assertEqual(installed.stat().st_mode & 0o777, 0o700)
        self.env["GIT_CONFIG_GLOBAL"] = "/dev/null"
        result = self.call_git("credential", "fill", input_data="protocol=https\nhost=github.com\n\n")
        self.assertIn("password=fixture-secret", result.stdout)
        self.assertNotIn(b"fixture-secret", config)

    def test_missing_auth_does_not_change_config_or_install_helper(self):
        (self.root / "deny").touch()
        before = (self.repo / ".git/config").read_bytes()
        result = self.setup_script("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.repo / ".git/config").read_bytes(), before)
        self.assertFalse((self.home / ".local").exists())
        self.assertNotIn("secret-provider-diagnostic", result.stdout + result.stderr)

    def test_existing_install_needs_no_home_directory_writes(self):
        first = self.setup_script("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        arguments = [str(SETUP), "--repository", str(self.repo),
                     "--git", str(self.bin / "git-proxy"), "--apply"]
        # Model an agent that may configure this checkout but cannot modify the
        # already installed helper in the user's home directory.
        with patch.dict(os.environ, self.env, clear=True), patch.object(sys, "argv", arguments), \
                patch.object(Path, "mkdir", side_effect=PermissionError("protected install")), \
                patch.object(os, "chmod", side_effect=PermissionError("protected install")):
            self.assertEqual(setup_module.main(), 0)

    def test_unsupported_remote_is_not_changed(self):
        self.call_git("remote", "set-url", "origin", "https://username:fixture-secret@github.com/example/repo.git")
        before = (self.repo / ".git/config").read_bytes()
        result = self.setup_script("--apply")
        self.assertEqual(result.returncode, 1)
        self.assertEqual((self.repo / ".git/config").read_bytes(), before)
        self.assertNotIn("fixture-secret", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
