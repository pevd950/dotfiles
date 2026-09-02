# Heartbeat Automation for PR Monitoring

Create or update a Codex heartbeat automation when checks or reviews will take longer than the current turn. Prefer updating an existing monitor for the same PR over creating a duplicate.

Heartbeat state is only a wakeup mechanism. Each heartbeat run must re-verify the target repo, PR number, branch, and latest head SHA from live GitHub before acting — never trust saved prompt text, previous thread summaries, sidebar/app status, or prior payloads as current PR state.

At the start of every heartbeat:

1. Re-run the Babysit PR loop's snapshot and corpus gathering (or the GitHub connector equivalent if `gh` is unavailable).
2. Compare the live PR URL, number, branch, and head SHA against the heartbeat prompt.
3. If the prompt points at the wrong PR/thread, `target_thread_id` is invalid, or the PR cannot be verified live, stop and report the mismatch instead of editing, replying, or marking ready.
4. Treat Codex app/sidebar heartbeat updates as best-effort UI state only; they do not replace live GitHub checks, comments, threads, reactions, or local branch status.
5. After every push or external review change, refresh the heartbeat prompt with the latest head SHA and known state; stale payloads must not drive readiness decisions.

Use `codex_app.automation_update` when available:

- `kind`: `heartbeat`; `destination`: `thread` for the current thread — but never assume this succeeded.
- Schedule: usually every 10-15 minutes while review bots and CI are expected to post.
- Prompt contents: repo and PR number; branch name and latest pushed SHA; current known checks/reviews state; exact readiness criteria; fix only PR-scoped bot/actionable CI issues; do not merge unless the user explicitly asked; do not reply to human reviewers without approval; local validation already run.

## Verify the saved record before ending the turn

```bash
AUTOMATION_DIR="${CODEX_HOME:-$HOME/.codex}/automations/<automation-id>"
sed -n '1,120p' "$AUTOMATION_DIR/automation.toml"
```

The heartbeat is correctly attached only if `target_thread_id` is a real thread id — not the literal string `"thread"` — and the prompt/name match the monitored PR. Otherwise tell the user the automation target needs manual correction in the app; do not claim the PR is being monitored by automation until this verification passes.

If a paused heartbeat was requested, verify `status` too: some creates ignore a requested paused status. If the saved record is active when it should be paused, immediately pause/update it or delete the test automation.

Network, GitHub, or laptop-sleep interruptions are transient — retry on the next heartbeat rather than marking the PR blocked.
