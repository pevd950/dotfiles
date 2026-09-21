"""Synthetic regressions for merged session event semantics."""
import json
import unittest
from unittest.mock import patch
import test_scan_codex_sessions as fixtures
from test_scan_codex_sessions import scanner, meta, item, user, BEFORE, NOW


class CollectorSemanticsTests(unittest.TestCase):
    setUp = fixtures.ScannerTests.setUp
    write = fixtures.ScannerTests.write
    collect = fixtures.ScannerTests.collect
    events = fixtures.ScannerTests.events
    def test_completed_calls_do_not_evict_pending_calls(self):
        self.write([meta(),
                    item("function_call", BEFORE, name="old", call_id="old"),
                    item("function_call_output", BEFORE, call_id="old", output="done"),
                    item("function_call", BEFORE, name="pending", call_id="pending"),
                    item("function_call_output", call_id="pending", output="done")])
        result = self.collect(max_pending_calls=1)
        self.assertEqual(result["coverage"]["pending_calls_evicted"], 0)
        self.assertEqual(self.events(result)[0]["call"]["name"], "pending")

    def test_chronology_pairs_fragments_before_pending_limit(self):
        self.write([meta(), item("function_call_output", "2026-09-12T00:00:02Z", call_id="one", output="done"),
                    item("function_call", "2026-09-12T00:00:03Z", call_id="two", name="two"),
                    item("function_call_output", "2026-09-12T00:00:04Z", call_id="two", output="done")], "a.jsonl")
        self.write([meta(), item("function_call", NOW, call_id="one", name="one")], "z.jsonl")
        result = self.collect(max_pending_calls=1)
        events = self.events(result)
        self.assertEqual([e["kind"] for e in events], ["tool_call", "tool_result", "tool_call", "tool_result"])
        self.assertEqual(result["coverage"]["pending_calls_evicted"], 0)
        self.assertEqual([e["call"]["name"] for e in events if e["kind"] == "tool_result"], ["one", "two"])

    def test_copied_records_keep_same_file_occurrences(self):
        records = [meta(), user("repeat"), user("repeat")]
        self.write(records)
        self.write(records, directory=self.archive)
        result = self.collect()
        self.assertEqual(len(self.events(result)), 2)
        self.assertEqual(result["coverage"]["duplicate_records"], 2)

    def test_mirrored_messages_pair_once_and_keep_repetitions(self):
        mirror = {"type": "event_msg", "timestamp": NOW,
                  "payload": {"type": "user_message", "message": "No, repeat"}}
        self.write([meta(), user("No, repeat"), mirror, user("No, repeat"), mirror])
        result = self.collect()
        events = self.events(result)
        self.assertEqual(len(events), 2)
        self.assertTrue(all(len(e["mirror_source_refs"]) == 1 for e in events))

    def test_distinct_turns_are_not_mirrors(self):
        first = user("repeat")
        first["payload"]["turn_id"] = "turn-one"
        second = {"type": "event_msg", "timestamp": NOW,
                  "payload": {"type": "user_message", "message": "repeat", "turn_id": "turn-two"}}
        self.write([meta(), first, second])
        self.assertEqual(len(self.events(self.collect())), 2)

    def test_mirror_does_not_hide_activity_across_checkpoint(self):
        self.write([meta(), user("same", "2026-09-11T00:00:00Z"),
                    {"type": "event_msg", "timestamp": "2026-09-11T00:00:00.100Z",
                     "payload": {"type": "user_message", "message": "same"}}])
        self.assertEqual(len(self.events(self.collect())), 1)

    def test_empty_text_messages_are_not_mirrors(self):
        self.write([meta(), item("message", role="user", content=[{"type": "input_image"}]),
                    {"type": "event_msg", "timestamp": NOW,
                     "payload": {"type": "user_message", "message": "", "images": ["synthetic"]}}])
        self.assertEqual(len(self.events(self.collect())), 2)

    def test_stop_does_not_probe_later_missing_root(self):
        self.write([meta(), user("one"), user("two")])
        result = scanner.collect([self.active, self.root / "missing"], max_events=1)
        self.assertIn("remaining_roots", result["truncation"])
        self.assertNotIn("root_missing_or_not_directory", [g["reason"] for g in result["source_gaps"]])

    def test_many_completed_calls_do_not_consume_pending_capacity(self):
        records = [meta()]
        for number in range(10):
            records.extend([item("function_call", call_id=str(number), name="test"),
                            item("function_call_output", call_id=str(number), output="done")])
        self.write(records)
        result = self.collect(max_pending_calls=1)
        self.assertEqual(result["coverage"]["pending_calls_evicted"], 0)
        self.assertEqual(len([e for e in self.events(result) if "call" in e]), 10)

    def test_recursion_failure_does_not_lose_other_records(self):
        self.write([meta(), user("bad")], "a.jsonl")
        self.write([meta(), user("good")], "b.jsonl")
        original = json.dumps
        def fail_one(value, **kwargs):
            if value.get("payload", {}).get("content", [{}])[0].get("text") == "bad":
                raise RecursionError("synthetic")
            return original(value, **kwargs)
        with patch.object(scanner.json, "dumps", side_effect=fail_one):
            result = self.collect()
        self.assertEqual(len(self.events(result)), 1)
        self.assertIn("record_decode_failed", [g["reason"] for g in result["source_gaps"]])


if __name__ == "__main__":
    import unittest
    unittest.main()
