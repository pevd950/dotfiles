"""Synthetic regression cases for PR review input and output boundaries."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
import test_scan_codex_sessions as fixtures
from test_scan_codex_sessions import SCRIPT, scanner, meta, item, user


class BoundaryTests(unittest.TestCase):
    setUp = fixtures.ScannerTests.setUp
    write = fixtures.ScannerTests.write
    collect = fixtures.ScannerTests.collect
    events = fixtures.ScannerTests.events
    def test_nonobject_detail_references_and_records(self):
        for value in (None, [], 3, "text"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                scanner.detail([self.active], value)
            raw = json.dumps(value).encode() + b"\n"
            path = self.active / "nonobject.jsonl"
            path.write_bytes(raw)
            ref = {"root_index": 0, "relative_path": path.name, "byte_offset": 0,
                   "byte_length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            with self.assertRaises(ValueError):
                scanner.detail([self.active], ref)

    def test_arbitrary_json_tool_output_preserved_privately(self):
        self.write([meta(), item("function_call_output", call_id="one",
                    output='{"error":"permission denied", "token":"synthetic secret"}')])
        event = self.events(self.collect())[0]
        self.assertIn("denial_candidate", event["signals"])
        self.assertNotIn("synthetic secret", json.dumps(event))
        excerpt = scanner.detail([self.active], event["source_ref"])
        self.assertIn("permission denied", excerpt["text"])
        self.assertNotIn("synthetic secret", excerpt["text"])

    def test_mcp_source_is_primary(self):
        self.write([meta(source="mcp"), user("hello")])
        result = self.collect()
        self.assertEqual(result["sessions"][0]["source_class"], "primary")
        self.assertFalse(result["source_gaps"])

    def test_cli_detail_reference_rejects_fifo_symlink_and_nonobject(self):
        root = self.root.resolve()
        reference = root / "reference.json"
        reference.write_text("null")
        fifo = root / "fifo"
        os.mkfifo(fifo)
        link = root / "link"
        link.symlink_to(reference)
        for path in (reference, fifo, link):
            result = subprocess.run([sys.executable, str(SCRIPT), "--authorized",
                "--source-root", str(self.active), "--source-host", "fixture",
                "--detail-ref", str(path), "--output", str(root / "private" / "detail.json")],
                capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(result.stdout, "")

    def test_cli_scan_requires_nonempty_current_session(self):
        for extra in ([], ["--exclude-session", ""]):
            result = subprocess.run([sys.executable, str(SCRIPT), "--authorized",
                "--source-root", str(self.active), "--source-host", "fixture",
                "--output", str(self.root / "private" / "index.json"), *extra],
                capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--exclude-session", result.stderr)


if __name__ == "__main__":
    unittest.main()
