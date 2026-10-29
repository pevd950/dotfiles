"""Check video artifact isolation using synthetic files and local subprocesses."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = (Path(__file__).resolve().parent.parent /
          ".agents/skills/productivity/video-analysis/scripts/video_analyze.py")
SPEC = importlib.util.spec_from_file_location("video_privacy_subject", SCRIPT)
VIDEO = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VIDEO
SPEC.loader.exec_module(VIDEO)
METADATA = {"duration_seconds": 1.0, "audio": {"present": True}}


class VideoPrivacyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="video-privacy-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "synthetic.mp4"
        self.source.write_bytes(b"synthetic fixture, not a real recording")

    def invoke(self, destination=None, *, source=None, fail=False):
        args = [str(SCRIPT), str(source or self.source), "--mode", "frame-only"]
        if destination is not None:
            args += ["--out-dir", str(destination)]

        def write_artifact(command, **kwargs):
            if command[0] == "yt-dlp":
                output = command[command.index("-o") + 1]
                output = output.replace("%(title).200B", "fixture").replace("%(id)s", "1").replace("%(ext)s", "mp4")
            else:
                output = command[-1].replace("%05d", "00001")
            self.assertEqual(stat.S_IMODE(Path(output).parent.parent.stat().st_mode), 0o700)
            # A real child proves that the privacy policy is inherited by tools.
            subprocess.run([sys.executable, "-c",
                            "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'synthetic')",
                            output], check=True, timeout=10)
            if fail:
                raise RuntimeError("synthetic processing failure")

        output = io.StringIO()
        with patch.object(sys, "argv", args), patch.object(VIDEO, "probe", return_value=METADATA), \
                patch.object(VIDEO, "require_binary"), patch.object(VIDEO, "run", side_effect=write_artifact), \
                patch.object(VIDEO.tempfile, "gettempdir", return_value=str(self.root)), redirect_stdout(output):
            self.assertEqual(VIDEO.main(), 0)
        return Path(output.getvalue().strip())

    def assert_private(self, output):
        for path in [output, *output.rglob("*")]:
            expected = 0o700 if path.is_dir() else 0o600
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), expected, str(path))

    def test_all_writers_are_private_under_permissive_umask_and_success_persists(self):
        old_mask = os.umask(0)
        try:
            output = self.invoke(self.root / "results", source="https://example.invalid/fixture")
            current_mask = os.umask(0)
            self.assertEqual(current_mask, 0)
            self.assert_private(output)
            for artifact in ["download/fixture-1.mp4", "audio/audio.m4a", "analysis.md", "timeline.json",
                             "contact_sheets/sheet_001.jpg"]:
                self.assertTrue((output / artifact).is_file(), artifact)
            self.assertEqual(len(list((output / "frames").glob("frame_*.jpg"))), 1)
        finally:
            os.umask(old_mask)

    def test_existing_leaf_destinations_are_rejected_before_any_writers(self):
        sentinel = self.root / "sentinel"
        sentinel.write_text("untouched")
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "timeline.json").write_text("untouched")
        linked = self.root / "linked"
        linked.symlink_to(existing, target_is_directory=True)
        dangling = self.root / "dangling"
        dangling.symlink_to(self.root / "absent")
        for destination in [existing, sentinel, linked, dangling]:
            with self.subTest(destination=destination.name), patch.object(VIDEO, "resolve_source") as resolve:
                with self.assertRaises(SystemExit):
                    self.invoke(destination)
                resolve.assert_not_called()
        self.assertEqual(sentinel.read_text(), "untouched")
        self.assertEqual((existing / "timeline.json").read_text(), "untouched")
        self.assertTrue(linked.is_symlink())
        self.assertTrue(dangling.is_symlink())

    def test_symlink_parent_is_rejected_including_dotdot(self):
        target = self.root / "target"
        target.mkdir()
        linked = self.root / "linked"
        linked.symlink_to(target, target_is_directory=True)
        for destination in [linked / "results", linked / ".." / "results"]:
            with self.subTest(destination=str(destination)), self.assertRaises(SystemExit):
                self.invoke(destination)
        self.assertEqual(list(target.iterdir()), [])
        self.assertFalse((self.root / "results").exists())

    def test_unsafe_or_missing_parent_is_rejected(self):
        writable = self.root / "shared"
        writable.mkdir(mode=0o700)
        writable.chmod(0o777)
        for destination in [writable / "results", self.root / "missing" / "results"]:
            with self.subTest(destination=str(destination)), self.assertRaises(SystemExit):
                self.invoke(destination)
            self.assertFalse(destination.exists())

    def test_trusted_sticky_parent_allows_private_output(self):
        shared = self.root / "sticky"
        shared.mkdir(mode=0o700)
        shared.chmod(0o1777)
        self.assert_private(self.invoke(shared / "results"))

    def test_foreign_owned_parent_is_rejected_even_with_sticky_bit(self):
        foreign = self.root / "foreign"
        foreign.mkdir(mode=0o700)
        foreign.chmod(0o1777)
        real_lstat = Path.lstat

        def different_owner(path):
            info = real_lstat(path)
            if path == foreign:
                values = list(info)
                values[4] = os.geteuid() + 1
                return os.stat_result(values)
            return info

        with patch.object(Path, "lstat", autospec=True, side_effect=different_owner):
            with self.assertRaisesRegex(SystemExit, "owned by you or root"):
                self.invoke(foreign / "results")
        self.assertEqual(list(foreign.iterdir()), [])

    @unittest.skipUnless(sys.platform == "darwin", "macOS ACL tools required")
    def test_macos_inherited_acl_is_rejected_before_writers(self):
        parent = self.root / "acl-parent"
        parent.mkdir(mode=0o755)
        subprocess.run(["/bin/chmod", "+a", "everyone allow read,search,file_inherit,directory_inherit",
                        str(parent)], check=True, timeout=10)
        try:
            with patch.object(VIDEO, "resolve_source") as resolve:
                with self.assertRaisesRegex(SystemExit, "ACL"):
                    self.invoke(parent / "results")
                resolve.assert_not_called()
            self.assertFalse((parent / "results").exists())
        finally:
            subprocess.run(["/bin/chmod", "-RN", str(parent)], check=True, timeout=10)

    def test_linux_acl_detector_contract(self):
        with patch.object(VIDEO.sys, "platform", "linux"), \
                patch.object(VIDEO.os, "listxattr", return_value=["user.fixture"], create=True):
            VIDEO.validate_output_acl(self.root)
        for attribute in ["system.posix_acl_access", "system.posix_acl_default"]:
            with self.subTest(attribute=attribute), patch.object(VIDEO.sys, "platform", "linux"), \
                    patch.object(VIDEO.os, "listxattr", return_value=[attribute], create=True):
                with self.assertRaisesRegex(SystemExit, "has ACLs"):
                    VIDEO.validate_output_acl(self.root)

    def test_unknown_acl_state_fails_before_writers(self):
        cases = [
            ("linux", patch.object(VIDEO.os, "listxattr", side_effect=OSError("inspection failed"), create=True)),
            ("darwin", patch.object(VIDEO.subprocess, "run", side_effect=OSError("inspection failed"))),
            ("darwin", patch.object(VIDEO.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b""))),
            ("unsupported", patch.object(VIDEO.os, "listxattr", create=True)),
        ]
        for platform, inspection in cases:
            with self.subTest(platform=platform), patch.object(VIDEO.sys, "platform", platform), inspection, \
                    patch.object(VIDEO, "resolve_source") as resolve:
                with self.assertRaisesRegex(SystemExit, "Cannot verify output directory ACLs"):
                    self.invoke(self.root / "results")
                resolve.assert_not_called()
            self.assertFalse((self.root / "results").exists())

    def test_acl_on_new_root_is_rejected_and_cleaned_before_writers(self):
        output = self.root / "results"
        validate = VIDEO.validate_output_acl

        def root_acl(path):
            if path == output:
                raise SystemExit("Output directory has ACLs")
            validate(path)

        with patch.object(VIDEO, "validate_output_acl", side_effect=root_acl), \
                patch.object(VIDEO, "resolve_source") as resolve:
            with self.assertRaisesRegex(SystemExit, "has ACLs"):
                self.invoke(output)
            resolve.assert_not_called()
        self.assertFalse(output.exists())

    def test_partial_output_is_removed_on_failure_and_umask_restored(self):
        output = self.root / "results"
        sentinel = self.root / "sentinel"
        sentinel.write_text("untouched")
        old_mask = os.umask(0o022)
        try:
            with self.assertRaisesRegex(RuntimeError, "synthetic processing failure"):
                self.invoke(output, source="https://example.invalid/fixture", fail=True)
            self.assertEqual(os.umask(0o022), 0o022)
        finally:
            os.umask(old_mask)
        self.assertFalse(output.exists())
        self.assertEqual(sentinel.read_text(), "untouched")

    def test_invalid_analysis_removes_only_the_new_output(self):
        with patch.object(VIDEO, "parse_time", side_effect=SystemExit("invalid range")):
            with self.assertRaisesRegex(SystemExit, "invalid range"):
                self.invoke(self.root / "results")
        self.assertFalse((self.root / "results").exists())
        self.assertTrue(self.source.exists())

    def test_default_partial_output_is_removed(self):
        before = set(self.root.iterdir())
        with self.assertRaisesRegex(RuntimeError, "synthetic processing failure"):
            self.invoke(fail=True)
        self.assertEqual(set(self.root.iterdir()), before)

    def test_failure_cleanup_does_not_remove_a_replacement_directory(self):
        output = self.root / "results"
        moved = self.root / "moved"
        with self.assertRaisesRegex(RuntimeError, "failure after replacement"):
            with VIDEO.private_output_directory(str(output)):
                output.rename(moved)
                output.mkdir(mode=0o700)
                (output / "sentinel").write_text("untouched")
                raise RuntimeError("failure after replacement")
        self.assertEqual((output / "sentinel").read_text(), "untouched")
        self.assertTrue(moved.is_dir())

    def test_concurrent_defaults_are_unique_and_private(self):
        runner = (
            "import runpy, sys; "
            f"scope = runpy.run_path({str(SCRIPT)!r}); "
            "main = scope['main']; "
            f"main.__globals__['probe'] = lambda path: {METADATA!r}; "
            "main.__globals__['time'].strftime = lambda fmt: 'same-second'; "
            f"sys.argv = [{str(SCRIPT)!r}, {str(self.source)!r}, '--mode', 'gemini-only', "
            "'--no-gemini', '--no-audio-extract']; "
            "main()"
        )
        env = {"PATH": os.environ.get("PATH", ""), "TMPDIR": str(self.root)}

        def analyze(_):
            result = subprocess.run([sys.executable, "-c", runner], env=env,
                                    text=True, capture_output=True, timeout=20, check=True)
            return Path(result.stdout.strip())

        with ThreadPoolExecutor(max_workers=6) as executor:
            outputs = list(executor.map(analyze, range(6)))
        self.assertEqual(len(set(outputs)), 6)
        for output in outputs:
            self.assert_private(output)
            self.assertTrue((output / "timeline.json").is_file())

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "requires ffmpeg and ffprobe")
    def test_real_synthetic_frame_only_cli(self):
        source = self.root / "color.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=64x64:r=2",
                        "-t", "1", "-an", str(source)], check=True, timeout=20, capture_output=True)
        result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--mode", "frame-only",
                                 "--no-audio-extract", "--resolution", "64", "--fps", "2",
                                 "--out-dir", str(self.root / "real-output")],
                                check=True, text=True, capture_output=True, timeout=30)
        output = Path(result.stdout.strip())
        timeline = json.loads((output / "timeline.json").read_text())
        self.assertGreater(timeline["frames"]["count"], 0)
        self.assertTrue(timeline["contact_sheets"])
        self.assert_private(output)


if __name__ == "__main__":
    unittest.main()
