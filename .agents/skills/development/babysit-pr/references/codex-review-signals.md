# Codex Review Reaction Signals

GitHub exposes PR-body reactions through the issue reactions API because every pull request is also an issue:

```bash
gh api 'repos/{owner}/{repo}/issues/<pr>/reactions' --paginate \
  --jq '.[] | {id, user: .user.login, content, created_at}'
```

Automatic Codex review does not require an `@codex review` comment. Monitor the PR body and review submissions first. If any existing relevant request comment is present, including a legacy request, record its ID and verify its trusted issuer before using it as head-bound completion evidence; inspect its reactions too. Do not create or renew a request comment merely to obtain a reaction target:

```bash
gh api repos/{owner}/{repo}/issues/comments/<comment-id>/reactions --paginate \
  --jq '.[] | {id, user: .user.login, content, created_at}'
```

## In-progress lock

An `eyes` reaction from `chatgpt-codex-connector[bot]` (or another user-approved Codex bot account) on either the PR body or an existing relevant `@codex review` request comment blocks readiness while present. A request comment is optional; its absence does not authorize a manual review.

## Completion requires all of

- Every relevant Codex `eyes` reaction is gone from the PR body and any existing relevant review request comment.
- No newer actionable Codex inline comments, top-level comments, review-body findings, or unresolved Codex review threads.
- The no-issues evidence is bound to the live `headRefOid`, via one of:
  - a positive Codex review whose `commit_id` is that head;
  - a `+1` from the approved Codex bot on the recorded authorized request ID from its trusted issuer naming that full SHA;
  - after recording the verified live head and its initial reaction IDs, the monitor observed new Codex `eyes` appear and later become `+1` while that head remained unchanged.

## Anti-spoofing rules

- Never compare reaction time with commit authored or committed time; those timestamps are forgeable.
- A PR-body `+1` is advisory unless its preceding `eyes` first appeared after the verified live head and its initial reaction IDs were recorded. Absence from a pre-mutation baseline alone cannot bind a reaction to the new head.
- Never reuse reaction evidence after a push; newer actionable feedback overrides prior no-issues signals.
- If no head-bound signal exists, report Codex status as unverified.

## Before marking ready, pushing to a ready PR, or an authorized manual request

Capture existing PR-body and relevant request-comment reaction IDs with the current `headRefOid` before the mutation; keep them as historical context in the checkpoint. After the mutation, promptly verify the live head and record its initial reactions. A reaction appearing between these snapshots may belong to either head; it requires independently head-bound review evidence. These observations never authorize a manual trigger.

## After the mutation or when resuming monitoring

1. Verify and record the live `headRefOid` and its initial reaction IDs. Treat reactions already present at this first post-mutation snapshot as unbound unless independent review evidence identifies the new head. Never bind a reaction merely because it was absent before the mutation. Record any existing relevant request comment ID, including legacy requests, and its trusted issuer; a legacy request does not authorize another request.
2. For a ready PR under routine babysitting, wait for automatic review without posting a review command after a push. For an explicitly authorized draft or stacked-PR fix-and-rereview cycle, preserve that authorization: if the old request names a previous head, verify the live head and that no review is already running or complete for it, then issue one fresh request naming the full SHA and record its trusted issuer. Honor one-shot limits. Poll PR-body reactions, reviews with their `commit_id`, and any existing relevant request comment's reactions, re-fetching `headRefOid` each time.
3. Keep monitoring until Codex removes `eyes` and either posts actionable feedback or leaves a head-bound no-issues signal. Restart if the head changes. If review is unavailable or stalled, report that evidence under the babysitter's blocker policy; do not manually retrigger it without user authorization under the trigger policy.
