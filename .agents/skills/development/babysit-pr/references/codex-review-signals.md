# Codex Review Reaction Signals

GitHub exposes PR-body reactions through the issue reactions API because every pull request is also an issue:

```bash
gh api 'repos/{owner}/{repo}/issues/<pr>/reactions' --paginate \
  --jq '.[] | {id, user: .user.login, content, created_at}'
```

Codex also commonly reacts to the latest `@codex review` issue comment rather than the PR body. Track that comment's ID after each push and inspect its reactions the same way:

```bash
gh api repos/{owner}/{repo}/issues/comments/<comment-id>/reactions --paginate \
  --jq '.[] | {id, user: .user.login, content, created_at}'
```

## In-progress lock

An `eyes` reaction from `chatgpt-codex-connector[bot]` (or another user-approved Codex bot account) on either the PR body or the latest relevant `@codex review` request comment blocks readiness while present.

## Completion requires all of

- Every relevant Codex `eyes` reaction is gone from the PR body and the latest review request comment.
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

## After every push or fresh `@codex review` request

1. Record the live `headRefOid`, current reaction IDs, and the latest `@codex review` request comment ID.
2. Poll PR-body reactions, that request's reactions, and reviews with their `commit_id`, re-fetching `headRefOid` each time.
3. Keep monitoring until Codex removes `eyes` and either posts actionable feedback or leaves a head-bound no-issues signal. Restart if the head changes.
