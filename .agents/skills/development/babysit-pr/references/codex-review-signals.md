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
  - the monitor observed new Codex `eyes` absent from the pre-mutation baseline, bound them to the verified post-mutation head, and later observed `+1` while that head remained unchanged; or recorded the live head before observing new `eyes` appear and later become `+1` on that unchanged head.

## Anti-spoofing rules

- Never compare reaction time with commit authored or committed time; those timestamps are forgeable.
- A PR-body `+1` is advisory unless its preceding `eyes` was absent from the pre-mutation baseline and bound to the verified post-mutation head, or first appeared after the live head was recorded.
- Never reuse reaction evidence after a push; newer actionable feedback overrides prior no-issues signals.
- If no head-bound signal exists, report Codex status as unverified.

## Before marking ready, pushing to a ready PR, or an authorized manual request

Capture the existing PR-body reaction IDs and reactions on any existing relevant request comments before the mutation, together with the current `headRefOid`. For a new PR, record the intended head and an empty PR-reaction baseline before creation. Keep this baseline in the monitor checkpoint. It lets the monitor identify a new automatic review even if `eyes` appears before the first post-mutation poll. These observations never authorize a manual trigger.

## After the mutation or when resuming monitoring

1. Verify and record the live `headRefOid` and current reaction IDs. Compare them with the pre-mutation baseline and bind newly appearing Codex `eyes` IDs to that verified head; do not carry an existing old-head reaction forward as new review evidence. If the baseline is missing, retain the observed signals but require independently head-bound completion evidence instead of claiming the review is verified. Record any existing relevant request comment ID, including legacy requests, and its trusted issuer; a legacy request does not authorize another request.
2. For a ready PR, wait for automatic review; for an authorized manual pass, monitor the existing request. Poll PR-body reactions, reviews with their `commit_id`, and any existing relevant request comment's reactions, re-fetching `headRefOid` each time. Do not post a review command after a push.
3. Keep monitoring until Codex removes `eyes` and either posts actionable feedback or leaves a head-bound no-issues signal. Restart if the head changes. If review is unavailable or stalled, report that evidence under the babysitter's blocker policy; do not manually retrigger it without user authorization under the trigger policy.
