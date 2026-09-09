# Heartbeat Automation for PR Monitoring

Create or update a Codex heartbeat automation when checks or reviews will take longer than the current turn. Prefer updating an existing monitor for the same PR over creating a duplicate.

Heartbeat state is only a wakeup mechanism. Each heartbeat run must re-verify the target repo, PR number, branch, and latest head SHA from live GitHub before acting — never trust saved prompt text, previous thread summaries, sidebar/app status, or prior payloads as current PR state.

At the start of every heartbeat:

1. Re-run the Babysit PR loop's snapshot, live rules/check classification, and corpus gathering (or the GitHub connector equivalent if `gh` is unavailable). Saved run IDs are historical evidence only.
2. Compare the live PR URL, number, branch, and head SHA against the heartbeat prompt.
3. If the prompt points at the wrong PR/thread, `target_thread_id` is invalid, or the PR cannot be verified live, stop and report the mismatch instead of editing, replying, or marking ready.
4. Treat Codex app/sidebar heartbeat updates as best-effort UI state only; they do not replace live GitHub checks, comments, threads, reactions, or local branch status.
5. After every push or external review change, refresh the heartbeat prompt with the latest head SHA and known state; stale payloads must not drive readiness decisions.

Use `codex_app.automation_update` when available:

- `kind`: `heartbeat`; `destination`: `thread` for the current thread — but never assume this succeeded.
- Schedule: usually every 10-15 minutes while review bots and CI are expected to post.
- Prompt contents: repo and PR number; branch name and latest pushed SHA; current known checks/reviews state; exact readiness criteria; the user's granted scope (read-only monitoring versus authorized fixes/commits/pushes/bot replies/resolutions); do not merge unless the user explicitly asked; do not reply to human reviewers without approval; local validation already run. A heartbeat preserves authority, not stale gates.

## Queue diagnosis and durable escalation

Record `head_sha`, `blocking_gate`, `blocked_since`, `state_fingerprint`, `unchanged_polls`, and `last_notified_at` in the monitor checkpoint. Gate identity includes repository, base branch, check context/provider and policy source, not just a run ID. Fingerprint meaningful state (head, rules, blocker, status, attempt, job assignment), excluding poll timestamps and elapsed time. Reset the block window on a new head, changed gate/rules, or meaningful progress. Preserve notification history while the same condition persists.

- A run queued with `jobs=[]` for 15 minutes is a dispatch anomaly: inspect its jobs/attempt, concurrency, approval/environment waits, runner assignment and provider health where accessible. The decision helper accepts job arrays or integer counts and normalizes both to a count; missing/null is unknown, not zero. It is not proof that a runner is offline. Diagnose optional duplicates too, but do not promote them into merge gates.
- Notify after 30 minutes or two unchanged **scheduled** observations of the same blocking condition (not two API calls in one iteration). Include the check/reviewer, elapsed time, evidence URL, what is known, and next action. Notify once per unchanged condition; update again on meaningful change, recovery, or an explicit reminder schedule.
- Continue ordinary running checks and transient recovery. Pause only when merged/closed, ready for the user's decision, or after an escalated non-transient external blocker needs intervention. Record the intervention and resume condition. Never cancel/rerun unrelated runs or change branch rules to make a gate pass.
- A queued workflow may have no job yet, so job `timeout-minutes` is not a substitute for this monitor deadline.

`scripts/check_gate_state.py` is a network-free decision helper for already classified, trusted snapshots; it cannot certify overall PR readiness or authorize mutations. Run its regression suite with `python3 -m unittest discover -s scripts -p 'test_*.py'` from this skill directory. See `check-gates.md` for inputs and the human audit that remains necessary.

## Verify the saved record before ending the turn

```bash
AUTOMATION_DIR="${CODEX_HOME:-$HOME/.codex}/automations/<automation-id>"
sed -n '1,120p' "$AUTOMATION_DIR/automation.toml"
```

The heartbeat is correctly attached only if `target_thread_id` is a real thread id — not the literal string `"thread"` — and the prompt/name match the monitored PR. Otherwise tell the user the automation target needs manual correction in the app; do not claim the PR is being monitored by automation until this verification passes.

If a paused heartbeat was requested, verify `status` too: some creates ignore a requested paused status. If the saved record is active when it should be paused, immediately pause/update it or delete the test automation.

Network, GitHub, or laptop-sleep interruptions are transient — retry on the next heartbeat rather than marking the PR blocked.
