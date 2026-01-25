---
name: gh-pr-address-feedback
description: Triage and address GitHub PR review feedback using the gh CLI. Use when asked to respond to PR comments, validate reviewer claims (don’t fix blindly), make safe fixes without regressions, and reply with evidence (commit SHA + tests). Update the PR description only when it becomes inaccurate.
---

# GH PR Address Feedback

## Overview
Fetch PR feedback, evaluate whether each comment is correct and worth acting on, apply minimal safe fixes, and respond to comments with clear evidence. Avoid regressions by preserving prior behavior and running targeted tests.

## Workflow

### 1) Confirm repo + PR context
- `gh auth status`
- `gh repo view --json nameWithOwner -q .nameWithOwner`
- `gh pr view <pr> --json headRefName,baseRefName,title,body -q .title`

Optional snapshots (useful if you might update the PR description later):
- `gh pr view <pr> --json body -q .body > /tmp/pr-body.before.md`
- `gh pr view <pr> --json commits -q '.commits[].messageHeadline' > /tmp/pr-commits.before.txt`

### 2) Fetch all feedback
There are two comment streams you usually need:

- Line review comments (inline on diffs):
  - `gh api repos/{owner}/{repo}/pulls/<pr>/comments --paginate --jq '.[] | {id, path, line, body, user: .user.login}'`
- Issue-style PR comments (timeline):
  - `gh api repos/{owner}/{repo}/issues/<pr>/comments --paginate --jq '.[] | {id, body, user: .user.login}'`

Optional context:
- Reviews (high-level approvals/requests):
  - `gh api repos/{owner}/{repo}/pulls/<pr>/reviews --paginate --jq '.[] | {id, user: .user.login, state, body}'`

### 3) Triage and validate (don’t fix blindly)
For each comment, classify it as one of:
- Fix now: correctness bug, regression risk, security issue, test gap, broken UX, or clearly a repo convention.
- Ask: intent is unclear or requires product decision.
- Disagree: comment is incorrect/harmful or would regress an earlier fix.
- Follow-up: valid improvement but not needed for this PR (open/point to an issue).

Validation checklist (pick the smallest that proves it):
- Locate the code path (search + read around it) and verify the claim.
- If it changes behavior, identify what could regress (especially earlier fixes in the PR).
- Run a targeted test (or add one) when the change affects correctness.

### 4) Implement fixes safely
- Prefer the smallest diff that resolves the validated concern.
- Avoid refactors unless required to fix the issue.
- Add/update tests when a regression is plausible.
- Run targeted tests (or the smallest confidence-building suite).
- Commit with a clear message (don’t amend unless asked).
- Push the branch.

### 5) Update the PR description only when needed
Only update the PR body when it’s now inaccurate (scope/behavior changed, testing section out of date, notable risks changed).

Safe editing pattern (preserves auto-generated sections):
- `gh pr view <pr> --json body -q .body > /tmp/pr-body.md`
- Edit `/tmp/pr-body.md`
- `gh pr edit <pr> --body-file /tmp/pr-body.md`

### 6) Respond to comments with evidence
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

## Common Pitfalls
- 404 when calling `/pulls/comments/<id>/replies`: use `/pulls/<pr>/comments` with `in_reply_to`.
- 422 about missing `position`/`commit_id`: you used the wrong endpoint or didn’t pass `in_reply_to` (or used `-f` instead of `-F`).
- PR body churn: don’t update the description unless it’s actually out of date.

## Output Expectations
- Every addressed comment has a reply (fix/decision/follow-up) with evidence.
- Fixes are regression-safe (tests run where appropriate).
- PR description is updated only when it becomes inaccurate.
