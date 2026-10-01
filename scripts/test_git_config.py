"""Exercise Git's real include loading and yadm's class/OS selection."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("yadm"), "yadm is required for alternate checks")
class GitConfigTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-git-config-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.config = self.home / ".config/git"
        self.config.mkdir(parents=True)
        shutil.copy2(ROOT / ".gitconfig", self.home / ".gitconfig")
        for source in (ROOT / ".config/git").iterdir():
            if source.name == "settings.conf" or "##" in source.name:
                shutil.copy2(source, self.config / source.name)
        self.env = {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_DATA_HOME": str(self.home / ".local/share"),
            "PATH": os.environ["PATH"],
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
        self.run_command("yadm", "init")
        paths = [".gitconfig"] + [
            str(path.relative_to(self.home))
            for path in self.config.iterdir()
        ]
        self.run_command("yadm", "add", "--", *paths)

    def run_command(self, *args):
        return subprocess.run(
            args, cwd=self.home, env=self.env, check=True,
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()

    def select(self, machine_class, system):
        self.run_command("yadm", "config", "local.class", machine_class)
        self.run_command("yadm", "config", "local.os", system)
        self.run_command("yadm", "alt", "--force")

    def value(self, key):
        return self.run_command("git", "config", "--get", key)

    def test_class_and_os_alternates_load_through_root_entry_point(self):
        for machine_class in ("personal", "work"):
            for system in ("Darwin", "Linux"):
                with self.subTest(machine_class=machine_class, system=system):
                    self.select(machine_class, system)
                    for name, suffix in (
                        ("local", "class." + machine_class),
                        ("platform", "os." + system),
                    ):
                        link = self.config / (name + ".conf")
                        self.assertTrue(link.is_symlink())
                        self.assertEqual(
                            link.resolve(), self.config / (name + ".conf##" + suffix)
                        )
                    for key in ("user.name", "user.email"):
                        expected = self.run_command(
                            "git", "config", "--file", str(self.config / "local.conf"),
                            "--get", key,
                        )
                        self.assertEqual(self.value(key), expected)
                    self.assertEqual(self.value("alias.st"), "status")
                    self.assertEqual(self.value("pull.rebase"), "true")

    def test_auth_compatibility_and_include_precedence(self):
        self.select("personal", "Darwin")
        (self.home / ".gitconfig.auth").write_text(
            "[fixture]\nlegacy = present\norder = legacy\n"
            "[credential \"https://example.invalid\"]\nhelper = fixture-helper\n"
            "[push]\ndefault = matching\n"
        )
        self.assertEqual(self.value("fixture.legacy"), "present")
        self.assertEqual(
            self.value("credential.https://example.invalid.helper"), "fixture-helper"
        )
        (self.config / "auth.conf").write_text("[fixture]\norder = grouped\n")
        self.assertEqual(self.value("fixture.order"), "grouped")
        self.assertEqual(self.value("push.default"), "simple")

    def test_existing_xdg_config_is_preserved_without_duplicate_shared_values(self):
        self.select("personal", "Linux")
        (self.config / "config").write_text("[fixture]\nxdg = present\n")
        self.assertEqual(self.value("fixture.xdg"), "present")
        self.assertEqual(
            self.run_command("git", "config", "--get-all", "alias.st"),
            "status",
        )
        # The portable entry point does not depend on XDG_CONFIG_HOME matching .config.
        self.env["XDG_CONFIG_HOME"] = str(self.home / "custom-xdg")
        self.assertEqual(self.value("alias.st"), "status")
        self.assertEqual(self.value("pull.rebase"), "true")


if __name__ == "__main__":
    unittest.main()
