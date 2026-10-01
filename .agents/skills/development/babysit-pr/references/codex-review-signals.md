# Codex Review Reaction Signals

GitHub exposes PR-body reactions through the issue reactions API because every pull request is also an issue:

```bash
gh api 'repos/{owner}/{repo}/issues/<pr>/reactions' --paginate \
  --jq '.[] | {id, user: .user.login, content, created_at}'
```

Automatic Codex review does not require an `@codex review` comment. Monitor the PR body and review submissions first. If an existing relevant request comment is present from a user-authorized exception, record its ID and inspect its reactions too. Do not create or renew a request comment merely to obtain a reaction target:

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
  - after recording the live head, the monitor observed new Codex `eyes` appear and later become `+1` while that head remained unchanged.

## Anti-spoofing rules

- Never compare reaction time with commit authored or committed time; those timestamps are forgeable.
- A PR-body `+1` is advisory unless its `eyes` first appeared after the live head was recorded.
- Never reuse reaction evidence after a push; newer actionable feedback overrides prior no-issues signals.
- If no head-bound signal exists, report Codex status as unverified.

## After marking ready or pushing commits

1. Record the live `headRefOid` and current reaction IDs. Record a relevant request comment ID only if one already exists from a user-authorized exception.
2. Wait for automatic review. Poll PR-body reactions, reviews with their `commit_id`, and any existing relevant request comment's reactions, re-fetching `headRefOid` each time. Do not post a review command after a push.
3. Keep monitoring until Codex removes `eyes` and either posts actionable feedback or leaves a head-bound no-issues signal. Restart if the head changes. If review is unavailable or stalled, report that evidence under the babysitter's blocker policy; do not manually retrigger it without user authorization under the trigger policy.
