---
name: "gh-fix-ci"
description: "Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions. Prefer this custom skill when you need deeper local log inspection or Xcode/xcresult artifact recovery. Use the GitHub app for PR metadata when available, and use `gh` for Actions check and log inspection before implementing any approved fix."
---

# GitHub Actions CI Fix

Use the GitHub app/connector for PR metadata and patch context when available; use `gh` for Actions checks and logs — the connector does not cover that workflow end to end. Summarize the root cause first, propose a focused fix plan, and implement only after explicit approval.

## Helper script

`scripts/inspect_pr_checks.py` handles `gh` field drift, job-log fallbacks, and Xcode `xcresult` artifact recovery when Actions logs are incomplete:

```bash
PYTHON_BIN=${PYTHON_BIN:-python3}; command -v "$PYTHON_BIN" >/dev/null || PYTHON_BIN=python
"$PYTHON_BIN" "<path-to-skill>/scripts/inspect_pr_checks.py" --repo "." --pr "<number-or-url>" [--json] [--max-lines 200 --context 40]
```

- Exit code `1` means "failing checks were found", not a crash. Treat the payload as evidence; suspect the helper only when output is malformed or a traceback points at the script or runtime.
- Give it a generous first wait — log and artifact fetches take several seconds, and empty intermediate output while it runs is normal.
- The `xcresult` path is best-effort enrichment: it needs `xcrun` locally and usable uploaded artifacts.

## Manual fallback

`gh pr checks <pr> --json name,state,bucket,link,startedAt,completedAt,workflow` — if a field is rejected, retry with the fields the installed `gh` supports. For each failing check, extract the run id from `detailsUrl`/`link`, then `gh run view <run_id> --log`; if the run log says it is still in progress, fetch job logs via `gh api /repos/<owner>/<repo>/actions/jobs/<job_id>/logs`.

## Scope and reporting

- Non-GitHub-Actions checks (Buildkite and other providers): label as external and report only the URL.
- Report the failing check name, run URL, and a concise log snippet; call out missing logs rather than over-claiming certainty. Surface recovered `xcresult` summaries as the best available evidence.
- If the failure is clearly unrelated to the local diff, say so before proposing code changes.
- After an approved fix: run the most relevant local verification, suggest re-running the tests and `gh pr checks`, and report what remains unverified, possibly flaky, or external and not actionable here.
