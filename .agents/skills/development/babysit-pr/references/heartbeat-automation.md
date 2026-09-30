# Heartbeat Automation for PR Monitoring

Create or update a Codex heartbeat automation when checks or reviews will take longer than the current turn. Prefer updating an existing monitor for the same PR over creating a duplicate.

Heartbeat state is only a wakeup mechanism. Each heartbeat run must re-verify the target repo, PR number, branch, and latest head SHA from live GitHub before acting — never trust saved prompt text, previous thread summaries, sidebar/app status, or prior payloads as current PR state.

At the start of every heartbeat:

1. Fetch the live PR snapshot first (or the GitHub connector equivalent if `gh` is unavailable). If the verified PR is merged/closed, follow completion cleanup below and end the run before gathering reviews/checks or making further GitHub changes. Otherwise continue the Babysit PR loop's live rules/check classification and corpus gathering. Saved run IDs are historical evidence only.
2. Compare the live PR URL, number, branch, and head SHA against the heartbeat prompt.
3. If the prompt points at the wrong PR/thread, `target_thread_id` is invalid, or the PR cannot be verified live, stop and report the mismatch instead of editing, replying, or marking ready.
4. Treat Codex app/sidebar heartbeat updates as best-effort UI state only; they do not replace live GitHub checks, comments, threads, reactions, or local branch status.
5. After every push or external review change, refresh the heartbeat prompt with the latest head SHA and known state; stale payloads must not drive readiness decisions.

Use `codex_app.automation_update` when available:

- `kind`: `heartbeat`; `destination`: `thread` for the current thread — but never assume this succeeded.
- Schedule: usually every 10-15 minutes while review bots and CI are expected to post.
- Save the returned automation ID in the monitor checkpoint and add it to the heartbeat prompt after creation. When reusing a monitor, verify its saved ID, kind, PR and target thread before updating it.
- Prompt contents: this monitor's automation ID and target thread; repo and PR number; branch name and latest pushed SHA; current known checks/reviews state; exact readiness criteria; the user's granted scope (read-only monitoring versus authorized fixes/commits/pushes/bot replies/resolutions); do not merge unless the user explicitly asked; do not reply to human reviewers without approval; local validation already run; delete this heartbeat when the verified PR is merged/closed or the requested monitoring is complete, and pause only for a resumable wait. A heartbeat preserves authority, not stale gates.

## Completion cleanup

Delete the heartbeat when live GitHub confirms the target PR is merged/closed, the user says stop, or the readiness bar is met and the user's requested monitoring ends there. If the user explicitly wants continued monitoring through merge, keep it until merge/closure or a later stop request. Cleanup of this monitor is part of the babysitting request, including watch-only monitoring.

1. Resolve this monitor's saved automation ID from the checkpoint or trusted scheduler context. If missing, inspect `${CODEX_HOME:-$HOME/.codex}/automations/*/automation.toml` for an unambiguous matching heartbeat. Verify `kind`, target thread and repo/PR against the known monitor identity; a matching name alone is insufficient. If identity is ambiguous, report the cleanup blocker without deleting anything.
2. Use `codex_app.automation_update` with `mode: "delete"` and that verified `id`. Delete only this monitor; do not sweep other PR monitors, cron jobs or unrelated thread automations. If it is already absent, cleanup is complete.
3. Verify deletion through the tool result and absence of the saved automation record before claiming cleanup succeeded. If deletion fails or cannot be confirmed, re-read the record and pause that verified heartbeat with `mode: "update"`, preserving its other fields. Verify `status: "PAUSED"` and report that deletion remains incomplete. If neither deletion nor pause can be verified, report the monitor may still be active. Use the app tool rather than removing scheduler files manually.
4. Retain a concise thread/checkpoint handoff: final PR state and head SHA, stop reason, automation ID and verified cleanup outcome. Completing monitoring does not authorize merging the PR or completing a separate task tracker.

Pause rather than delete when the user explicitly says pause, or a human-review decision or escalated external blocker needs intervention and monitoring should resume. Record the intervention and resume condition. Transient network/auth failures or an unverified PR state do not prove completion and must not trigger deletion.

## Queue diagnosis and durable escalation

Record `head_sha`, `blocking_gate`, `blocked_since`, `state_fingerprint`, `unchanged_polls`, and `last_notified_at` in the monitor checkpoint. Gate identity includes repository, base branch, check context/provider and policy source, not just a run ID. Fingerprint meaningful state (head, rules, blocker, status, attempt, job assignment), excluding poll timestamps and elapsed time. Reset the block window on a new head, changed gate/rules, or meaningful progress. Preserve notification history while the same condition persists.

- A run queued with `jobs=[]` for 15 minutes is a dispatch anomaly: inspect its jobs/attempt, concurrency, approval/environment waits, runner assignment and provider health where accessible. The decision helper accepts job arrays or integer counts and normalizes both to a count; missing/null is unknown, not zero. It is not proof that a runner is offline. Diagnose optional duplicates too, but do not promote them into merge gates.
- Notify after 30 minutes or two unchanged **scheduled** observations of the same blocking condition (not two API calls in one iteration). Send through `$notify-user` only (`~/.agents/skills/productivity/notify-user/scripts/send_notification.py --check` then `--send`) with title/subtitle/body covering the check/reviewer, elapsed time, evidence URL as plain text, what is known, and next action. Do not call ActionBuddy, Poke, or Buddy MCP from this heartbeat. Notify once per unchanged condition; update again on meaningful change, recovery, or an explicit reminder schedule.
- Continue ordinary running checks and transient recovery. Use completion cleanup when monitoring ends; pause for resumable human decisions or escalated non-transient external blockers. Record the intervention and resume condition. Never cancel/rerun unrelated runs or change branch rules to make a gate pass.
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
