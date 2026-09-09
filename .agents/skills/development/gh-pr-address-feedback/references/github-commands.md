# GitHub feedback commands

Inline replies use `in_reply_to` with a typed field (`-F`, not `-f`):

```bash
gh api -X POST repos/{owner}/{repo}/pulls/<pr>/comments \
  -F in_reply_to=<comment_id> \
  -F body='Addressed in <sha>: <summary>. Tests: <command>.'
```

Timeline replies: `gh pr comment <pr> -b '...'`. For findings that exist only in a review body with no replyable object, post a top-level comment with the same evidence plus the review URL — do not wait for an inline object to appear.

GitHub CLI 2.99.0 or later can attach repeatable image/video evidence to timeline comments. Feature-detect `--attach` on the exact command first. When placement matters, reference the local path in the Markdown body and pass the same path with `--attach`; otherwise add meaningful image alt text after `#`. Read the posted comment back to verify rendering. Inline review replies use the API and cannot attach media directly, so post one head-bound timeline evidence comment and link it from the inline reply instead of duplicating uploads.

```bash
gh pr comment <pr> --body-file /tmp/pr-visual-evidence.md \
  --attach './after.png#After the fix'
```

## gh CLI pitfalls

- 404 on `/pulls/comments/<id>/replies`: use `/pulls/<pr>/comments` with `in_reply_to`. 422 about `position`/`commit_id`: wrong endpoint, missing `in_reply_to`, or `-f` instead of `-F`.
- `gh pr checks` exit codes are status signals when a table prints — current versions may return `1` for failed and `8` for pending/failing. Classify the rows; repeated exit `8` with the same pending rows is not progress.
- Unsupported `--json` fields vary by `gh` version: trim the field list and retry with the smallest supported set.
- If `--attach` is absent, do not post raw local paths or silently omit requested visual proof; report that GitHub CLI 2.99.0 or later is required and use an authorized fallback.
- `Merge already in progress` / HTTP 405: stop issuing merge commands; switch to status polling and reporting.
