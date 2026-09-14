"""Synthetic-only fixtures shaped like actual Codex JSONL envelopes."""
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("scan_codex_sessions.py")
spec = importlib.util.spec_from_file_location("scanner", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)
OLD = "2026-08-01T00:00:00Z"
BEFORE = "2026-09-10T23:59:00Z"
NOW = "2026-09-12T00:00:00Z"
AFTER = "2026-09-14T00:00:00Z"
LOWER = scanner._time("2026-09-11T00:00:00Z")
UPPER = scanner._time("2026-09-13T00:00:00Z")


def meta(sid="session-one", source="cli"):
    return {"timestamp": OLD, "type": "session_meta", "payload": {"id": sid, "source": source}}


def item(kind, timestamp=NOW, **fields):
    return {"timestamp": timestamp, "type": "response_item", "payload": {"type": kind, **fields}}


def user(text, timestamp=NOW):
    return item("message", timestamp, role="user", content=[{"type": "input_text", "text": text}])


class ScannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.active = self.root / "sessions"
        self.archive = self.root / "archived_sessions"
        self.active.mkdir(); self.archive.mkdir()

    def write(self, records, name="old-created.jsonl", directory=None, tail=b""):
        path = (directory or self.active) / name
        path.write_bytes(b"".join(json.dumps(record).encode() + b"\n" for record in records) + tail)
        return path

    def collect(self, **kwargs):
        return scanner.collect([self.active, self.archive], LOWER, UPPER, **kwargs)

    def events(self, result):
        return [event for session in result["sessions"] for event in session["events"]]

    def test_real_classic_and_custom_calls_pair_with_prior_window_call(self):
        self.write([meta(), item("function_call", BEFORE, name="exec_command", call_id="one", arguments="{}"),
                    item("function_call_output", call_id="one", output="Process exited with code 1"),
                    item("custom_tool_call", name="record_and_replay", call_id="two", input="private"),
                    item("custom_tool_call_output", call_id="two", output="exit code 0")])
        events = self.events(self.collect())
        self.assertEqual([event["kind"] for event in events], ["tool_result", "tool_call", "tool_result"])
        self.assertEqual(events[0]["call"]["name"], "exec_command")
        self.assertTrue(events[0]["call"]["before_window"])
        self.assertEqual(events[0]["status"]["exit_code"], 1)
        self.assertEqual(events[1]["name"], "record_and_replay")
        self.assertEqual(events[1]["correlation_id"], events[2]["correlation_id"])
        self.assertEqual(events[2]["status"]["exit_code"], 0)

    def test_old_creation_recent_activity_and_upper_boundary(self):
        self.write([meta(), user("old", BEFORE), user("recent"), user("future", AFTER)])
        result = self.collect()
        self.assertEqual(len(self.events(result)), 1)
        self.assertEqual(result["coverage"]["out_of_window_events"], 2)

    def test_archived_without_recent_activity_is_explicitly_not_archive_event(self):
        self.write([meta(), user("old", BEFORE)], directory=self.archive)
        result = self.collect()
        self.assertEqual(self.events(result), [])
        self.assertIn("archive metadata database not integrated", " ".join(result["limitations"]))

    def test_payload_id_exclusion_and_structural_sidecar_variants(self):
        self.write([meta("current"), user("exclude")])
        self.write([meta("side-one", {"subagent": {"guardian": {"parent_thread_id": "parent"}}}), user("exclude")], "one.jsonl")
        self.write([meta("side-two", "approval"), user("exclude")], "two.jsonl")
        self.write([meta("ordinary", {"subagent": {"spawn": {"parent_thread_id": "parent"}}}), user("include")], "guardian-is-only-filename.jsonl")
        result = self.collect(exclude={"current"})
        self.assertEqual([s["id"] for s in result["sessions"]], ["ordinary"])
        self.assertEqual(result["sessions"][0]["source_class"], "subagent")
        self.assertEqual(result["coverage"]["excluded_sidecar_files"], 2)

    def test_archive_copy_resume_deduplication_and_later_file_pairing(self):
        original = [meta(), item("function_call", BEFORE, call_id="one", name="exec_command", arguments="{}")]
        # Active fragment appears before archive file containing the prior call.
        self.write([meta(), item("function_call_output", call_id="one", output="exit code 0")])
        self.write(original, directory=self.archive)
        self.write(original + [user("resumed")], "copy.jsonl", self.archive)
        result = self.collect()
        self.assertEqual(len(result["sessions"]), 1)
        self.assertEqual(len(self.events(result)), 2)
        self.assertGreaterEqual(result["coverage"]["duplicate_records"], 1)
        self.assertEqual(self.events(result)[0]["call"]["name"], "exec_command")
        self.assertEqual(len(result["sessions"][0]["source_files"]), 3)

    def test_corrections_successful_friction_and_denials_are_candidates(self):
        self.write([meta(), user("No, I already approved that"),
                    user("You asked me again despite approval"),
                    item("function_call_output", call_id="one", output="exit code 0; workaround needed"),
                    item("function_call_output", call_id="two", output="exit code 1; permission denied")])
        events = self.events(self.collect())
        self.assertIn("correction_candidate", events[0]["signals"])
        self.assertIn("correction_candidate", events[1]["signals"])
        self.assertIn("friction_candidate", events[2]["signals"])
        self.assertIn("denial_candidate", events[3]["signals"])
        self.assertNotIn("expected_denial", json.dumps(events))

    def test_embedded_replayed_json_does_not_become_new_events(self):
        embedded = json.dumps(user("No, wrong result"))
        self.write([meta(), item("function_call_output", call_id="one", output=embedded),
                    item("custom_tool_call", name="record_and_replay", call_id="two", input="replay")])
        self.assertEqual([e["kind"] for e in self.events(self.collect())], ["tool_result", "tool_call"])

    def test_default_no_text_and_private_detail_redaction_and_bounds(self):
        text = 'Instead token=synthetic_secret email=person@example.test https://private.example/person password: "secret with spaces"'
        self.write([meta(), user(text), item("custom_tool_call", call_id="one", name="exec_command", input=text)])
        result = self.collect()
        encoded = json.dumps(result)
        for sensitive in ("synthetic_secret", "person@example.test", "private.example", "secret with spaces", '"text"', '"input"'):
            self.assertNotIn(sensitive, encoded)
        reference = self.events(result)[0]["source_ref"]
        excerpt = scanner.detail([self.active, self.archive], reference)
        for sensitive in ("synthetic_secret", "person@example.test", "private.example", "secret with spaces"):
            self.assertNotIn(sensitive, excerpt["text"])
        short = scanner.detail([self.active, self.archive], reference, max_chars=5)
        self.assertEqual(len(short["text"]), 5)
        self.assertTrue(short["truncated"])
        with self.assertRaises(ValueError):
            scanner.detail([self.active], reference, max_bytes=10)
        with self.assertRaises(ValueError):
            scanner.detail([self.active], reference, max_chars=16001)

    def test_detail_changed_path_traversal_symlink_and_record_boundary(self):
        path = self.write([meta(), user("one")])
        ref = self.events(self.collect())[0]["source_ref"]
        for altered in ({**ref, "relative_path": "../outside.jsonl"},
                        {**ref, "byte_offset": ref["byte_offset"] + 1},
                        {**ref, "root_index": 99}, {**ref, "byte_length": -1}):
            with self.assertRaises(ValueError):
                scanner.detail([self.active], altered)
        link = self.active / "linked.jsonl"
        link.symlink_to(path)
        with self.assertRaises(ValueError):
            scanner.detail([self.active], {**ref, "relative_path": link.name})
        path.write_bytes(path.read_bytes().replace(b'one', b'two'))
        with self.assertRaises(ValueError):
            scanner.detail([self.active], ref)

    def test_partial_record_recovered_by_next_bounded_rescan(self):
        pending = json.dumps(user("later")).encode()
        path = self.write([meta(), user("earlier")], tail=pending[:20])
        first = self.collect()
        self.assertEqual(first["coverage"]["incomplete_trailing_records"], 1)
        self.assertFalse(first["complete_within_supported_scope"])
        with path.open("ab") as handle:
            handle.write(pending[20:] + b"\n")
        self.assertEqual(len(self.events(self.collect())), 2)

    def test_limits_disclose_truncation_and_bound_reads(self):
        self.write([meta(), *[user(str(i)) for i in range(20)]])
        for kwargs, reason in (({"max_events": 2}, "max_events"),
                               ({"max_bytes": 250}, "max_bytes"),
                               ({"max_scan_records": 3}, "max_scan_records")):
            with self.subTest(reason=reason):
                result = self.collect(**kwargs)
                self.assertIn(reason, result["truncation"])
                self.assertFalse(result["complete_within_supported_scope"])
                self.assertLessEqual(result["coverage"]["bytes_read"], kwargs.get("max_bytes", 64 * 1024 * 1024))
        self.write([meta("two"), user("two")], "second.jsonl")
        self.assertIn("max_files", self.collect(max_files=1)["truncation"])
        self.assertIn("max_sessions", self.collect(max_sessions=1)["truncation"])
        self.assertIn("max_directory_entries", self.collect(max_directory_entries=1)["truncation"])

    def test_oversized_and_malformed_records_disclose_source_gaps(self):
        self.write([meta(), user("x" * 2000)])
        result = self.collect(max_line_bytes=300)
        self.assertIn("oversized_record_file_stopped", [g["reason"] for g in result["source_gaps"]])
        self.assertLessEqual(result["coverage"]["bytes_read"], 500)
        self.write([meta()], "bad.jsonl", tail=b"not json\n")
        self.assertEqual(self.collect()["coverage"]["malformed_records"], 1)

    def test_missing_root_access_denial_unknown_source_and_missing_time(self):
        missing = scanner.collect([self.root / "absent"])
        self.assertEqual(missing["source_gaps"][0]["reason"], "root_missing_or_not_directory")
        path = self.write([meta(source="future_source"), {"type": "response_item", "payload": {"type": "message", "role": "user", "content": "untimed"}}])
        result = self.collect()
        self.assertEqual(result["coverage"]["untimestamped_events"], 1)
        self.assertIn("unknown_session_source", [g["reason"] for g in result["source_gaps"]])
        original_open = os.open
        def denied(candidate, *args, **kwargs):
            if Path(candidate).name == path.name:
                raise PermissionError("SENSITIVE ERROR MUST NOT APPEAR")
            return original_open(candidate, *args, **kwargs)
        with patch.object(scanner.os, "open", side_effect=denied):
            result = self.collect()
        self.assertIn("file_unreadable", [g["reason"] for g in result["source_gaps"]])
        self.assertNotIn("SENSITIVE", json.dumps(result))

    def test_mcp_structured_and_json_string_results(self):
        output = {"isError": True, "content": [{"type": "text", "text": 'Permission denied; token="synthetic secret"'}]}
        self.write([meta(), item("function_call_output", call_id="one", output=output),
                    item("function_call_output", call_id="two", output=json.dumps(output))])
        events = self.events(self.collect())
        for event in events:
            self.assertTrue(event["status"]["is_error"])
            self.assertIn("denial_candidate", event["signals"])
            excerpt = scanner.detail([self.active], event["source_ref"])
            self.assertIn("Permission denied", excerpt["text"])
            self.assertNotIn("synthetic secret", excerpt["text"])

    def test_detail_rejects_nonregular_files_without_blocking(self):
        fifo = self.active / "pipe.jsonl"
        os.mkfifo(fifo)
        ref = {"root_index": 0, "relative_path": fifo.name, "byte_offset": 0, "byte_length": 1, "sha256": "x"}
        with self.assertRaises(ValueError):
            scanner.detail([self.active], ref)

    def test_pending_call_eviction_is_disclosed(self):
        self.write([meta(), item("function_call", BEFORE, name="one", call_id="one"),
                    item("function_call", BEFORE, name="two", call_id="two"),
                    item("function_call_output", call_id="one", output="done")])
        result = self.collect(max_pending_calls=1)
        self.assertIn("max_pending_calls", result["truncation"])
        self.assertEqual(self.events(result)[0]["pairing"], "call_not_found_in_bounded_scan")

    def test_invalid_limits_and_naive_boundaries_rejected(self):
        for limit in (0, -1, True):
            with self.assertRaises(ValueError):
                self.collect(max_events=limit)
        with self.assertRaises(ValueError):
            scanner.collect([self.active], LOWER.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            scanner.collect([self.active], UPPER, LOWER)

    def test_cli_authorization_and_private_output_no_stdout(self):
        self.write([meta(), user("sensitive prose")])
        output = self.root / "private" / "index.json"
        command = [sys.executable, str(SCRIPT), "--source-root", str(self.active),
                   "--source-host", "fixture", "--output", str(output)]
        denied = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse(output.exists())
        allowed = subprocess.run(command + ["--authorized"], capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(allowed.stdout, "")
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(output.parent.stat().st_mode), 0o700)
        self.assertNotIn("sensitive prose", output.read_text())
        output.parent.chmod(0o755)
        unsafe = subprocess.run(command + ["--authorized"], capture_output=True, text=True)
        self.assertNotEqual(unsafe.returncode, 0)
        self.assertEqual(unsafe.stdout, "")


if __name__ == "__main__":
    unittest.main()
