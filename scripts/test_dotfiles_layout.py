"""Exercise migration safety and real application discovery in disposable homes."""

import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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

    def test_private_directory_merge_aborts_without_changing_either_tree(self):
        old = self.local_additions()
        old.chmod(0o700)
        self.custom.chmod(0o755)
        private = old / "readable-inside-private-directory"
        private.write_text("synthetic private fixture\n")
        private.chmod(0o644)
        for apply in (False, True):
            with self.subTest(apply=apply):
                with self.assertRaisesRegex(ValueError, "permissions"), \
                        patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
                    MIGRATION.migrate(self.home, apply)
                rename.assert_not_called()
                self.assertFalse(old.is_symlink())
                self.assertEqual(private.read_text(), "synthetic private fixture\n")
                self.assertFalse((self.custom / private.name).exists())
                self.assertEqual(old.stat().st_mode & 0o777, 0o700)
                self.assertEqual(self.custom.stat().st_mode & 0o777, 0o755)

    def test_nested_private_directory_is_checked_before_any_move(self):
        old = self.local_additions()
        (old / "plugins").chmod(0o700)
        (self.custom / "plugins").mkdir(mode=0o755)
        with self.assertRaisesRegex(ValueError, "permissions"), \
                patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
            MIGRATION.migrate(self.home, True)
        rename.assert_not_called()
        self.assertTrue((old / "bin/private-tool").is_file())
        self.assertTrue((old / "plugins/example/.git/config").is_file())
        self.assertFalse((self.custom / "bin/private-tool").exists())

    def test_destination_ancestry_cannot_escape_private_home(self):
        for component in (".config", ".config/zsh"):
            for apply in (False, True):
                with self.subTest(component=component, apply=apply):
                    case = f"{component.replace('/', '-')}-{apply}"
                    home = self.home / ("home-" + case)
                    home.mkdir(mode=0o700)
                    target = home / ".config/zsh/custom"
                    target.mkdir(parents=True)
                    old = home / ".zshrc_custom"
                    old.mkdir()
                    (old / "whole-directory").mkdir()
                    for path in (old / "private-file", old / "whole-directory/private-file"):
                        path.write_text("synthetic private fixture\n")
                        path.chmod(0o644)
                    outside = self.home / ("shared-" + case)
                    original = home / component
                    original.rename(outside)
                    original.symlink_to(outside, target_is_directory=True)
                    with self.assertRaisesRegex(ValueError, "home layout"), \
                            patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
                        MIGRATION.migrate(home, apply)
                    rename.assert_not_called()
                    self.assertFalse(old.is_symlink())
                    self.assertTrue((old / "private-file").is_file())
                    self.assertTrue((old / "whole-directory/private-file").is_file())
                    self.assertFalse((target / "private-file").exists())
                    self.assertFalse((target / "whole-directory").exists())

    def test_home_alias_and_internal_config_alias_preserve_relative_links(self):
        old = self.local_additions()
        external = self.home / "external-tool"
        external.write_text("synthetic local tool\n")
        (old / "bin/external").symlink_to("../../external-tool")
        storage = self.home / "nested/config-storage"
        storage.parent.mkdir()
        (self.home / ".config").rename(storage)
        (self.home / ".config").symlink_to("nested/config-storage", target_is_directory=True)
        alias = self.home / "home-alias"
        alias.symlink_to(self.home, target_is_directory=True)
        self.assertEqual(MIGRATION.migrate(alias), 5)
        self.assertEqual(MIGRATION.migrate(alias, True), 5)
        self.assertEqual((old / "bin/external").resolve(), external)
        self.assertEqual((old / "bin/private-tool").stat().st_mode & 0o777, 0o700)
        self.assertEqual(MIGRATION.migrate(alias, True), 0)

    def test_destination_cannot_overlap_source_tree(self):
        old = self.local_additions()
        shutil.rmtree(self.home / ".config")
        (old / "config/zsh/custom").mkdir(parents=True)
        (self.home / ".config").symlink_to(old / "config", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "overlap"), \
                patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
            MIGRATION.migrate(self.home, True)
        rename.assert_not_called()
        self.assertTrue((old / "bin/private-tool").is_file())

    def test_narrower_destination_and_whole_private_directory_rename_work(self):
        old = self.local_additions()
        old.chmod(0o755)
        (old / "plugins").chmod(0o700)
        self.custom.chmod(0o700)
        (self.custom / "bin").chmod(0o700)
        self.assertEqual(MIGRATION.migrate(self.home), 4)
        self.assertFalse(old.is_symlink())
        self.assertEqual(MIGRATION.migrate(self.home, True), 4)
        self.assertEqual(self.custom.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.custom / "bin").stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.custom / "plugins").stat().st_mode & 0o777, 0o700)
        self.assertEqual((old / "plugins/example/.git/config").read_text(), "plugin metadata\n")
        self.assertEqual(MIGRATION.migrate(self.home, True), 0)

    def test_owner_or_group_change_aborts_before_any_move(self):
        old = self.local_additions()
        original_stat = Path.stat
        for field in (4, 5):  # uid and gid in os.stat_result
            with self.subTest(field=field):
                def different_identity(path, *args, **kwargs):
                    result = original_stat(path, *args, **kwargs)
                    if path == self.custom:
                        fields = list(result)
                        fields[field] += 1
                        return os.stat_result(fields)
                    return result

                with patch.object(Path, "stat", different_identity), \
                        patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
                    with self.assertRaisesRegex(ValueError, "ownership"):
                        MIGRATION.migrate(self.home, True)
                rename.assert_not_called()
                self.assertTrue((old / "exports-local.zsh").is_file())

    @unittest.skipUnless(sys.platform == "darwin", "macOS ACL tools required")
    def test_macos_acl_on_either_directory_prevents_merge(self):
        old = self.local_additions()
        for directory in (old, self.custom):
            with self.subTest(directory=directory.name):
                self.run_command("/bin/chmod", "+a", "everyone allow read,search", str(directory))
                try:
                    with self.assertRaisesRegex(ValueError, "Directory ACLs"), \
                            patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
                        MIGRATION.migrate(self.home, True)
                    rename.assert_not_called()
                    self.assertTrue((old / "exports-local.zsh").is_file())
                finally:
                    self.run_command("/bin/chmod", "-N", str(directory))

    def test_acl_detection_and_inspection_failures(self):
        with patch.object(MIGRATION.sys, "platform", "linux"), \
                patch.object(MIGRATION.os, "listxattr", create=True, return_value=["user.fixture"]):
            self.assertFalse(MIGRATION.has_acl(self.custom))
        for attribute in ("system.posix_acl_access", "system.posix_acl_default"):
            with self.subTest(attribute=attribute), \
                    patch.object(MIGRATION.sys, "platform", "linux"), \
                    patch.object(MIGRATION.os, "listxattr", create=True, return_value=[attribute]):
                self.assertTrue(MIGRATION.has_acl(self.custom))
        with patch.object(MIGRATION.sys, "platform", "linux"), \
                patch.object(MIGRATION.os, "listxattr", create=True, side_effect=OSError("fixture failure")):
            with self.assertRaisesRegex(ValueError, "Cannot verify directory ACLs"):
                MIGRATION.has_acl(self.custom)
        with patch.object(MIGRATION.sys, "platform", "darwin"), \
                patch.object(MIGRATION.subprocess, "run", side_effect=OSError("fixture failure")):
            with self.assertRaisesRegex(ValueError, "Cannot verify directory ACLs"):
                MIGRATION.has_acl(self.custom)

    def test_unknown_acl_state_aborts_before_any_move(self):
        old = self.local_additions()
        with patch.object(MIGRATION, "has_acl", side_effect=ValueError("Cannot verify directory ACLs")), \
                patch.object(Path, "rename", autospec=True, side_effect=Path.rename) as rename:
            with self.assertRaisesRegex(ValueError, "Cannot verify directory ACLs"):
                MIGRATION.migrate(self.home, True)
        rename.assert_not_called()
        self.assertTrue((old / "exports-local.zsh").is_file())

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
        old.chmod(0o700)
        self.custom.chmod(0o700)
        (old / "bin").chmod(0o700)
        (self.custom / "bin").chmod(0o700)
        with patch.object(Path, "symlink_to", side_effect=OSError("fixture failure")):
            with self.assertRaises(OSError):
                MIGRATION.migrate(self.home, True)
        self.assertTrue((old / "bin/private-tool").exists())
        self.assertTrue((old / "exports-local.zsh").exists())
        self.assertFalse((self.custom / "exports-local.zsh").exists())
        self.assertFalse(old.is_symlink())
        self.assertEqual(old.stat().st_mode & 0o777, 0o700)
        self.assertEqual((old / "bin").stat().st_mode & 0o777, 0o700)

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

    def test_current_and_legacy_private_skills_are_ignored(self):
        shutil.copy2(ROOT / ".gitignore", self.home / ".gitignore")
        self.run_command("git", "init")
        private_paths = (".agents/private-skills/fixture/nested/SKILL.md",
                         ".agents/skills/private/fixture/nested/SKILL.md")
        public_path = ".agents/skills/development/fixture/SKILL.md"
        for path in (*private_paths, public_path):
            file = self.home / path
            file.parent.mkdir(parents=True)
            file.write_text("synthetic skill fixture\n")
        for path in private_paths:
            with self.subTest(path=path):
                self.run_command("git", "check-ignore", "--", path)
        self.run_command("git", "add", "--all", "--", ".agents")
        self.assertEqual(self.run_command("git", "ls-files").splitlines(), [public_path])

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

    def test_setup_uses_active_plugin_directory_without_duplicate_checkout(self):
        self.local_additions()
        script = self.home / "setup-under-test.sh"
        # Load the real setup functions while replacing installers with local stubs.
        script.write_text((ROOT / "setup.sh").read_text().replace('main "$@"', ""))
        command = ('source "$HOME/setup-under-test.sh"; '
                   'install_oh_my_zsh() { :; }; install_starship() { :; }; '
                   'install_zsh_syntax_highlighting() { printf "%s\\n" "$1"; }; '
                   'setup_shell Darwin')
        for migrated in (False, True):
            if migrated:
                MIGRATION.migrate(self.home, True)
            expected = self.custom if migrated else self.home / ".zshrc_custom"
            self.assertEqual(self.run_command("bash", "-c", command).strip(),
                             str(expected / "plugins/zsh-syntax-highlighting"))
        self.env["ZSH_CUSTOM"] = str(self.home / "explicit-custom")
        self.assertEqual(self.run_command("bash", "-c", command).strip(),
                         str(self.home / "explicit-custom/plugins/zsh-syntax-highlighting"))

    @unittest.skipUnless(shutil.which("zsh"), "zsh required")
    def test_auth_diagnostic_sees_active_local_exports_without_provider_access(self):
        self.local_additions()
        local_bin = self.home / ".local/bin"
        local_bin.mkdir(parents=True)
        for name in ("op", "codex", "ssh", "ssh-add", "gh", "git"):
            stub = local_bin / name
            stub.write_text("#!/bin/sh\nexit 1\n")
            stub.chmod(0o700)
        self.env["AGENT_HOST_ALIAS"] = "fixture"
        for migrated in (False, True):
            if migrated:
                MIGRATION.migrate(self.home, True)
            output = self.run_command("zsh", str(self.custom / "bin/onepassword-dev-preflight"))
            row = next(line for line in output.splitlines() if line.startswith("exports-local.zsh"))
            self.assertEqual(row.split(), ["exports-local.zsh", "present"])

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
