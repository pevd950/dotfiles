---
name: gh-pr-address-feedback
description: Triage and address GitHub PR review feedback and GitHub Actions CI failures using the gh CLI. Use when asked to respond to PR comments, validate reviewer claims (don’t fix blindly), inspect failing checks, make safe fixes without regressions, and reply with evidence (commit SHA + tests). Update the PR description only when it becomes inaccurate.
---

# GH PR Address Feedback

## Overview
Fetch PR feedback and check status, evaluate whether each comment or failure is correct and worth acting on, apply minimal safe fixes, and respond with clear evidence. Avoid regressions by preserving prior behavior and running targeted tests.

## Workflow

### 1) Confirm auth, connectivity, and PR context
- If the `gh-connectivity-preflight` skill is available in the current session, use it before a gh-heavy sweep.
- `gh auth status`
- If auth fails or tokens are invalid, ask the user to re-auth with `gh auth login -h github.com` or fix `GITHUB_TOKEN` / `GH_TOKEN`.
- `GITHUB_TOKEN` and `GH_TOKEN` override keychain auth. If they are invalid, unset them before assuming the keychain login is broken.
- If the API is unreachable, ask the user to confirm network or proxy access, or provide the repo and PR directly.
- `gh repo view --json nameWithOwner -q .nameWithOwner`
- `gh pr view <pr> --json headRefName,baseRefName,title,body -q .title`

Optional snapshots (useful if you might update the PR description later):
- `gh pr view <pr> --json body -q .body > /tmp/pr-body.before.md`
- `gh pr view <pr> --json commits -q '.commits[].messageHeadline' > /tmp/pr-commits.before.txt`

### 2) Gather review feedback and check status
There are three review feedback sources you should treat as required:

- Line review comments (inline on diffs):
  - `gh api repos/{owner}/{repo}/pulls/<pr>/comments --paginate --jq '.[] | {id, path, line, body, user: .user.login}'`
- Issue-style PR comments (timeline):
  - `gh api repos/{owner}/{repo}/issues/<pr>/comments --paginate --jq '.[] | {id, body, user: .user.login}'`
- Reviews (high-level approvals/requests):
  - `gh api repos/{owner}/{repo}/pulls/<pr>/reviews --paginate --jq '.[] | {id, user: .user.login, state, body}'`
- Check status:
  - `gh pr checks <pr>`
  - Treat exit code `8` from `gh pr checks` as a status signal that checks are pending or failing, not as a broken command by itself. Read the table before deciding whether follow-up is needed.
  - When polling, prefer one `gh pr checks <pr> --watch=false` call per interval instead of embedding long sleep/retry ladders into one shell payload.
  - Prefer `gh pr checks <pr> --json name,state,conclusion,detailsUrl` when available.
  - If `conclusion` or `detailsUrl` are not supported by the installed `gh`, fall back to `--json name,state,link,bucket,workflow,startedAt,completedAt`.
  - If `gh pr view --json ...` rejects a field, remove the unsupported field and retry with the smallest supported set instead of assuming the CLI schema matches a newer version.
  - If `gh pr checks <pr>` reports `no checks reported on the '<branch>' branch` immediately after a push, treat it as transient remote state first and retry after a short delay before deeper debugging.

Important:
- Do not treat `pulls/<pr>/reviews` as optional context. Some bot reviewers, especially `chatgpt-codex-connector[bot]`, may surface actionable findings only in the review body and not as replyable inline `pulls/comments` objects.
- Always inspect new review bodies from bot reviewers for code-linked findings, even when `pulls/<pr>/comments` shows no new items.

Optional extra coverage:
- Review threads (useful when the UI shows a comment that is missing from the simpler REST views):
  - `gh api graphql -f query='query { repository(owner:"<owner>", name:"<repo>") { pullRequest(number:<pr>) { reviewThreads(first:100) { nodes { isResolved comments(first:20) { nodes { databaseId author { login } body path line createdAt } } } } } } }'`

### 3) Triage and validate (don’t fix blindly)
For each comment or failing check, classify it as one of:
- Fix now: correctness bug, regression risk, security issue, test gap, broken UX, or clearly a repo convention.
- Ask: intent is unclear or requires product decision.
- Disagree: comment is incorrect/harmful or would regress an earlier fix.
- Follow-up: valid improvement but not needed for this PR (open/point to an issue).

Validation checklist (pick the smallest that proves it):
- Locate the code path (search + read around it) and verify the claim.
- If it changes behavior, identify what could regress (especially earlier fixes in the PR).
- Run a targeted test (or add one) when the change affects correctness.
- Mark stale comments and out-of-scope failures explicitly instead of silently fixing around them.

### 4) Implement fixes safely
- Prefer the smallest diff that resolves the validated concern.
- Avoid refactors unless required to fix the issue.
- Add/update tests when a regression is plausible.
- Run targeted tests (or the smallest confidence-building suite).
- Recheck `gh pr checks <pr>` when CI status was part of the task and the result might have changed.
- Commit with a clear message (don’t amend unless asked).
- Push the branch.

### 5) Triage CI failures (GitHub Actions only)
- Use `gh pr checks <pr>` to identify failing checks before assuming a reviewer comment is the main blocker.
- For GitHub Actions runs, extract the run id from `detailsUrl` (or `link`) and fetch logs:
  - `gh run view <run-id> --log`
  - If logs are still pending, retry or fetch job logs via `gh api /repos/{owner}/{repo}/actions/jobs/{job_id}/logs`
- When `gh pr checks <pr>` only shows pending entries, switch to polling/reporting mode instead of treating the command exit as actionable failure.
- Use bounded polling. A practical default is one immediate check, then short waits such as 30s, 60s, and 120s. After that, report the remaining pending checks and their URLs instead of looping indefinitely in the same turn.
- If only self-hosted or external checks remain pending and there is no new failure signal, stop polling and summarize the waiting state.
- For external checks such as Buildkite, report the details URL and treat deeper debugging as out of scope for this skill.
- If merge endpoints report `Merge already in progress` or HTTP `405`, stop issuing merge commands and switch to status polling plus user-visible reporting.

### 6) Update the PR description only when needed
Only update the PR body when it’s now inaccurate (scope/behavior changed, testing section out of date, notable risks changed).
- Treat the PR as a live artifact while review work is active. Preserve meaningful scope changes, tradeoffs, follow-up decisions, validation updates, and new risks in the PR body or a PR comment instead of leaving them only in chat.
- If review uncovers follow-up work outside the PR scope, open or point to an issue and link it in the PR response.

Safe editing pattern (preserves auto-generated sections):
- `gh pr view <pr> --json body -q .body > /tmp/pr-body.md`
- Edit `/tmp/pr-body.md`
- `gh pr edit <pr> --body-file /tmp/pr-body.md`

### 7) Respond to comments with evidence
Use a short reply referencing:
- what changed
- commit SHA
- tests run (or why not)

Examples:
- `Addressed in <sha>: <what changed>. Tests: <command>.`
- `Not changing: <reason>. Evidence: <code/spec pointer>.`
- `Follow-up: <issue link> (out of scope for this PR).`

#### Reply to line review comments
Use `in_reply_to` with a typed field (note: use `-F`, not `-f`):

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<pr>/comments \
  -F in_reply_to=<comment_id> \
  -F body='Addressed in <sha>: <short summary>. Tests: <command>.'
```

#### Reply to issue-style PR comments
- `gh pr comment <pr> -b 'Addressed in <sha>: <summary>.'`
- Or: `gh api -X POST repos/{owner}/{repo}/issues/<pr>/comments -F body='...'`

#### Reply when a finding exists only in a review summary
- If a bot finding appears in `pulls/<pr>/reviews` (or the GitHub UI) but GitHub does not expose a replyable inline comment object, do not wait indefinitely for it to appear in `pulls/<pr>/comments`.
- Post a top-level PR comment with the same evidence you would have used in a thread reply:
  - what changed (or why no change was needed)
  - commit SHA or explicit “already addressed in <sha>”
  - tests run
  - a direct reference to the review URL when available

## When to push back
- The request conflicts with the PR goal or repo patterns.
- The feedback is stale or contradicted by current code or tests.
- The suggested fix would require a large refactor without clear benefit.

## Common Pitfalls
- 404 when calling `/pulls/comments/<id>/replies`: use `/pulls/<pr>/comments` with `in_reply_to`.
- 422 about missing `position`/`commit_id`: you used the wrong endpoint or didn’t pass `in_reply_to` (or used `-f` instead of `-F`).
- PR body churn: don’t update the description unless it’s actually out of date.
- Unsupported JSON fields vary by `gh` version. Trim the field list and retry instead of treating the CLI error as a repo problem.
- `Merge already in progress` is not a signal to keep retrying merge commands. Treat it as remote state and poll.
- Repeated exit `8` from `gh pr checks` with the same pending rows is not forward progress. Stop after bounded polling and report the remaining blockers.

## Output Expectations
- Every addressed comment has a reply (fix/decision/follow-up) with evidence.
- Fixes are regression-safe (tests run where appropriate).
- CI status is summarized when checks were part of the task.
- PR description is updated only when it becomes inaccurate.
