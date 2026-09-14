"""Independent intake contract cases using synthetic collector output."""
import copy
import subprocess
import sys
import unittest
from unittest.mock import patch

import central_intake as intake
import test_scan_codex_sessions as fixtures


class IntakeBoundaryTests(unittest.TestCase):
    setUp = fixtures.ScannerTests.setUp
    write = fixtures.ScannerTests.write
    collect = fixtures.ScannerTests.collect

    def prepare(self):
        # tempfile may use the system /var symlink on macOS; inputs use the
        # canonical private directory required by the no-follow interface.
        self.root = self.root.resolve()
        self.write([fixtures.meta(), fixtures.user("synthetic correction")])
        bundle = self.collect(source_host="alpha")
        state = self.root / "state"
        state.mkdir(mode=0o700)
        return state, bundle

    def submit(self, state, bundle, run="sample"):
        path = self.root / "index.json"
        fixtures.scanner._write_private(path, bundle)
        return intake.intake(state, run, {"alpha": {
            "status": "available", "window": bundle["window"], "path": str(path)}})

    def test_actual_collector_index_is_supported_not_all_source_complete(self):
        state, bundle = self.prepare()
        result = self.submit(state, bundle)
        self.assertTrue(result["hosts"]["alpha"]["eligible"])
        self.assertFalse(result["all_sources_complete"])
        ledger = intake.decode(intake.read_private(state / "ledger.json"))
        self.assertEqual(ledger["acknowledged_collector_windows"], {})

    def test_event_count_mismatch_cannot_be_acknowledged(self):
        state, bundle = self.prepare()
        bundle["coverage"]["emitted_events"] += 1
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])
        with self.assertRaises(ValueError):
            intake.acknowledge(state, "sample", result["digest"], "alpha", bundle["window"]["after"])

    def test_acknowledgment_leaves_other_offline_host_pending(self):
        state, bundle = self.prepare()
        path = self.root / "index.json"
        fixtures.scanner._write_private(path, bundle)
        run = intake.intake(state, "mixed", {
            "alpha": {"status": "available", "window": bundle["window"], "path": str(path)},
            "beta": {"status": "offline", "window": bundle["window"]}})
        intake.acknowledge(state, "mixed", run["digest"], "alpha", bundle["window"]["after"])
        ledger = intake.decode(intake.read_private(state / "ledger.json"))
        self.assertEqual(set(ledger["acknowledged_collector_windows"]), {"alpha"})
        self.assertEqual(ledger["runs"]["mixed"]["hosts"]["beta"]["status"], "offline")

    def test_unknown_event_text_is_not_persisted(self):
        state, bundle = self.prepare()
        bundle["sessions"][0]["events"][0]["text"] = "synthetic-private-unexpected-text"
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])
        self.assertNotIn(b"synthetic-private-unexpected-text", intake.read_private(state / "ledger.json"))

    def test_unrepresentable_timestamp_is_invalid_input_not_a_crash(self):
        state, bundle = self.prepare()
        bundle["generated_at"] = "0001-01-01T00:00:00+23:00"
        result = self.submit(state, bundle)
        self.assertEqual(result["hosts"]["alpha"]["status"], "invalid_or_denied")

    def test_window_after_generation_cannot_advance(self):
        state, bundle = self.prepare()
        bundle["generated_at"] = bundle["window"]["after"]
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])
        with self.assertRaises(ValueError):
            intake.acknowledge(state, "sample", result["digest"], "alpha", bundle["window"]["after"])

    def test_collector_narratives_cannot_persist_transcript_text(self):
        state, original = self.prepare()
        for key in ("limitations", "truncation"):
            with self.subTest(key=key):
                bundle = copy.deepcopy(original)
                bundle[key] = ["SYNTHETIC UNEXPECTED PRIVATE TRANSCRIPT"]
                result = self.submit(state, bundle, run=key)
                self.assertFalse(result["hosts"]["alpha"]["eligible"])
                self.assertNotIn(b"SYNTHETIC UNEXPECTED PRIVATE TRANSCRIPT", intake.read_private(state / "ledger.json"))

    def test_disabled_archive_cannot_select_pre_window_event(self):
        state, bundle = self.prepare()
        session = bundle["sessions"][0]
        session["archived_at"] = int(fixtures.UPPER.timestamp())
        session["events"][0].update(timestamp=fixtures.OLD, selection_reasons=["session_archived_in_window"])
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])

    def test_reference_paths_must_belong_to_session(self):
        state, _ = self.prepare()
        self.write([fixtures.meta(), fixtures.item("function_call", name="exec_command", call_id="one"),
                    fixtures.item("function_call_output", call_id="one", output="exit code 0")])
        original = self.collect(source_host="alpha")
        for kind in ("primary", "mirror", "call"):
            with self.subTest(kind=kind):
                bundle = copy.deepcopy(original)
                event = next(e for e in bundle["sessions"][0]["events"] if e["kind"] == "tool_result")
                bad = {**event["source_ref"], "relative_path": "unrelated.jsonl"}
                if kind == "primary":
                    event["source_ref"] = bad
                elif kind == "mirror":
                    event["mirror_source_refs"] = [bad]
                else:
                    event["call"]["source_ref"] = bad
                result = self.submit(state, bundle, run=kind)
                self.assertFalse(result["hosts"]["alpha"]["eligible"])

    def test_real_opposite_discovery_orders_merge_mirrored_event(self):
        state, _ = self.prepare()
        self.write([fixtures.meta(), fixtures.user("same")])
        self.write([fixtures.meta(), {"type": "event_msg", "timestamp": fixtures.NOW,
                    "payload": {"type": "user_message", "message": "same"}}], directory=self.archive)
        manifests = {}
        for host, roots in (("alpha", [self.active, self.archive]), ("beta", [self.archive, self.active])):
            bundle = fixtures.scanner.collect(roots, fixtures.LOWER, fixtures.UPPER, source_host=host)
            path = self.root / (host + ".json")
            fixtures.scanner._write_private(path, bundle)
            manifests[host] = {"status": "available", "window": bundle["window"], "path": str(path)}
        result = intake.intake(state, "mirrored", manifests)
        self.assertEqual(len(result["events"]), 1)
        provenance = next(iter(result["events"].values()))["provenance"]
        self.assertEqual({ref["host"] for ref in provenance}, {"alpha", "beta"})
        self.assertEqual(len(provenance), 4)

    def test_missing_root_preserves_other_root_evidence(self):
        state, _ = self.prepare()
        original = fixtures.scanner.os.scandir

        def denied_archive(path):
            if str(path) == str(self.archive.resolve()):
                raise PermissionError("synthetic denied root")
            return original(path)

        with patch.object(fixtures.scanner.os, "scandir", side_effect=denied_archive):
            bundle = self.collect(source_host="alpha")
        self.assertTrue(any(gap.get("relative_path") == "." for gap in bundle["source_gaps"]))
        result = self.submit(state, bundle)
        self.assertEqual(result["hosts"]["alpha"]["status"], "partial")
        self.assertEqual(len(result["events"]), 1)

    def test_removed_archive_freshness_gap_cannot_advance(self):
        state, bundle = self.prepare()
        bundle["archive_metadata"]["status"] = "snapshot_read"
        self.assertEqual(bundle["source_gaps"], [])
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])

    def test_mirror_references_survive_merged_provenance(self):
        state, _ = self.prepare()
        self.write([fixtures.meta(), fixtures.user("same"),
                    {"type": "event_msg", "timestamp": fixtures.NOW,
                     "payload": {"type": "user_message", "message": "same"}}])
        bundle = self.collect(source_host="alpha")
        result = self.submit(state, bundle)
        self.assertEqual(len(result["events"]), 1)
        provenance = next(iter(result["events"].values()))["provenance"]
        refs = [entry["source_ref"] for entry in provenance]
        event = bundle["sessions"][0]["events"][0]
        self.assertIn(event["source_ref"], refs)
        self.assertIn(event["mirror_source_refs"][0], refs)

    def test_archive_selection_does_not_admit_future_event(self):
        state, bundle = self.prepare()
        session = bundle["sessions"][0]
        session["archived_at"] = int(fixtures.UPPER.timestamp())
        event = session["events"][0]
        event["selection_reasons"] = ["session_archived_in_window"]
        event["timestamp"] = "2099-01-01T00:00:00Z"
        result = self.submit(state, bundle)
        self.assertFalse(result["hosts"]["alpha"]["eligible"])

    def test_actual_archive_selected_bundle_retains_partial_evidence(self):
        state, _ = self.prepare()
        path = self.write([fixtures.meta("archived-session"), fixtures.user("old", fixtures.OLD)],
                          directory=self.archive)
        database, _ = fixtures.ScannerTests.database(self, [
            ("archived-session", str(path), 1, int(fixtures.UPPER.timestamp()))])
        bundle = self.collect(source_host="alpha", archive_db=database, archive_db_roots=[self.root])
        result = self.submit(state, bundle)
        self.assertEqual(result["hosts"]["alpha"]["status"], "partial")
        self.assertFalse(result["hosts"]["alpha"]["eligible"])
        self.assertEqual(len(result["events"]), bundle["coverage"]["emitted_events"])

    def test_traversal_and_boolean_offsets_are_invalid(self):
        state, original = self.prepare()
        for number, mutation in enumerate(({"relative_path": "../outside.jsonl"}, {"byte_offset": False})):
            with self.subTest(mutation=mutation):
                bundle = copy.deepcopy(original)
                bundle["sessions"][0]["events"][0]["source_ref"].update(mutation)
                result = self.submit(state, bundle, run="invalid-" + str(number))
                self.assertFalse(result["hosts"]["alpha"]["eligible"])

    def test_cli_requires_authorization_and_keeps_evidence_off_stdout(self):
        state, bundle = self.prepare()
        path = self.root / "index.json"
        manifest = self.root / "manifest.json"
        fixtures.scanner._write_private(path, bundle)
        fixtures.scanner._write_private(manifest, {"alpha": {
            "status": "available", "window": bundle["window"], "path": str(path)}})
        command = [sys.executable, intake.__file__, "--state", str(state),
                   "intake", "--run", "cli", "--manifest", str(manifest)]
        denied = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(denied.returncode, 0)
        self.assertFalse((state / "ledger.json").exists())
        command.insert(2, "--authorized")
        accepted = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertEqual(accepted.stdout, "")
        ledger = intake.decode(intake.read_private(state / "ledger.json"))
        digest = ledger["runs"]["cli"]["digest"]
        ack = subprocess.run([sys.executable, intake.__file__, "--authorized", "--state", str(state),
                              "acknowledge", "--run", "cli", "--digest", digest, "--host", "alpha",
                              "--previous", bundle["window"]["after"]],
                             capture_output=True, text=True, timeout=10)
        self.assertEqual(ack.returncode, 0, ack.stderr)
        self.assertEqual(ack.stdout, "")


if __name__ == "__main__":
    unittest.main()
