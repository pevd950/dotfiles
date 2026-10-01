"""Exercise migration safety and real application discovery in disposable homes."""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("layout_migration", ROOT / "scripts/migrate-zsh-layout.py")
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dotfiles-layout-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.custom = self.home / ".config/zsh/custom"
        shutil.copytree(ROOT / ".config/zsh", self.home / ".config/zsh")
        for name in (".zshenv", ".zshrc"):
            shutil.copy2(ROOT / name, self.home / name)
        self.env = {
            "HOME": str(self.home), "PATH": os.environ["PATH"],
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_DATA_HOME": str(self.home / ".local/share"),
            "TERM": "dumb", "GIT_CONFIG_NOSYSTEM": "1",
        }

    def run_command(self, *args):
        return subprocess.run(args, cwd=self.home, env=self.env, check=True,
                              capture_output=True, text=True, timeout=30).stdout

    def local_additions(self):
        old = self.home / ".zshrc_custom"
        (old / "bin").mkdir(parents=True)
        (old / "plugins/example/.git").mkdir(parents=True)
        (old / "plugins/example/.git/config").write_text("plugin metadata\n")
        (old / "exports-local.zsh").write_text("export LAYOUT_FIXTURE=local\n")
        (old / "exports-local.zsh").chmod(0o600)
        (old / "bin/private-tool").write_text("#!/bin/sh\nexit 0\n")
        (old / "bin/private-tool").chmod(0o700)
        (old / "completions").symlink_to("plugins/example")
        return old

    def test_migration_preserves_local_additions_and_legacy_access(self):
        old = self.local_additions()
        self.assertEqual(MIGRATION.migrate(self.home), 4)
        self.assertFalse(old.is_symlink())
        self.assertFalse((self.custom / "exports-local.zsh").exists())
        self.assertEqual(MIGRATION.migrate(self.home, True), 4)
        self.assertTrue(old.is_symlink())
        self.assertEqual((old / "exports-local.zsh").read_text(), "export LAYOUT_FIXTURE=local\n")
        self.assertEqual((self.custom / "exports-local.zsh").stat().st_mode & 0o777, 0o600)
        self.assertEqual((self.custom / "bin/private-tool").stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.custom / "completions").readlink(), Path("plugins/example"))
        self.assertEqual((old / "plugins/example/.git/config").read_text(), "plugin metadata\n")
        self.assertEqual(MIGRATION.migrate(self.home, True), 0)

    def test_collision_aborts_before_any_moves(self):
        old = self.local_additions()
        (self.custom / "exports-local.zsh").write_text("different private override\n")
        with self.assertRaises(ValueError):
            MIGRATION.migrate(self.home, True)
        self.assertFalse(old.is_symlink())
        self.assertTrue((old / "bin/private-tool").is_file())
        self.assertFalse((self.custom / "bin/private-tool").exists())
        self.assertEqual((self.custom / "exports-local.zsh").read_text(), "different private override\n")

    def test_relative_links_keep_external_and_internal_targets(self):
        old = self.local_additions()
        external = self.home / "external-tool"
        external.write_text("outside custom directory\n")
        (old / "bin/external").symlink_to("../../external-tool")
        (old / "bin/internal").symlink_to("../plugins/example/.git/config")
        MIGRATION.migrate(self.home, True)
        self.assertEqual((self.custom / "bin/external").resolve(), external)
        self.assertEqual((old / "bin/external").resolve(), external)
        self.assertEqual((self.custom / "bin/internal").readlink(), Path("../plugins/example/.git/config"))

    def test_failed_link_creation_rolls_back_moves_and_directories(self):
        old = self.local_additions()
        with patch.object(Path, "symlink_to", side_effect=OSError("fixture failure")):
            with self.assertRaises(OSError):
                MIGRATION.migrate(self.home, True)
        self.assertTrue((old / "bin/private-tool").exists())
        self.assertTrue((old / "exports-local.zsh").exists())
        self.assertFalse((self.custom / "exports-local.zsh").exists())
        self.assertFalse(old.is_symlink())

    def test_fresh_home_and_unexpected_legacy_link(self):
        self.assertEqual(MIGRATION.migrate(self.home, True), 0)
        old = self.home / ".zshrc_custom"
        old.unlink()
        old.symlink_to("somewhere-else")
        with self.assertRaises(ValueError):
            MIGRATION.migrate(self.home, True)
        self.assertEqual(old.readlink(), Path("somewhere-else"))

    def test_recovery_failure_keeps_original_error_and_restores_other_paths(self):
        old = self.local_additions()
        rename = Path.rename

        def fail_one_restore(path, target):
            if target == old / "bin/private-tool":
                raise OSError("fixture recovery failure")
            return rename(path, target)

        errors = io.StringIO()
        with patch.object(Path, "symlink_to", side_effect=OSError("original fixture failure")), \
                patch.object(Path, "rename", fail_one_restore), patch("sys.stderr", errors):
            with self.assertRaisesRegex(OSError, "original fixture failure"):
                MIGRATION.migrate(self.home, True)
        self.assertTrue((old / "exports-local.zsh").exists())
        self.assertTrue((old / "plugins/example/.git/config").exists())
        self.assertTrue((self.custom / "bin/private-tool").exists())
        self.assertIn(str(old / "bin/private-tool"), errors.getvalue())

    def test_compatibility_link_and_private_additions_are_ignored(self):
        shutil.copy2(ROOT / ".gitignore", self.home / ".gitignore")
        self.run_command("git", "init")
        MIGRATION.migrate(self.home, True)
        for path in (".zshrc_custom", ".config/zsh/custom/exports-local.zsh",
                     ".config/zsh/custom/bin/private-tool", ".config/zsh/custom/plugins/example"):
            with self.subTest(path=path):
                self.run_command("git", "check-ignore", "--", path)

    @unittest.skipUnless(shutil.which("zsh"), "zsh required")
    def test_shell_startup_before_and_after_migration(self):
        self.local_additions()
        (self.home / ".zshenv.local").write_text("export LAYOUT_ENV_FIXTURE=quiet\n")
        omz = self.home / ".oh-my-zsh"
        omz.mkdir()
        (omz / "oh-my-zsh.sh").write_text('for file in "$ZSH_CUSTOM"/*.zsh(N); do source "$file"; done\n')
        local_bin = self.home / ".local/bin"
        local_bin.mkdir(parents=True)
        code = local_bin / "code"
        code.write_text('#!/bin/sh\nfor file; do test -f "$file" || exit 8; done\n')
        code.chmod(0o700)
        for migrated in (False, True):
            if migrated:
                MIGRATION.migrate(self.home, True)
            for mode in ("-c", "-lc", "-ic", "-lic"):
                with self.subTest(migrated=migrated, mode=mode):
                    result = self.run_command("zsh", mode,
                        '[[ "$LAYOUT_ENV_FIXTURE" = quiet ]] || exit 2; '
                        '[[ "$CODEX_HOME" = "$HOME/.codex" ]] || exit 3; '
                        'whence coderabbit >/dev/null || exit 4; '
                        'if [[ -o interactive ]]; then '
                        '[[ "$LAYOUT_FIXTURE" = local && "$EDITOR" = vim ]] || exit 5; '
                        'whence has_docker_compose_cli_plugin >/dev/null || exit 6; '
                        'whence myip >/dev/null || exit 7; '
                        'eval myaliases || exit 8; eval myfunctions || exit 9; '
                        'eval zshrc || exit 10; fi; print layout-ok')
                    self.assertEqual(result.strip(), "layout-ok")

    @unittest.skipUnless(shutil.which("yadm"), "yadm required")
    def test_yadm_generates_root_entry_points_from_alt_folder(self):
        alt = self.home / ".config/yadm/alt"
        shutil.copytree(ROOT / ".config/yadm/alt", alt)
        self.run_command("yadm", "init")
        self.run_command("yadm", "config", "local.os", "Darwin")
        self.run_command("yadm", "add", "--", ".config/yadm/alt")
        self.run_command("yadm", "alt")
        self.assertTrue((self.home / ".Brewfile").is_file())
        self.assertEqual((self.home / ".zprofile").resolve(), alt / ".zprofile##os.Darwin")

    @unittest.skipUnless(shutil.which("vim"), "vim required")
    def test_vim_discovers_native_directory(self):
        shutil.copytree(ROOT / ".vim", self.home / ".vim")
        output = self.home / "vim-result"
        self.run_command("vim", "-n", "-i", "NONE", "-c",
            f"call writefile([expand('$MYVIMRC'), string(&number), string(&incsearch), string(&scrolloff)], '{output}')",
            "-c", "qa!")
        self.assertEqual(output.read_text().splitlines(), [str(self.home / ".vim/vimrc"), "1", "1", "10"])

    def test_workspace_resolves_checkout_or_home_root(self):
        path = ROOT / ".config/vscode/dotfiles.code-workspace"
        workspace = json.loads(path.read_text())
        self.assertEqual((path.parent / workspace["folders"][0]["path"]).resolve(), ROOT)


if __name__ == "__main__":
    unittest.main()
