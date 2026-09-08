# Check classification

Inspect live branch protection, effective rulesets (including inherited rules), current PR checks, and trusted project/user requirements. A successful empty rules response is different from a permission or network failure. No rules does not mean no validation is needed.

Classify by check context, expected provider, revision and applicable policy:

| Class | Treatment |
| --- | --- |
| Required | GitHub-enforced or explicitly required by trusted policy. Missing/pending is a blocker. A similarly named check from another provider is not a substitute. |
| Evidence | Additional validation. Investigate failures; pending alone is not a requirement. Missing acceptance evidence remains a policy blocker. |
| Duplicate/superseded | Ignore only after proving redundancy or obsolescence; keep the source and rationale. A required context cannot be demoted because another job did similar work. |

Resolve reruns and GitHub's effective revision before making a snapshot: head SHA versus current test-merge SHA, event, attempt, check context and provider must match. Never reuse old-head success. A fresh head invalidates old evidence even when commit timestamps look newer. Do not blanket-ignore optional failures or accept a skipped required job without verifying why it was skipped and whether policy permits it.

## Decision helper contract

`check_gate_state.py` reads JSON on stdin and prints a decision. It performs no network access, writes, notifications or merges. The caller supplies live, trusted classification and records the returned checkpoint once per scheduled observation. It is not a GitHub collector or a substitute for the skill's review, worktree and acceptance audit.

Input fields:

- `head_sha`, `state` (`OPEN`, `MERGED`, `CLOSED`), `now` (Unix seconds), `rules_verified` (boolean).
- `checks`: each has stable `id`, `classification` (`required`, `evidence`, `duplicate`), effective `head_sha`, `status`, optional `attempt`, `jobs`, `queued_since`, `skip_allowed`, and `reason`. A duplicate requires a recorded reason. Include missing required contexts with status `missing`; never omit them.
- `previous`: last returned `checkpoint`, or null. Include repository/base/rules policy changes in `policy_id`; this resets stale block history.

Statuses are normalized to `success`, `neutral`, `skipped`, `failure`, `cancelled`, `queued`, `in_progress`, or `missing`. Only verified, policy-allowed skips/neutral conclusions pass. Additional failed/cancelled/unknown checks require investigation. `diagnose` lists 15-minute zero-job queue anomalies; `notify` marks a first 30-minute/two-unchanged-observation escalation. The caller actually sends the notification and only then records `last_notified_at` (or records failure and retries). `checks_satisfied` is **not merge-ready**.

Dry-run fixtures cover the incident shape: passed required validation plus an optional duplicate stuck queued; the same queue as a required check; stale-head success; optional failure; rules lookup failure; unexpected skip; head/policy changes; notification deduplication; and terminal PRs. Do not require installation of this helper or a canonical workflow in every repository.
