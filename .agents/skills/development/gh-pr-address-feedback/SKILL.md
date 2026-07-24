---
name: gh-pr-address-feedback
description: Triage and address GitHub PR review feedback and GitHub Actions CI failures using the gh CLI. Use when asked to respond to PR comments, validate reviewer claims (don't fix blindly), inspect failing checks, make safe fixes without regressions, and reply with evidence (commit SHA + tests). Update the PR description only when it becomes inaccurate.
---

# GH PR Address Feedback

Evaluate each comment or failure before acting, apply minimal safe fixes, and respond with evidence. Run `gh-connectivity-preflight` first when auth or transport looks broken — remember `GH_TOKEN`/`GITHUB_TOKEN` override keychain auth, so unset invalid env tokens before assuming the login is broken.

## Gather the full review corpus

Treat all three review sources as required — bots such as `chatgpt-codex-connector[bot]` may surface actionable findings only in review bodies that never appear as replyable inline comments:

- Inline diff comments: `gh api repos/{owner}/{repo}/pulls/<pr>/comments --paginate`
- Timeline comments: `gh api repos/{owner}/{repo}/issues/<pr>/comments --paginate`
- Reviews: `gh api repos/{owner}/{repo}/pulls/<pr>/reviews --paginate`
- Checks: `gh pr checks <pr>`; add the review-threads GraphQL query when the UI shows a comment missing from REST views.

## Triage — don't fix blindly

Classify each item: **Fix now** (correctness, regression risk, security, test gap, broken UX, clear repo convention) / **Ask** (unclear intent or product decision) / **Disagree** (incorrect, harmful, or would regress an earlier fix) / **Follow-up** (valid but out of scope — open or point to an issue). Verify the claim at the code path, run the smallest proving test, and mark stale or out-of-scope items explicitly instead of silently fixing around them.

Push back when feedback conflicts with the PR goal or repo patterns, is contradicted by current code or tests, or demands a large refactor without clear benefit.

## Fix

Smallest diff that resolves the validated concern; add or update tests when regression is plausible; run targeted tests; commit clearly (no amend unless asked) and push.

## CI failures (GitHub Actions)

- Check `gh pr checks <pr>` before assuming a reviewer comment is the main blocker. Extract the run id from `detailsUrl`/`link`, then `gh run view <run-id> --log`; still-pending logs via `gh api /repos/{owner}/{repo}/actions/jobs/{job_id}/logs`.
- Bounded polling: one immediate check, then waits around 30s/60s/120s; after that, report remaining pending checks with URLs instead of looping. If only self-hosted or external checks remain pending with no new failure signal, stop polling and summarize.
- External providers such as Buildkite: report the details URL; deeper debugging is out of scope here.
- `no checks reported on the '<branch>' branch` right after a push is usually transient — retry after a short delay.

## Reply with evidence

- `Addressed in <sha>: <what changed>. Tests: <command>.`
- `Not changing: <reason>. Evidence: <code/spec pointer>.`
- `Follow-up: <issue link> (out of scope for this PR).`

Inline replies use `in_reply_to` with a typed field (`-F`, not `-f`):

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<pr>/comments \
  -F in_reply_to=<comment_id> \
  -F body='Addressed in <sha>: <summary>. Tests: <command>.'
```

Timeline replies: `gh pr comment <pr> -b '...'`. For findings that exist only in a review body with no replyable object, post a top-level comment with the same evidence plus the review URL — do not wait for an inline object to appear.

## PR description

Update the body only when it has become inaccurate (scope, behavior, testing section, or risks changed). Preserve meaningful scope changes, tradeoffs, follow-up decisions, and validation updates in the PR body or a comment rather than only in chat. Safe edit preserving auto-generated sections: `gh pr view <pr> --json body -q .body > /tmp/pr-body.md`, edit, `gh pr edit <pr> --body-file /tmp/pr-body.md`.

## gh CLI pitfalls

- 404 on `/pulls/comments/<id>/replies`: use `/pulls/<pr>/comments` with `in_reply_to`. 422 about `position`/`commit_id`: wrong endpoint, missing `in_reply_to`, or `-f` instead of `-F`.
- `gh pr checks` exit codes are status signals when a table prints — current versions may return `1` for failed and `8` for pending/failing. Classify the rows; repeated exit `8` with the same pending rows is not progress.
- Unsupported `--json` fields vary by `gh` version: trim the field list and retry with the smallest supported set.
- `Merge already in progress` / HTTP 405: stop issuing merge commands; switch to status polling and reporting.

## Output expectations

Every addressed comment gets a reply (fix, decision, or follow-up) with evidence; fixes are regression-safe with tests where appropriate; CI status is summarized when checks were part of the task; the PR description changes only when it was actually out of date.
