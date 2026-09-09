import unittest

from check_gate_state import assess


def check(kind="required", status="success", **extra):
    return dict(id="ci/provider", classification=kind, status=status, head_sha="head", **extra)


def snapshot(checks, now=0, previous=None, **extra):
    return dict(head_sha="head", state="OPEN", rules_verified=True,
                checks=checks, now=now, previous=previous, **extra)


class CheckGateStateTests(unittest.TestCase):
    def test_job_arrays_and_counts_share_anomaly_and_checkpoint_semantics(self):
        first = assess(snapshot([check(status="queued", jobs=[], queued_since=0)], now=900))
        self.assertEqual(first["diagnose"], ["ci/provider"])
        second = assess(snapshot([check(status="queued", jobs=0, queued_since=0)],
                                 now=1200, previous=first["checkpoint"]))
        self.assertEqual(second["checkpoint"]["unchanged_polls"], 1)

    def test_matching_malformed_checkpoint_fails_with_actionable_error(self):
        checks = [check(status="queued")]
        previous = assess(snapshot(checks))["checkpoint"]
        for field in ("blocked_since", "unchanged_polls", "last_notified_at"):
            malformed = dict(previous)
            del malformed[field]
            with self.assertRaisesRegex(ValueError, "checkpoint"):
                assess(snapshot(checks, previous=malformed))

    def test_stale_additional_evidence_cannot_satisfy_current_head(self):
        stale = dict(check("evidence"), head_sha="old")
        self.assertEqual(assess(snapshot([stale]))["decision"], "blocked")
        self.assertEqual(assess(snapshot([check("evidence", "queued")]))["decision"],
                         "checks_satisfied")

    def test_optional_duplicate_does_not_block_but_is_diagnosed(self):
        duplicate = check("duplicate", "queued", jobs=0, queued_since=0,
                          reason="Same revision and validation already succeeded")
        duplicate["id"] = "duplicate-run"
        result = assess(snapshot([check(), duplicate], now=900))
        self.assertEqual(result["decision"], "checks_satisfied")
        self.assertEqual(result["diagnose"], ["duplicate-run"])
        self.assertFalse(result["notify"])

    def test_required_duplicate_validation_cannot_replace_required_context(self):
        checks = [check(status="queued", jobs=0, queued_since=0),
                  dict(check("evidence"), id="equivalent")]
        first = assess(snapshot(checks))
        second = assess(snapshot(checks, 900, first["checkpoint"]))
        third = assess(snapshot(checks, 1800, second["checkpoint"]))
        self.assertEqual(third["decision"], "blocked")
        self.assertEqual(second["diagnose"], ["ci/provider"])
        self.assertTrue(third["notify"])

    def test_two_unchanged_scheduled_polls_escalate_before_thirty_minutes(self):
        checks = [check(status="queued", jobs=0)]
        first = assess(snapshot(checks))
        second = assess(snapshot(checks, 600, first["checkpoint"]))
        third = assess(snapshot(checks, 1200, second["checkpoint"]))
        self.assertFalse(second["notify"])
        self.assertTrue(third["notify"])

    def test_thirty_minutes_escalates_even_without_two_intermediate_polls(self):
        checks = [check(status="queued")]
        first = assess(snapshot(checks))
        self.assertTrue(assess(snapshot(checks, 1800, first["checkpoint"]))["notify"])

    def test_first_observation_of_old_queue_escalates_immediately(self):
        result = assess(snapshot([check(status="queued", jobs=0, queued_since=0)], now=3600))
        self.assertTrue(result["notify"])
        self.assertEqual(result["checkpoint"]["blocked_since"], 0)

    def test_notification_deduplication_and_failed_send_retry(self):
        checks = [check(status="queued")]
        first = assess(snapshot(checks))
        due = assess(snapshot(checks, 1800, first["checkpoint"]))
        self.assertIsNone(due["checkpoint"]["last_notified_at"])
        self.assertTrue(assess(snapshot(checks, 2400, due["checkpoint"]))["notify"])
        due["checkpoint"]["last_notified_at"] = 1800
        self.assertFalse(assess(snapshot(checks, 3000, due["checkpoint"]))["notify"])

    def test_stale_success_is_not_evidence_for_a_required_gate(self):
        stale = dict(check(), head_sha="old")
        self.assertEqual(assess(snapshot([stale]))["decision"], "blocked")

    def test_optional_failure_still_requires_investigation(self):
        self.assertEqual(assess(snapshot([check("evidence", "failure")]))["decision"], "blocked")

    def test_rules_errors_are_not_empty_rules(self):
        value = snapshot([])
        value["rules_verified"] = False
        self.assertEqual(assess(value)["decision"], "blocked")
        self.assertEqual(assess(snapshot([]))["decision"], "checks_satisfied")

    def test_required_skip_requires_explicit_policy(self):
        self.assertEqual(assess(snapshot([check(status="skipped")]))["decision"], "blocked")
        self.assertEqual(assess(snapshot([check(status="skipped", skip_allowed=True)]))["decision"],
                         "checks_satisfied")

    def test_head_policy_and_job_progress_reset_block_history(self):
        checks = [check(status="queued", jobs=0)]
        first = assess(snapshot(checks))
        for changes in ({"head_sha": "new"}, {"policy_id": "new-rules"},
                        {"checks": [check(status="in_progress", jobs=1)]}):
            value = snapshot(checks, 3600, first["checkpoint"])
            value.update(changes)
            with self.subTest(changes=changes):
                result = assess(value)
                self.assertFalse(result["notify"])
                self.assertEqual(result["checkpoint"]["blocked_since"], 3600)

    def test_terminal_pr_clears_checkpoint(self):
        for state in ("MERGED", "CLOSED"):
            value = snapshot([check(status="queued")])
            value["state"] = state
            result = assess(value)
            self.assertEqual(result["decision"], "stop")
            self.assertIsNone(result["checkpoint"])

    def test_duplicate_requires_reason(self):
        with self.assertRaises(ValueError):
            assess(snapshot([check("duplicate", "queued")]))

    def test_unknown_classification_fails_closed(self):
        with self.assertRaises(ValueError):
            assess(snapshot([check("optional-ish")]))


if __name__ == "__main__":
    unittest.main()
