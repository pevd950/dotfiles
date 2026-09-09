---
name: gh-pr-address-feedback
description: Validate and fix specific PR review findings or CI failures, then reply with authorized evidence. Use babysit-pr for sustained monitoring.
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
- For a standalone feedback request, use bounded polling and report remaining pending checks with URLs. When invoked by `babysit-pr`, return pending state to that workflow; its monitoring and heartbeat policy owns continuation. Break waits into intervals supported by the current runtime.
- External providers: inspect available authorized diagnostics at the details URL; report missing access or evidence. Keep repairs within the requested PR scope.
- `no checks reported on the '<branch>' branch` right after a push is usually transient — retry after a short delay.

## Reply with evidence

- `Addressed in <sha>: <what changed>. Tests: <command>.`
- `Not changing: <reason>. Evidence: <code/spec pointer>.`
- `Follow-up: <issue link> (out of scope for this PR).`
- For UI, rendering, motion, focus, timing, or intermittent-behavior findings, attach the smallest screenshot or video that materially proves the result. State the exact head SHA, tested scenario, build, platform, device, and OS that produced it; media never substitutes for the textual conclusion and validation commands.

For reply endpoints, attachment commands, and CLI recovery, read [GitHub commands](references/github-commands.md) before posting.

## PR description

Update the body only when it has become inaccurate (scope, behavior, testing section, risks, or durable visual proof changed). Preserve meaningful scope changes, tradeoffs, follow-up decisions, and validation updates in the PR body or a comment rather than only in chat. Safe edit preserving auto-generated sections: `gh pr view <pr> --json body -q .body > /tmp/pr-body.md`, edit, `gh pr edit <pr> --body-file /tmp/pr-body.md`; add `--attach <path>` only for media referenced by that updated body.

## Output expectations

Every addressed comment gets a reply (fix, decision, or follow-up) with evidence; fixes are regression-safe with tests where appropriate; CI status is summarized when checks were part of the task; the PR description changes only when it was actually out of date.
