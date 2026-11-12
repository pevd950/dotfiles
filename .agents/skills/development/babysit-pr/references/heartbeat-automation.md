# Codex heartbeat automation

On Codex, the wakeup for a PR monitor is a heartbeat automation. Other hosts use their own mechanism; the rules in `SKILL.md` apply either way. Update an existing monitor for the same PR rather than creating a second one.

## Create or update

Use `codex_app.automation_update`:

- `kind`: `heartbeat`; `destination`: `thread` for the current thread.
- Schedule: every 10-15 minutes while review bots and CI are expected to post.
- Prompt contents: the automation ID (add it after creation) and target thread; repo, PR number, branch and latest pushed SHA; known check and review state; the user's granted scope (watch-only, fixes and bot replies, merge when ready); validation already run. Refresh the SHA and state after every push.

Then verify the saved record before ending the turn:

```bash
AUTOMATION_DIR="${CODEX_HOME:-$HOME/.codex}/automations/<automation-id>"
sed -n '1,120p' "$AUTOMATION_DIR/automation.toml"
```

`target_thread_id` must be a real thread id, not the literal string `"thread"`, and the name and prompt must match the PR. If they do not, tell the user the target needs correcting in the app, and report the PR as unmonitored until it is fixed. Some creates ignore a requested paused status, so check `status` too.

## Each heartbeat

The saved prompt is a wakeup, not PR state. Fetch the live PR first and compare its URL, number, branch and head SHA with the prompt. If they disagree, `target_thread_id` is invalid, or the PR cannot be verified, stop and report the mismatch. If the PR is merged or closed, clean up and end the run. Otherwise run the normal loop.

Network, GitHub or laptop-sleep interruptions are transient: retry on the next heartbeat. Heartbeat status in the Codex app or sidebar is best-effort UI state.

## Escalating a stuck check

Keep in the heartbeat prompt: `head_sha`, the blocking check (repository, base branch, context, provider), `blocked_since`, `unchanged_polls` and `last_notified_at`. Reset them on a new head, changed rules or real progress. Count scheduled observations, not repeated API calls within one run.

Notify once per unchanged condition, with the check or reviewer, elapsed time, evidence URL as plain text, what is known and the next action; notify again only on a meaningful change or recovery. A queued workflow may have no job yet, so a job's `timeout-minutes` does not bound the wait. `scripts/check_gate_state.py` can compute these decisions; see `check-gates.md`.

## Cleanup

Delete the heartbeat when live GitHub confirms the PR is merged or closed, the user says stop, or the requested monitoring is complete. Pause it instead when the user says pause, or a human decision or external blocker will be followed by more monitoring; record the resume condition. A transient network or auth failure is not completion.

1. Find the automation ID in the prompt or scheduler context. Failing that, look for the one matching heartbeat in `${CODEX_HOME:-$HOME/.codex}/automations/*/automation.toml` and confirm `kind`, target thread and repo/PR; a matching name is not enough. If the match is ambiguous, report that and delete nothing.
2. Call `codex_app.automation_update` with `mode: "delete"` and that `id`. Delete only this monitor, through the app tool rather than by removing scheduler files.
3. Confirm the record is gone. If deletion fails, pause it with `mode: "update"`, confirm `status: "PAUSED"`, and report that deletion is incomplete.
4. Leave a short handoff in the thread: final PR state and head SHA, stop reason, automation ID and cleanup result.
