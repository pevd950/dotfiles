"""Synthetic-only fixtures shaped like actual Codex JSONL envelopes."""
import importlib.util
from contextlib import contextmanager
import json
import os
from pathlib import Path
import stat
import sqlite3
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

    def database(self, rows, wal=False):
        path = self.root / "state.sqlite"
        connection = sqlite3.connect(path)
        if wal:
            connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE threads (id TEXT, rollout_path TEXT, archived INTEGER, archived_at INTEGER)")
        connection.executemany("INSERT INTO threads VALUES (?, ?, ?, ?)", rows)
        connection.commit()
        self.addCleanup(connection.close)
        return path, connection

    def with_database(self, path, **kwargs):
        return self.collect(archive_db=path, archive_db_roots=[self.root], **kwargs)

    def test_snapshot_archive_union_old_detail_and_read_only(self):
        archived = self.write([meta(), user("old private text", OLD)], directory=self.archive)
        self.write([meta("active"), user("new private text")], name="active.jsonl")
        database, connection = self.database([("session-one", str(archived), 1, int(scanner._time(NOW).timestamp()))])
        before = database.read_bytes(), connection.total_changes, set(self.root.iterdir())
        result = self.with_database(database)
        self.assertEqual(len(self.events(result)), 2)
        old = next(event for event in self.events(result) if "session_archived_in_window" in event["selection_reasons"])
        self.assertEqual(old["selection_reasons"], ["session_archived_in_window"])
        self.assertEqual(scanner.detail([self.active, self.archive], old["source_ref"])["text"], "old private text")
        self.assertNotIn("private text", json.dumps(result))
        self.assertEqual(before, (database.read_bytes(), connection.total_changes, set(self.root.iterdir())))
        self.assertIn("archive_snapshot_freshness_unverified", [gap["reason"] for gap in result["source_gaps"]])

    def test_wal_fails_closed_without_modifying_any_source(self):
        database, connection = self.database([], wal=True)
        paths = [database, Path(str(database) + "-wal"), Path(str(database) + "-shm")]
        before = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
        result = self.with_database(database)
        self.assertEqual(result["archive_metadata"]["status"], "unavailable")
        self.assertIn("archive_database_requires_quiescent_snapshot", [gap["reason"] for gap in result["source_gaps"]])
        self.assertEqual(before, {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths})

    def test_sidecars_including_dangling_symlinks_are_rejected_without_following(self):
        database, _ = self.database([])
        for suffix in ("-wal", "-shm", "-journal"):
            with self.subTest(suffix=suffix):
                sidecar = Path(str(database) + suffix)
                sidecar.symlink_to(self.root / "does-not-exist")
                result = self.with_database(database)
                self.assertEqual(result["archive_metadata"]["status"], "unavailable")
                self.assertTrue(sidecar.is_symlink())
                self.assertFalse((self.root / "does-not-exist").exists())
                sidecar.unlink()

    def test_wal_header_without_sidecars_is_not_assumed_checkpointed(self):
        database, connection = self.database([], wal=True)
        connection.close()
        self.assertFalse(Path(str(database) + "-wal").exists())
        before = database.read_bytes(), set(self.root.iterdir())
        result = self.with_database(database)
        self.assertEqual(result["archive_metadata"]["status"], "unavailable")
        self.assertEqual(before, (database.read_bytes(), set(self.root.iterdir())))

    def test_snapshot_rejects_observed_mutation_or_appearing_sidecar(self):
        database, _ = self.database([])
        original_open = scanner._open_source
        for mutation in ("timestamp", "sidecar"):
            with self.subTest(mutation=mutation):
                opened = 0

                @contextmanager
                def changing_open(root, relative):
                    nonlocal opened
                    if relative == database.name:
                        opened += 1
                        if opened == 2:
                            if mutation == "timestamp":
                                value = database.stat()
                                os.utime(database, ns=(value.st_atime_ns, value.st_mtime_ns + 1000000))
                            else:
                                Path(str(database) + "-wal").write_bytes(b"")
                    with original_open(root, relative) as handle:
                        yield handle

                with patch.object(scanner, "_open_source", changing_open):
                    result = self.with_database(database)
                self.assertEqual(result["archive_metadata"]["status"], "unavailable")
                self.assertIn("archive_database_changed_during_snapshot", [gap["reason"] for gap in result["source_gaps"]])

    def test_archive_boundaries_null_unarchived_and_missing_paths(self):
        rows = []
        for sid, archived, timestamp in (("lower", 1, int(LOWER.timestamp())), ("upper", 1, int(UPPER.timestamp())),
                                         ("future", 1, int(UPPER.timestamp()) + 1), ("null", 1, None), ("unarchived", 0, None)):
            path = self.write([meta(sid), user("old", OLD)], name=sid + ".jsonl")
            rows.append((sid, str(path), archived, timestamp))
        rows.append(("missing", str(self.active / "missing.jsonl"), 1, int(UPPER.timestamp())))
        database, _ = self.database(rows)
        result = self.with_database(database)
        self.assertEqual([session["id"] for session in result["sessions"]], ["upper"])
        gaps = [gap["reason"] for gap in result["source_gaps"]]
        self.assertIn("archive_database_missing_or_invalid_archive_time", gaps)
        self.assertIn("archive_database_archive_time_after_window", gaps)
        self.assertIn("archive_database_rollout_missing_or_unsafe", gaps)

    def test_archive_limits_schema_and_database_allowlist(self):
        path = self.write([meta(), user("old", OLD)])
        database, connection = self.database([("session-one", str(path), 1, int(UPPER.timestamp()))])
        result = self.collect(archive_db=database)
        self.assertEqual(self.events(result), [])
        self.assertEqual(result["source_gaps"][0]["reason"], "archive_database_outside_allowed_roots")
        result = self.with_database(database, max_archive_bytes=1)
        self.assertEqual(result["source_gaps"][0]["reason"], "archive_database_byte_limit")
        connection.execute("INSERT INTO threads VALUES ('second', ?, 1, ?)", (str(path), int(UPPER.timestamp())))
        connection.commit()
        result = self.with_database(database, max_archive_rows=1)
        self.assertIn("archive_database_row_limit", [gap["reason"] for gap in result["source_gaps"]])
        connection.execute("DROP TABLE threads")
        connection.execute("CREATE VIEW threads AS SELECT 'secret' AS id")
        connection.commit()
        result = self.with_database(database)
        self.assertEqual(result["source_gaps"][0]["reason"], "archive_database_unsupported_schema")

    def test_archive_unsafe_and_mismatched_rollout_paths(self):
        path = self.write([meta("actual"), user("old", OLD)])
        link = self.archive / "link.jsonl"
        link.symlink_to(path)
        database, _ = self.database([("mismatch", str(path), 1, int(UPPER.timestamp())),
                                      ("link", str(link), 1, int(UPPER.timestamp())),
                                      ("outside", str(self.root / "outside.jsonl"), 1, int(UPPER.timestamp()))])
        result = self.with_database(database)
        self.assertEqual(self.events(result), [])
        gaps = [gap["reason"] for gap in result["source_gaps"]]
        self.assertIn("archive_database_rollout_identity_mismatch", gaps)
        self.assertIn("archive_database_rollout_missing_or_unsafe", gaps)
        self.assertIn("archive_database_rollout_outside_allowed_roots", gaps)

    def test_archive_selection_respects_current_session_and_event_cap(self):
        path = self.write([meta(), user("old one", OLD), user("old two", OLD)])
        database, _ = self.database([("session-one", str(path), 1, int(UPPER.timestamp()))])
        self.assertEqual(self.events(self.with_database(database, exclude={"session-one"})), [])
        result = self.with_database(database, max_events=1)
        self.assertEqual(len(self.events(result)), 1)
        self.assertIn("max_events", result["truncation"])

    def test_archive_copy_of_previously_seen_old_records_is_selected(self):
        records = [meta(), user("old", OLD)]
        self.write(records)
        path = self.write(records, directory=self.archive)
        database, _ = self.database([("session-one", str(path), 1, int(UPPER.timestamp()))])
        result = self.with_database(database)
        self.assertEqual(len(self.events(result)), 1)
        self.assertEqual(self.events(result)[0]["selection_reasons"], ["session_archived_in_window"])

    def test_archive_query_limit_and_symlink_database_fail_closed(self):
        database, connection = self.database([])
        connection.executemany("INSERT INTO threads VALUES (?, '', 0, NULL)", [(str(index),) for index in range(200)])
        connection.commit()
        result = self.with_database(database, max_archive_query_steps=100)
        self.assertIn("archive_database_unreadable_invalid_or_query_limit", [gap["reason"] for gap in result["source_gaps"]])
        self.assertEqual(result["archive_metadata"]["selected_rollouts"], 0)
        link = self.root / "linked.sqlite"
        link.symlink_to(database)
        result = self.with_database(link)
        self.assertEqual(result["archive_metadata"]["status"], "unavailable")

    def test_copied_archived_mirrors_and_pairs_preserve_occurrences_and_union(self):
        records = [meta(), user("old", OLD),
                   {"timestamp": OLD, "type": "event_msg", "payload": {"type": "user_message", "message": "old"}},
                   item("function_call", OLD, name="exec_command", call_id="old-call", arguments="{}"),
                   item("function_call_output", OLD, call_id="old-call", output="exit code 0"),
                   user("repeated", NOW), user("repeated", NOW)]
        self.write(records)
        path = self.write(records, directory=self.archive)
        database, _ = self.database([("session-one", str(path), 1, int(UPPER.timestamp()))])
        events = self.events(self.with_database(database))
        self.assertEqual(len(events), 5)
        result = next(event for event in events if event["kind"] == "tool_result")
        self.assertEqual(result["call"]["name"], "exec_command")
        self.assertTrue(result["call"]["before_window"])
        old_message = next(event for event in events if event["kind"] == "user_message" and event["timestamp"] == scanner._time(OLD).isoformat())
        self.assertEqual(len(old_message["mirror_source_refs"]), 1)
        for event in events:
            self.assertIn("session_archived_in_window", event["selection_reasons"])
        recent = [event for event in events if event["timestamp"] == scanner._time(NOW).isoformat()]
        self.assertEqual(len(recent), 2)
        self.assertTrue(all("record_activity_in_window" in event["selection_reasons"] for event in recent))

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
                   "--source-host", "fixture", "--exclude-session", "current-fixture", "--output", str(output)]
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
