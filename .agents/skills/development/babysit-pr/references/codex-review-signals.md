# Codex Review Completion Signals

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
  - a trusted structured summary satisfying the versioned contract below;
  - a `+1` from the approved Codex bot on the recorded authorized request ID from its trusted issuer naming that full SHA;
  - after recording the verified live head and its initial reaction IDs, the monitor observed new Codex `eyes` appear and later become `+1` while that head remained unchanged.

## Structured summary contract

A structured summary is independent head-bound code-review evidence; it does not require a captured `eyes` → `+1` transition or a manual request. Accept it only after reading the original comment from the live PR and verifying all of the following:

- GitHub author metadata identifies the approved Codex bot, not a display name, body attribution, quoted copy, or another account posting the same JSON. Resolve API-specific login spelling through verified bot identity; do not simply strip `[bot]` from arbitrary logins.
- The comment contains `<!-- codex-pull-request-review-summary -->` and one unambiguous `<!-- codex-review-state:v1 {...} -->` payload. Only this known version is supported. Malformed JSON, duplicate keys or state markers, unknown versions, missing fields, and conflicting summaries are unverified.
- In that JSON, `code_review.commit_sha` is the full live `headRefOid`, `code_review.status` is exactly `"completed"`, and both `code_review.has_any_findings` and `code_review.has_unresolved_findings` are JSON `false`. Missing values, `null`, strings such as `"false"`, and numeric substitutes do not pass. A short SHA or the rendered “Completed” heading is insufficient.
- The complete live review corpus has no unresolved actionable Codex findings or newer contradictory state. Check comment edits as well as new comments/reviews; do not select an older clean snapshot over a current pending or finding-bearing summary. All relevant `eyes` locks must still be absent. Re-fetch the head after collecting evidence; restart if it changed.

Synthetic example of the supported payload (the SHA is illustrative):

```html
<!-- codex-pull-request-review-summary -->
<!-- codex-review-state:v1 {"code_review":{"commit_sha":"0123456789abcdef0123456789abcdef01234567","has_any_findings":false,"has_unresolved_findings":false,"status":"completed"},"security_review":{"commit_sha":null,"has_any_findings":null,"has_unresolved_findings":null,"status":null}} -->
```

This establishes only the Codex code-review signal. The `security_review` fields above are null: security review is unverified, not passed. Preserve independent security, reviewer, check, acceptance, and action-authorization gates. Record the live comment ID/link, verified author, payload version, full SHA, and observation time in the checkpoint; a copied transcript or previous checkpoint cannot establish current readiness.

### Review scenarios

These synthetic cases exercise the contract; they are not runtime test results.

| Evidence | Expected decision |
| --- | --- |
| Trusted live v1 summary, exact full head, completed and both flags false; no locks, findings, or contradictions; initial reactions were not captured | Accept the Codex code-review signal without requesting another review. Evaluate all other readiness gates separately. |
| Same clean summary with null security fields; a security review is required | Code-review signal passes; security remains unverified and readiness stays blocked. |
| Copied payload, untrusted author, or unresolved bot identity | Unverified; the marker and JSON cannot establish authorship. |
| Short/stale SHA, head changes during collection, unknown version, duplicate payload/key, malformed or missing field, string/number/null in place of false, or status other than completed | Unverified; do not infer success or fall back to the rendered heading. |
| Otherwise valid summary with an active relevant eyes reaction, an unresolved actionable finding, or newer contradictory review/edited summary | Keep readiness blocked; the summary does not override live locks or feedback. |

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
