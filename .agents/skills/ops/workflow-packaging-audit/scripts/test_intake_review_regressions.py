"""Collector-to-intake regressions for clock, identity and artifact boundaries."""
import copy
import json
import os
import unittest
from unittest.mock import patch

import central_intake as intake
import test_scan_codex_sessions as fixtures
import test_central_intake_boundaries as boundaries


class ReviewRegressionTests(unittest.TestCase):
    setUp = fixtures.ScannerTests.setUp
    write = fixtures.ScannerTests.write
    collect = fixtures.ScannerTests.collect
    prepare = boundaries.IntakeBoundaryTests.prepare
    submit = boundaries.IntakeBoundaryTests.submit
    assert_cannot_acknowledge = boundaries.IntakeBoundaryTests.assert_cannot_acknowledge

    def test_future_generation_and_window_cannot_advance(self):
        state, original = self.prepare()
        for name, through, generated in (
                ("both-future", "2035-01-02T00:00:00+00:00", "2035-01-03T00:00:00+00:00"),
                ("future-generation", original["window"]["through"], "2035-01-03T00:00:00+00:00"),
                ("one-microsecond", "2026-09-21T00:00:00.000001+00:00", "2026-09-21T00:00:00.000001+00:00")):
            with self.subTest(name=name):
                bundle = copy.deepcopy(original)
                bundle["window"]["through"] = through
                bundle["generated_at"] = generated
                with patch.object(intake, "clock_now", return_value="2026-09-21T00:00:00+00:00"):
                    run = self.submit(state, bundle, name)
                    self.assertEqual(run["hosts"]["alpha"]["status"], "partial")
                    self.assertEqual(len(run["events"]), 1)
                    self.assert_cannot_acknowledge(state, run, bundle, name)

    def test_clock_boundary_and_backward_clock_before_ack(self):
        state, bundle = self.prepare()
        now = bundle["window"]["through"]
        bundle["generated_at"] = now
        with patch.object(intake, "clock_now", return_value=now):
            run = self.submit(state, bundle)
        self.assertTrue(run["hosts"]["alpha"]["eligible"])
        with patch.object(intake, "clock_now", return_value=bundle["window"]["after"]):
            with self.assertRaises(ValueError):
                intake.acknowledge(state, "sample", run["digest"], "alpha", bundle["window"]["after"])
        self.assertEqual(intake.decode(intake.read_private(state / "ledger.json"))["acknowledged_collector_windows"], {})
        with patch.object(intake, "clock_now", return_value=now):
            intake.acknowledge(state, "sample", run["digest"], "alpha", bundle["window"]["after"])

    def test_corrupt_category_counters_cannot_authorize_checkpoint(self):
        state, original = self.prepare()
        for name in ("out_of_window_events", "unsupported_records", "duplicate_records",
                     "malformed_records", "incomplete_trailing_records", "untimestamped_events",
                     "pending_calls_evicted", "excluded_session_files", "excluded_sidecar_files"):
            with self.subTest(counter=name):
                bundle = copy.deepcopy(original)
                source = "files_read" if name.startswith("excluded_") else "records_read"
                bundle["coverage"][name] = bundle["coverage"][source] + 1
                run = self.submit(state, bundle, name)
                self.assertEqual(run["hosts"]["alpha"]["status"], "invalid_or_denied")
                self.assert_cannot_acknowledge(state, run, bundle, name)
        bundle = copy.deepcopy(original)
        bundle["coverage"].update(excluded_session_files=1, excluded_sidecar_files=1)
        run = self.submit(state, bundle, "combined-exclusions")
        self.assert_cannot_acknowledge(state, run, bundle, "combined-exclusions")

    def test_real_excluded_files_and_out_of_window_records_remain_valid(self):
        state, _ = self.prepare()
        self.write([fixtures.meta("excluded"), fixtures.user("excluded")], name="excluded.jsonl")
        self.write([fixtures.meta("sidecar", "approval")], name="sidecar.jsonl")
        self.write([fixtures.meta("old"), fixtures.user("old", fixtures.OLD),
                    {"type": "unsupported"}], name="old.jsonl")
        bundle = self.collect(source_host="alpha", exclude={"excluded"})
        self.assertEqual(bundle["coverage"]["excluded_session_files"], 1)
        self.assertEqual(bundle["coverage"]["excluded_sidecar_files"], 1)
        self.assertEqual(bundle["coverage"]["out_of_window_events"], 1)
        self.assertEqual(bundle["coverage"]["unsupported_records"], 1)
        self.assertTrue(self.submit(state, bundle)["hosts"]["alpha"]["eligible"])

    def test_different_serializations_merge_across_hosts_and_keep_repetitions(self):
        state, _ = self.prepare()
        records = [fixtures.meta(), fixtures.user("same"), fixtures.user("same"),
                   fixtures.item("function_call", name="test", call_id="one", arguments="{}")]
        first = self.write(records)
        second = self.archive / "other.jsonl"
        second.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in records))
        manifests = {}
        bundles = []
        for host, recent, old in (("alpha", first, second), ("beta", second, first)):
            os.utime(recent, (200, 200)); os.utime(old, (100, 100))
            bundle = self.collect(source_host=host)
            self.assertEqual(bundle["coverage"]["emitted_events"], 3)
            self.assertEqual(bundle["coverage"]["duplicate_records"], 3)
            bundles.append(bundle)
            path = self.root / (host + ".json")
            fixtures.scanner._write_private(path, bundle)
            manifests[host] = {"status": "available", "window": bundle["window"], "path": str(path)}
        self.assertNotEqual(bundles[0]["sessions"][0]["events"][0]["source_ref"]["sha256"],
                            bundles[1]["sessions"][0]["events"][0]["source_ref"]["sha256"])
        run = intake.intake(state, "copies", manifests)
        self.assertEqual(len(run["events"]), 3)
        self.assertTrue(all(len(e["provenance"]) == 2 and len(e["raw_sha256s"]) == 2 for e in run["events"].values()))
        self.assertTrue(all(e["eligible"] for e in run["hosts"].values()))

    def test_invalid_or_missing_canonical_digests_rejected(self):
        state, original = self.prepare()
        for i, value in enumerate(([], ["private text"], ["a" * 64] * 2, ["b" * 64, "a" * 64], None)):
            bundle = copy.deepcopy(original)
            event = bundle["sessions"][0]["events"][0]
            if value is None:
                event.pop("canonical_sha256s")
            else:
                event["canonical_sha256s"] = value
            run = self.submit(state, bundle, "digest-" + str(i))
            self.assertEqual(run["hosts"]["alpha"]["status"], "invalid_or_denied")
        bundle = copy.deepcopy(original)
        bundle["schema"] = "codex-evidence-index.v2"
        self.assertEqual(self.submit(state, bundle, "legacy")["hosts"]["alpha"]["status"], "invalid_or_denied")

    def test_default_output_ceiling_preserves_partial_long_path_evidence(self):
        state, _ = self.prepare()
        directory = self.active
        for i in range(4):
            directory = directory / (str(i) + "x" * 179)
            directory.mkdir()
        records = [fixtures.meta("long-path")]
        for i in range(2400):
            records.extend([fixtures.item("function_call", name="test", call_id=str(i), arguments="{}"),
                            fixtures.item("function_call_output", call_id=str(i), output="exit code 0")])
        self.write(records, directory=directory)
        bundle = self.collect(source_host="alpha")
        self.assertEqual(bundle["truncation"], ["max_output_bytes"])
        self.assertGreater(bundle["coverage"]["emitted_events"], 0)
        self.assertLess(bundle["coverage"]["emitted_events"], 4801)
        result = self.submit(state, bundle)
        self.assertLessEqual((self.root / "index.json").stat().st_size, intake.MAX_INPUT)
        self.assertEqual(result["hosts"]["alpha"]["status"], "partial")
        self.assertEqual(len(result["events"]), bundle["coverage"]["emitted_events"])
        self.assert_cannot_acknowledge(state, result, bundle, "sample")
        for session in bundle["sessions"]:
            for event in (session["events"][0], session["events"][-1]):
                fixtures.scanner.detail([self.active, self.archive], event["source_ref"])
                if "call" in event:
                    fixtures.scanner.detail([self.active, self.archive], event["call"]["source_ref"])

    def test_output_cap_includes_gaps_and_serialization_boundary(self):
        state, bundle = self.prepare()
        size = len((json.dumps(bundle, indent=2) + "\n").encode())
        with patch.object(fixtures.scanner, "MAX_INDEX_BYTES", size):
            self.assertTrue(fixtures.scanner._bound_index(copy.deepcopy(bundle))["complete_within_supported_scope"])
        with patch.object(fixtures.scanner, "MAX_INDEX_BYTES", size - 1):
            trimmed = fixtures.scanner._bound_index(copy.deepcopy(bundle))
        self.assertLessEqual(len((json.dumps(trimmed, indent=2) + "\n").encode()), size - 1)
        self.assert_cannot_acknowledge(state, self.submit(state, trimmed, "trimmed"), trimmed, "trimmed")
        bundle["source_gaps"] = [{"reason": "file_unreadable", "relative_path": "x" * 3000}] * 20
        with patch.object(fixtures.scanner, "MAX_INDEX_BYTES", 5000):
            trimmed = fixtures.scanner._bound_index(bundle)
        self.assertLessEqual(len((json.dumps(trimmed, indent=2) + "\n").encode()), 5000)
        self.assertIn("max_output_bytes", trimmed["truncation"])
        self.assert_cannot_acknowledge(state, self.submit(state, trimmed, "gaps"), trimmed, "gaps")


if __name__ == "__main__":
    unittest.main()
