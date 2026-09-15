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

    def test_recent_activity_has_priority_across_canonical_roots(self):
        old = self.write([meta("old"), user("old", fixtures.OLD)] * 30,
                         name="2026-01-old.jsonl")
        resumed = self.write([meta("resumed"), user("recent")],
                             name="2025-01-resumed.jsonl", directory=self.archive)
        os.utime(old, (100, 100))
        os.utime(resumed, (200, 200))
        result = self.collect(max_bytes=resumed.stat().st_size + 1)
        self.assertEqual([s["id"] for s in result["sessions"]], ["resumed"])
        self.assertIn("max_bytes", result["truncation"])
        self.assertFalse(result["complete_within_supported_scope"])
        self.assertEqual(scanner.detail([self.active, self.archive],
                         self.events(result)[0]["source_ref"])["text"], "recent")

    def test_stale_modification_time_never_excludes_in_window_activity(self):
        stale = self.write([meta("stale-copy"), user("current")])
        os.utime(stale, (1, 1))
        self.write([meta("newer"), user("old", fixtures.OLD)], "newer.jsonl")
        result = self.collect()
        self.assertEqual([s["id"] for s in result["sessions"]], ["stale-copy"])
        self.assertTrue(result["complete_within_supported_scope"])

    def test_identity_change_stops_file_and_reports_partial_coverage(self):
        self.write([meta("first"), user("first"), meta("second"), user("second")])
        result = self.collect()
        self.assertEqual([s["id"] for s in result["sessions"]], ["first"])
        self.assertIn("session_identity_changed", [g["reason"] for g in result["source_gaps"]])
        self.assertFalse(result["complete_within_supported_scope"])

    def test_fork_header_does_not_reattribute_inherited_parent_history(self):
        parent = meta("parent")
        inherited = user("inherited")
        fork = meta("child", {"subagent": {"spawn": {"parent_thread_id": "parent"}}})
        fork["payload"].update(forked_from_id="parent", parent_thread_id="parent",
                               subagent_history_start_ordinal=46)
        self.write([parent, inherited], "parent.jsonl")
        self.write([fork, parent, inherited, user("child activity")], "child.jsonl")
        result = self.collect()
        self.assertEqual([s["id"] for s in result["sessions"]], ["parent"])
        self.assertEqual(len(self.events(result)), 1)
        self.assertIn("session_identity_changed", [g["reason"] for g in result["source_gaps"]])
        self.assertFalse(result["complete_within_supported_scope"])

    def test_no_correction_boundaries(self):
        for text in ("No", "no", "NO", "No?", "No:", "No;", "No,", "No.", "No!", "No thanks"):
            with self.subTest(text=text):
                self.assertIn("correction_candidate", scanner._event(user(text))[0]["signals"])
        for text in ("Nobody", "Nothing", "Nope", "Normal", "Noted"):
            with self.subTest(text=text):
                self.assertNotIn("correction_candidate", scanner._event(user(text))[0]["signals"])

    def test_complete_final_record_without_newline_is_collected_and_readable(self):
        for directory in (self.active, self.archive):
            with self.subTest(directory=directory.name):
                path = self.write([meta(directory.name)], directory=directory,
                                  tail=json.dumps(user(directory.name)).encode())
                result = self.collect()
                session = next(s for s in result["sessions"] if s["id"] == directory.name)
                self.assertEqual(len(session["events"]), 1)
                self.assertEqual(result["coverage"]["incomplete_trailing_records"], 0)
                self.assertFalse(result["source_gaps"])
                ref = session["events"][0]["source_ref"]
                self.assertEqual(scanner.detail([self.active, self.archive], ref)["text"], directory.name)
                with path.open("ab") as handle:
                    handle.write(b"\n")
                with self.assertRaises(ValueError):
                    scanner.detail([self.active, self.archive], ref)

    def test_eof_record_is_not_assumed_complete_at_byte_cap(self):
        path = self.write([meta()], tail=json.dumps(user("last")).encode())
        result = self.collect(max_bytes=path.stat().st_size - 1)
        self.assertEqual(self.events(result), [])
        self.assertIn("max_bytes", result["truncation"])
        self.assertLessEqual(result["coverage"]["bytes_read"], path.stat().st_size - 1)

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
