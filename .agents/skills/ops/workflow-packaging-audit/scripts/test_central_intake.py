"""Synthetic local intake integration and persistence boundaries."""
import copy
import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import central_intake as intake
import scan_codex_sessions as scanner

LOW = "2026-09-01T00:00:00+00:00"
HIGH = "2026-09-02T00:00:00+00:00"
NEXT = "2026-09-03T00:00:00+00:00"


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.state = self.root / "state"
        self.state.mkdir(mode=0o700)
        source = self.root / "source"
        source.mkdir(mode=0o700)
        records = [{"type": "session_meta", "payload": {"id": "synthetic", "source": "cli"}},
                   {"type": "response_item", "timestamp": HIGH,
                    "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "synthetic"}]}}]
        (source / "session.jsonl").write_text("\n".join(json.dumps(r) for r in records))
        self.bundle = scanner.collect([source], dt.datetime.fromisoformat(LOW), dt.datetime.fromisoformat(HIGH), source_host="alpha")
        self.path = self.root / "bundle.json"
        self.write(self.bundle)
        self.hosts = {"alpha": {"status": "available", "window": {"after": LOW, "through": HIGH}, "path": str(self.path)}}

    def write(self, bundle):
        self.path.write_text(json.dumps(bundle))
        self.path.chmod(0o600)

    def run_intake(self, run="one"):
        return intake.intake(self.state, run, self.hosts)

    def ledger(self):
        return json.loads((self.state / "ledger.json").read_text())

    def ack(self, run, name="one", previous=LOW):
        intake.acknowledge(self.state, name, run["digest"], "alpha", previous)

    def test_actual_collector_idempotent_and_acknowledgment(self):
        run = self.run_intake()
        self.assertTrue(run["hosts"]["alpha"]["eligible"])
        self.assertEqual(len(run["events"]), 1)
        before = (self.state / "ledger.json").read_bytes()
        self.assertEqual(run, self.run_intake())
        self.assertEqual(before, (self.state / "ledger.json").read_bytes())
        self.assertEqual(self.ledger()["acknowledged_collector_windows"], {})
        self.ack(run)
        self.ack(run)
        self.assertFalse(run["all_sources_complete"])
        self.assertEqual((self.state / "ledger.json").stat().st_mode & 0o777, 0o600)

    def test_offline_catch_up_and_monotonic_windows(self):
        self.hosts["alpha"]["status"] = "offline"
        offline = self.run_intake("offline")
        self.assertEqual(offline["hosts"]["alpha"]["status"], "offline")
        with self.assertRaises(ValueError):
            self.ack(offline, "offline")
        self.hosts["alpha"]["status"] = "available"
        first = self.run_intake()
        self.ack(first)
        self.bundle["window"] = {"after": HIGH, "through": NEXT}
        self.bundle["sessions"] = []
        self.bundle["coverage"].update(sessions_included=0, emitted_events=0)
        self.hosts["alpha"]["window"] = self.bundle["window"]
        self.write(self.bundle)
        second = self.run_intake("two")
        with self.assertRaises(ValueError):
            self.ack(second, "two", LOW)
        self.ack(second, "two", HIGH)
        with self.assertRaises(ValueError):
            self.ack(first)

    def test_partial_and_malformed_are_nonadvancing(self):
        for mutate in (
                lambda b: b["source_gaps"].append({"reason": "file_unreadable"}),
                lambda b: b["truncation"].append("max_events"),
                lambda b: b.update(source_host="wrong"),
                lambda b: b.update(sessions=[{}]),
                lambda b: b["window"].update(through=NEXT),
                lambda b: b["sessions"][0]["events"][0]["source_ref"].update(byte_offset=True),
                lambda b: b["sessions"][0]["events"][0]["source_ref"].update(relative_path="../escape")):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle)
            self.write(bundle)
            run = self.run_intake(str(len(self.ledger()["runs"])) if (self.state / "ledger.json").exists() else "0")
            self.assertFalse(run["hosts"]["alpha"]["eligible"])
        self.assertEqual(self.ledger()["acknowledged_collector_windows"], {})

    def test_changed_run_rejected(self):
        self.run_intake()
        self.bundle["source_gaps"].append({"reason": "incomplete_trailing_record"})
        self.write(self.bundle)
        before = (self.state / "ledger.json").read_bytes()
        with self.assertRaises(ValueError):
            self.run_intake()
        self.assertEqual(before, (self.state / "ledger.json").read_bytes())

    def test_nested_content_and_unknown_kinds_rejected(self):
        for index, mutate in enumerate((
                lambda b: b["sessions"][0]["events"][0].update(name={"text": "private body"}),
                lambda b: b["sessions"][0]["events"][0].update(kind="unknown_event"),
                lambda b: b["sessions"][0]["events"][0].update(status={"exit_code": {"text": "body"}}),
                lambda b: b["sessions"][0]["source_files"][0].update(text="private body"),
                lambda b: b["archive_metadata"].update(text="private body"),
                lambda b: b["limitations"].append({"text": "private body"}))):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle)
            self.write(bundle)
            run = self.run_intake("nested-" + str(index))
            self.assertEqual(run["hosts"]["alpha"]["status"], "invalid_or_denied")
            self.assertNotIn("bundle", run["hosts"]["alpha"])

    def test_null_tool_label_remains_supported(self):
        self.bundle["sessions"][0]["events"][0].update(kind="tool_call", name=None)
        self.bundle["sessions"][0]["events"][0].pop("signals")
        self.write(self.bundle)
        self.assertTrue(self.run_intake()["hosts"]["alpha"]["eligible"])

    def test_declared_budgets_prevent_ack_without_discarding_evidence(self):
        for index, (counter, limit) in enumerate((("records_read", "max_scan_records"), ("bytes_read", "max_bytes"),
                ("files_discovered", "max_files"), ("directory_entries", "max_directory_entries"),
                ("emitted_events", "max_events"), ("sessions_included", "max_sessions"))):
            bundle = copy.deepcopy(self.bundle)
            if counter in ("emitted_events", "sessions_included"):
                # All nonzero fixture counts are within positive minimum limits;
                # duplicate complete sessions to create a genuine over-budget index.
                extra = copy.deepcopy(bundle["sessions"][0])
                extra["id"] = "second"
                bundle["sessions"].append(extra)
                bundle["coverage"].update(emitted_events=2, sessions_included=2)
                bundle["limits"][limit] = 1
            else:
                bundle["coverage"][counter] = bundle["limits"][limit] + 1
            self.write(bundle)
            entry = self.run_intake("budget-" + str(index))["hosts"]["alpha"]
            self.assertEqual(entry["status"], "partial")
            self.assertIn("bundle", entry)

    def test_result_shapes_and_call_timing(self):
        event = self.bundle["sessions"][0]["events"][0]
        event.update(kind="tool_result", status={"exit_code": 0}, pairing="missing_call_id")
        self.write(self.bundle)
        self.assertTrue(self.run_intake("missing-call")["hosts"]["alpha"]["eligible"])
        event.pop("pairing")
        event.update(correlation_id="a" * 64, call={"name": None, "timestamp": LOW, "before_window": True, "source_ref": copy.deepcopy(event["source_ref"])})
        self.write(self.bundle)
        self.assertTrue(self.run_intake("paired")["hosts"]["alpha"]["eligible"])
        for index, mutate in enumerate((lambda e: e["call"].update(timestamp=NEXT),
                lambda e: e["call"].update(before_window=False), lambda e: e.pop("status"),
                lambda e: e.update(name="forbidden"), lambda e: e.update(kind="user_message"))):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle["sessions"][0]["events"][0])
            self.write(bundle)
            self.assertEqual(self.run_intake("shape-" + str(index))["hosts"]["alpha"]["status"], "invalid_or_denied")

    def test_uncertain_directory_sync_is_retried_for_intake_and_ack(self):
        original = intake.os.fsync
        attempts = []
        def fail_directory(fd):
            import stat
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                attempts.append(fd)
                raise OSError("synthetic directory sync failure")
            return original(fd)
        with patch.object(intake.os, "fsync", side_effect=fail_directory):
            with self.assertRaises(OSError):
                self.run_intake()
            with self.assertRaises(OSError):
                self.run_intake()
        self.assertEqual(len(attempts), 2)
        run = self.run_intake()
        with patch.object(intake.os, "fsync", side_effect=fail_directory):
            with self.assertRaises(OSError):
                self.ack(run)
            with self.assertRaises(OSError):
                self.ack(run)
        self.assertEqual(len(attempts), 4)
        self.ack(run)

    def test_nonadvancing_generation_and_archive_status(self):
        for index, mutate in enumerate((
                lambda b: b.update(generated_at=LOW),
                lambda b: b["archive_metadata"].update(status="snapshot_read"),
                lambda b: b["archive_metadata"].update(status="unavailable"))):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle)
            self.write(bundle)
            self.assertFalse(self.run_intake("nonadvancing-" + str(index))["hosts"]["alpha"]["eligible"])

    def test_limits_coverage_and_closed_event_metadata(self):
        for index, mutate in enumerate((
                lambda b: b["limits"].pop("max_files"),
                lambda b: b["coverage"].update(records_read=0),
                lambda b: b["coverage"].update(files_read=2, files_discovered=1),
                lambda b: b["sessions"][0]["events"][0].update(signals=["private text"]),
                lambda b: b["sessions"][0]["events"][0].update(pairing="private text"),
                lambda b: b["sessions"][0]["events"][0].update(correlation_id="private text"),
                lambda b: b["sessions"][0]["events"][0].update(status={"exit_code_source": "private text"}))):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle)
            self.write(bundle)
            self.assertEqual(self.run_intake("invalid-" + str(index))["hosts"]["alpha"]["status"], "invalid_or_denied")

    def test_root_gap_is_partial_but_root_event_reference_is_invalid(self):
        self.bundle["source_gaps"].append({"reason": "directory_unreadable", "root_index": 0, "relative_path": "."})
        self.write(self.bundle)
        run = self.run_intake("gap")
        self.assertEqual(run["hosts"]["alpha"]["status"], "partial")
        self.assertEqual(len(run["events"]), 1)
        self.bundle["sessions"][0]["events"][0]["source_ref"]["relative_path"] = "."
        self.write(self.bundle)
        self.assertEqual(self.run_intake("badref")["hosts"]["alpha"]["status"], "invalid_or_denied")

    def test_collector_host_label_and_invalid_ledger_containers(self):
        host = ".opaque:" + "a" * 150
        self.bundle["source_host"] = host
        self.hosts[host] = self.hosts.pop("alpha")
        self.write(self.bundle)
        self.assertTrue(self.run_intake()["hosts"][host]["eligible"])
        for invalid in ([], {"schema": "central-intake.v1", "runs": [], "acknowledged_collector_windows": {}},
                        {"schema": "central-intake.v1", "runs": {}, "acknowledged_collector_windows": []}):
            path = self.state / "ledger.json"
            path.write_text(json.dumps(invalid))
            with self.assertRaises(ValueError):
                self.run_intake("invalidledger")

    def test_copies_merge_preserving_occurrences_and_host_provenance(self):
        event = self.bundle["sessions"][0]["events"][0]
        self.bundle["sessions"][0]["events"].append(copy.deepcopy(event))
        self.bundle["sessions"][0]["events"][1]["source_ref"]["byte_offset"] += event["source_ref"]["byte_length"]
        self.bundle["coverage"]["emitted_events"] = 2
        self.write(self.bundle)
        other = copy.deepcopy(self.bundle)
        other["source_host"] = "beta"
        path = self.root / "other.json"
        path.write_text(json.dumps(other))
        path.chmod(0o600)
        self.hosts["beta"] = {**self.hosts["alpha"], "path": str(path)}
        run = self.run_intake()
        self.assertEqual(len(run["events"]), 2)
        self.assertTrue(all(len(e["provenance"]) == 2 for e in run["events"].values()))

    def test_reversed_mirror_primary_merges_and_keeps_repetitions(self):
        event = self.bundle["sessions"][0]["events"][0]
        mirror = {**event["source_ref"], "sha256": "f" * 64, "byte_offset": 999}
        event["mirror_source_refs"] = [mirror]
        self.bundle["sessions"][0]["events"].append(copy.deepcopy(event))
        self.bundle["coverage"].update(emitted_events=2, records_read=5)
        self.write(self.bundle)
        other = copy.deepcopy(self.bundle)
        other["source_host"] = "beta"
        for copied in other["sessions"][0]["events"]:
            copied["source_ref"], copied["mirror_source_refs"] = copied["mirror_source_refs"][0], [copied["source_ref"]]
        path = self.root / "beta.json"
        path.write_text(json.dumps(other))
        path.chmod(0o600)
        self.hosts["beta"] = {**self.hosts["alpha"], "path": str(path)}
        run = self.run_intake()
        self.assertEqual(len(run["events"]), 2)
        self.assertTrue(all(len(e["provenance"]) == 4 for e in run["events"].values()))
        self.assertTrue(all(len(e["raw_sha256s"]) == 2 for e in run["events"].values()))

    def test_closed_narratives_archive_contract_and_provenance_membership(self):
        for index, mutate in enumerate((
                lambda b: b["limitations"].append("private narrative"),
                lambda b: b["truncation"].append("private narrative"),
                lambda b: b["source_gaps"].append({"reason": "private narrative"}),
                lambda b: b["sessions"][0].update(id="Please include this private transcript body"),
                lambda b: b["archive_metadata"].update(rows_read=1),
                lambda b: b["sessions"][0].update(archived_at=1788220801),
                lambda b: b["sessions"][0]["events"][0]["source_ref"].update(relative_path="other.jsonl"),
                lambda b: b["sessions"][0]["events"][0].update(mirror_source_refs=[{**b["sessions"][0]["events"][0]["source_ref"], "relative_path": "other.jsonl"}]),
                lambda b: b["sessions"][0]["events"][0].update(call={"name": None, "timestamp": LOW, "before_window": True, "source_ref": {**b["sessions"][0]["events"][0]["source_ref"], "relative_path": "other.jsonl"}}))):
            bundle = copy.deepcopy(self.bundle)
            mutate(bundle)
            self.write(bundle)
            entry = self.run_intake("contract-" + str(index))["hosts"]["alpha"]
            self.assertEqual(entry["status"], "invalid_or_denied")
            self.assertNotIn("bundle", entry)

    def test_denial_symlink_fifo_and_modes(self):
        for name, setup in (("missing", lambda p: None), ("symlink", lambda p: p.symlink_to(self.path)),
                            ("fifo", lambda p: os.mkfifo(p, 0o600))):
            path = self.root / name
            setup(path)
            self.hosts["alpha"]["path"] = str(path)
            self.assertEqual(self.run_intake(name)["hosts"]["alpha"]["status"], "invalid_or_denied")
        self.path.chmod(0o644)
        self.hosts["alpha"]["path"] = str(self.path)
        self.assertFalse(self.run_intake("mode")["hosts"]["alpha"]["eligible"])
        alias = self.root / "alias"
        alias.symlink_to(self.state)
        with self.assertRaises(OSError):
            intake.intake(alias, "alias", self.hosts)

    def test_lock_exclusion_and_failed_write_rollback(self):
        self.run_intake()
        before = (self.state / "ledger.json").read_bytes()
        with intake.locked(self.state):
            with self.assertRaises(BlockingIOError):
                self.run_intake("blocked")
        with patch.object(intake.os, "replace", side_effect=OSError("synthetic failure")):
            with self.assertRaises(OSError):
                self.run_intake("failed")
        self.assertEqual(before, (self.state / "ledger.json").read_bytes())
        self.assertFalse(list(self.state.glob(".pending-*")))


if __name__ == "__main__":
    unittest.main()
