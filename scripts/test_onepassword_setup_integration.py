"""Run developer setup in disposable homes with synthetic external providers."""
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess
import tempfile
import tomllib
import unittest


SCRIPT = Path(__file__).with_name("setup-1password-dev.zsh")
ZSH = shutil.which("zsh")
SSH = shutil.which("ssh")
SOCKETS = {
    "macos": "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock",
    "linux": "~/.1password/agent.sock",
}


def expanded_socket(socket):
    # ssh -G expands ~ through the account database, not a subprocess HOME.
    # Only inspect the resulting string; fake provider functions never open it.
    return pwd.getpwuid(os.getuid()).pw_dir + socket[1:]


@unittest.skipUnless(ZSH and SSH, "zsh and OpenSSH are required")
class OnePasswordSetupIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="onepassword-setup-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.log = self.root / "provider.log"
        self.protocol = self.root / "protocol"
        self.protocol.write_text("https\n")
        self.library = self.root / "setup-functions.zsh"
        source, entry, _ = SCRIPT.read_text().rpartition('\nmain "$@"')
        self.assertTrue(entry, "the real entry point must not run before providers are isolated")
        self.library.write_text(source + "\n")
        self.agent_config = self.home / ".config/1Password/ssh/agent.toml"
        self.ssh_config = self.home / ".ssh/config"
        self.ssh_config.parent.mkdir(mode=0o700)
        self.ssh_config.write_text(
            "Host restricted\n  IdentityAgent none\n"
            "  IdentityFile /tmp/fixture-restricted.pub\n  IdentitiesOnly yes\n"
            "Host alternate\n  IdentityAgent /tmp/fixture-alternate.sock\n"
            "Host github.com\n  User git\n"
            "  IdentityFile /tmp/fixture-github.pub\n  IdentitiesOnly yes\n")
        # Do not inherit real auth variables or provider search paths.
        self.env = {
            "PATH": "/usr/bin:/bin", "HOME": str(self.home),
            "FIXTURE_SCRIPT": str(self.library), "FIXTURE_LOG": str(self.log),
            "FIXTURE_PROTOCOL": str(self.protocol),
        }

    def setup_host(self, os_name="macos", *, installed=True, interactive=False,
                   dry_run=False, keys=False, login=False, inbound=False, vault=None):
        env = dict(self.env, FIXTURE_OS=os_name,
                   FIXTURE_INSTALLED=str(int(installed)),
                   FIXTURE_INTERACTIVE=str(int(interactive)),
                   FIXTURE_KEYS=str(int(keys)), FIXTURE_LOGIN=str(int(login)),
                   ONEPASSWORD_SETUP_DRY_RUN=str(int(dry_run)))
        if inbound:
            env["SSH_CONNECTION"] = "fixture inbound session"
        if vault is not None:
            env["ONEPASSWORD_SSH_KEY_VAULT"] = vault
        # Only the provider/installation boundaries are stubbed. main(), CLI detection,
        # vault conversion, SSH generation, socket mapping and GitHub policy stay real.
        script = r'''
source "$FIXTURE_SCRIPT"
OS="$FIXTURE_OS"
INTERACTIVE="$FIXTURE_INTERACTIVE"
onepassword_app_installed() { [[ "$FIXTURE_INSTALLED" == 1 ]]; }
op() {
  print -r -- "op:$*" >> "$FIXTURE_LOG"
  case "$1" in
    --version) print fixture-version ;;
    vault) print '{"id":"fixture-vault-id"}' ;;
    *) return 91 ;;
  esac
}
ensure_codex_mcp() {
  [[ -s "$HOME/.config/1Password/ssh/agent.toml" ]] || [[ "$DRY_RUN" == 1 ]] || return 92
  print -r -- "mcp:checked" >> "$FIXTURE_LOG"
}
ssh_agent_has_keys() {
  print -r -- "agent:$1" >> "$FIXTURE_LOG"
  [[ "$FIXTURE_KEYS" == 1 ]]
}
github_ssh_login_ready() {
  print -r -- "github:login" >> "$FIXTURE_LOG"
  [[ "$FIXTURE_LOGIN" == 1 ]]
}
gh() {
  print -r -- "gh:$*" >> "$FIXTURE_LOG"
  case "$1 $2" in
    "config get") cat "$FIXTURE_PROTOCOL" ;;
    "config set") print -r -- "$4" > "$FIXTURE_PROTOCOL" ;;
    *) return 93 ;;
  esac
}
main
'''
        return subprocess.run([ZSH, "-f", "-c", script], env=env,
                              text=True, capture_output=True, check=True, timeout=15)

    def effective_ssh(self, host, *, inbound=False):
        env = dict(self.env)
        if inbound:
            env["SSH_CLIENT"] = "fixture inbound session"
        result = subprocess.run([SSH, "-G", "-F", str(self.ssh_config), host],
                                env=env, check=True, text=True,
                                capture_output=True, timeout=10)
        settings = {}
        for line in result.stdout.splitlines():
            key, _, value = line.partition(" ")
            settings.setdefault(key, []).append(value)
        return settings

    def snapshot(self):
        return {str(path.relative_to(self.home)): (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
                for path in self.home.rglob("*") if path.is_file()}

    def test_main_keeps_vault_level_setup_and_host_key_selection_on_both_platforms(self):
        for os_name, socket in SOCKETS.items():
            with self.subTest(platform=os_name):
                self.setup_host(os_name)
                self.assertEqual(tomllib.loads(self.agent_config.read_text())["ssh-keys"],
                                 [{"vault": "Servers"}])
                self.assertEqual(stat.S_IMODE(self.agent_config.stat().st_mode), 0o600)
                self.assertIn(f'IdentityAgent "{socket}"', self.ssh_config.read_text())
                self.assertEqual(self.effective_ssh("restricted")["identityagent"], ["none"])
                self.assertEqual(self.effective_ssh("restricted")["identitiesonly"], ["yes"])
                self.assertIn("/tmp/fixture-restricted.pub",
                              self.effective_ssh("restricted")["identityfile"])
                self.assertEqual(self.effective_ssh("alternate")["identityagent"],
                                 ["/tmp/fixture-alternate.sock"])
                self.assertEqual(self.effective_ssh("github.com")["identitiesonly"], ["yes"])
                self.assertIn("/tmp/fixture-github.pub",
                              self.effective_ssh("github.com")["identityfile"])
                self.assertEqual(self.effective_ssh("github.com")["identityagent"], [expanded_socket(socket)])
                if os_name == "macos":
                    self.assertEqual((self.home / ".config/op/plugins.sh").read_text(),
                                     "export OP_PLUGIN_ALIASES_SOURCED=1\n")
                first = self.snapshot()
                self.setup_host(os_name)
                self.assertEqual(first, self.snapshot())
        self.assertNotIn("op:vault", self.log.read_text())

    def test_vault_conversion_preserves_other_scopes_and_backup(self):
        original = (
            '[[ssh-keys]] # current managed vault\nvault = "Servers" # keep once\n'
            '[[ssh-keys]]\nvault = "fixture-vault-id"\n'
            '[[ssh-keys]]\nitem = "obsolete-fixture-item"\nvault = "Servers"\n'
            '[[ssh-keys]] # independent vault\nvault = "Other fixture vault"\n'
            '[[ssh-keys]]\naccount = "fixture-account"\n')
        self.agent_config.parent.mkdir(parents=True)
        self.agent_config.write_text(original)
        self.setup_host(interactive=True)
        entries = tomllib.loads(self.agent_config.read_text())["ssh-keys"]
        self.assertEqual(entries, [{"vault": "Servers"}, {"vault": "Other fixture vault"},
                                   {"account": "fixture-account"}])
        backup = self.agent_config.with_name("agent.toml.bak")
        self.assertEqual(backup.read_text(), original)
        first = self.snapshot()
        self.setup_host(interactive=True)
        self.assertEqual(first, self.snapshot())
        self.assertIn("op:vault get Servers --format json", self.log.read_text())

    def test_custom_vault_and_existing_plugin_file_remain_usable(self):
        plugins = self.home / ".config/op/plugins.sh"
        plugins.parent.mkdir(parents=True)
        original = "# Fixture user-owned plugin settings\nexport FIXTURE_PLUGIN=1\n"
        plugins.write_text(original)
        self.setup_host(vault="Fixture development keys")
        self.assertEqual(tomllib.loads(self.agent_config.read_text())["ssh-keys"],
                         [{"vault": "Fixture development keys"}])
        self.assertEqual(plugins.read_text(), original)
        self.assertNotIn("op:vault", self.log.read_text())

    def test_inbound_session_keeps_forwarded_agent_and_vault_setup(self):
        for os_name in SOCKETS:
            with self.subTest(platform=os_name):
                self.setup_host(os_name, inbound=True)
                self.assertEqual(tomllib.loads(self.agent_config.read_text())["ssh-keys"],
                                 [{"vault": "Servers"}])
                self.assertNotIn("identityagent", self.effective_ssh("github.com", inbound=True))
                self.assertEqual(self.effective_ssh("restricted", inbound=True)["identityagent"], ["none"])

    def test_app_removal_keeps_vault_and_explicit_policy_without_fallback(self):
        for os_name in SOCKETS:
            with self.subTest(platform=os_name):
                self.setup_host(os_name)
                vault = self.agent_config.read_bytes()
                self.setup_host(os_name, installed=False)
                self.assertEqual(self.agent_config.read_bytes(), vault)
                self.assertNotIn("identityagent", self.effective_ssh("github.com"))
                self.assertEqual(self.effective_ssh("restricted")["identityagent"], ["none"])
                self.assertEqual(self.protocol.read_text(), "https\n")

    def test_dry_run_preserves_existing_and_fresh_home_state(self):
        before = self.snapshot()
        self.setup_host(dry_run=True, keys=True, login=True)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.protocol.read_text(), "https\n")
        self.setup_host()
        before = self.snapshot()
        self.setup_host(dry_run=True, installed=False)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.protocol.read_text(), "https\n")

    def test_github_protocol_requires_keys_and_successful_login(self):
        for keys, login in [(False, True), (True, False), (True, True)]:
            with self.subTest(keys=keys, login=login):
                self.protocol.write_text("https\n")
                self.log.write_text("")
                self.setup_host(keys=keys, login=login)
                self.assertEqual(self.protocol.read_text(), "ssh\n" if keys and login else "https\n")
                self.assertIn("agent:" + expanded_socket(SOCKETS["macos"]), self.log.read_text())
                if not keys:
                    self.assertNotIn("github:login", self.log.read_text())

    def test_github_identityagent_none_does_not_switch_protocol(self):
        self.ssh_config.write_text("Host github.com\n  IdentityAgent none\n")
        self.setup_host(keys=True, login=True)
        self.assertEqual(self.protocol.read_text(), "https\n")
        self.assertNotIn("github:login", self.log.read_text())
        self.assertNotIn("agent:", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
