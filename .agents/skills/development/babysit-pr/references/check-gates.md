# Check classification

Once per head, read branch protection, effective rulesets (inherited ones included), the PR's current checks, and any validation the project or user requires. An empty rules response is different from a permission or network failure: report the latter as unverified.

| Class | Treatment |
| --- | --- |
| Required | Enforced by GitHub or explicitly required by trusted policy. Missing or pending blocks. A similarly named check from another provider is not a substitute. |
| Evidence | Additional validation. Investigate failures; pending alone does not block. |
| Duplicate/superseded | Ignore once redundancy or obsolescence is shown, and note the reason. A required context stays required even when another job did similar work. |

Match each result to the current head: head SHA (or GitHub's test-merge SHA), event, attempt, check context and provider. Success on an older head does not carry over. A skipped required job passes only when policy allows the skip.

## Decision helper (optional)

`scripts/check_gate_state.py` turns an already classified snapshot into a decision. It reads JSON on stdin and has no network access or side effects. Its `checks_satisfied` covers checks only, not reviews or the rest of the readiness bar.

Input:

- `head_sha`, `state` (`OPEN`, `MERGED`, `CLOSED`), `now` (Unix seconds), `rules_verified` (boolean).
- `checks`: each with `id`, `classification` (`required`, `evidence`, `duplicate`), `head_sha`, `status`, and optional `attempt`, `jobs`, `queued_since`, `skip_allowed`, `reason`. A duplicate needs a `reason`. List a missing required context with status `missing`.
- `previous`: the last returned `checkpoint`, or null. Put repository, base and rules changes in `policy_id` so stale block history resets.

`jobs` is a count, an API job array, or null for unknown. Statuses normalize to `success`, `neutral`, `skipped`, `failure`, `cancelled`, `queued`, `in_progress`, or `missing`.

Output: `diagnose` lists runs queued with zero jobs for 15 minutes; `notify` marks the first 30-minute or two-unchanged-observation escalation. Record `last_notified_at` only after the notification is sent. A malformed saved checkpoint raises an error: recover the saved one rather than starting fresh.

Tests: `python3 -m unittest discover -s scripts -p 'test_*.py'` from the skill directory.
