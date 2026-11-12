---
name: backlog-planner
description: Create or refine issues, tickets, and epics with clear scope and acceptance criteria. Use for backlog planning and work breakdown.
---

# Backlog Planner

Turn ideas into issues an agent or human can implement without private chat history. Search for duplicates and in-flight PRs before creating; read the full issue, comments, labels, related PRs, and board status before changing an existing one. Once per session, resolve the repository and authenticated account with `gh repo view` and `gh auth status` and inspect the repository's labels and project fields. Follow repository policy; use the taxonomy below only where those labels and status values already exist, and create or rename taxonomy only when asked. Ask before bulk-creating issues unless the user explicitly requested filing them.

## Issue quality bar

- Body structure: Overview, Current State, Acceptance Criteria, Technical Context, Validation Plan.
- Concrete file paths, functions, endpoints, screens, commands, logs, or error text whenever known.
- Facts separated from hypotheses; a suspected root cause is labeled as suspected.
- Dependencies and blockers modeled explicitly, with related issues and PRs linked.
- Validation plan matched to the changed surface: unit, integration, local server, simulator, or manual API checks.
- For visual or interaction bugs, attach the smallest decisive screenshot or video when available and authorized, with the version or build, platform, device/OS, and reproduction state, alongside the textual reproduction. Follow the [media workflow](../../development/babysit-pr/references/github-media-evidence.md) for upload and render checks.
- Scope fits a focused PR, or the planned slices are named. Split work that spans multiple components or has unclear sequencing.

## Default readiness labels — one active at a time

- `ai-needs-review`: body materially drafted or rewritten by AI; needs human review.
- `needs-grooming`: human-reviewed but still missing scope, acceptance criteria, blockers, or validation detail.
- `agent-ready`: human-reviewed and implementable. Verify the quality bar first; for bugs, attempt reproduction or name the missing repro detail before applying.
- `human-required`: cannot or should not be completed end-to-end by an agent (secret provisioning, account setup, production credential changes, legal/business decisions, manual external actions). Name the exact human action and create the personal task for it, as the global instructions describe.
- `plan-me` / `!no-plan`: optional planning-automation trigger and opt-out only — never readiness states.

Labels classify and gate readiness; execution state lives on the project board. Closed issues drop readiness labels. Add only labels that repo policy defines as current.

## Project board status

When the board defines these values, use `Backlog` → `Next` → `Ready` → `In progress` → `In review` → `Done`. New issues start in `Backlog`; near-term but blocked or not-yet-ready priorities go to `Next`; `agent-ready` work goes to `Ready`; actively owned work to `In progress`; open-PR work to `In review`. With different status names, map each semantic stage to the closest existing value. If no equivalent exists or board tooling is unavailable, report the intended transition instead of creating fields, statuses, or substitute labels.

## GitHub as live artifact

Issues and PRs are durable working memory: preserve decisions, scope changes, blockers, and validation evidence there, not only in chat. Convert new information into the right action — update body, add comment, create sub-issue, add dependency, or no-op — and keep artifacts synchronized with actual repo state. The Craft workboard row or plan links the Issue and tracks progress without restating it.

## Sub-issues and blocking

Use sub-issues for multi-component parallelizable epics, 3+ distinct deliverables or PRs, or efforts beyond ~1-2 days needing progress tracking. For single change sets, small fixes, or repos without sub-issue support, use a checklist and issue links.

Model a dependency as `TARGET is blocked by BLOCKER` (convert "A blocks B" to "B is blocked by A"). `gh` handles both natively; confirm the flags with `--help` on the installed version:

- Create: `gh issue create --parent <number> --blocked-by <numbers> --blocking <numbers>`.
- Edit: `gh issue edit <number>` with `--parent`, `--add-sub-issue`, `--add-blocked-by` or `--add-blocking`; each has a `--remove-` counterpart.
- Verify before reporting: `gh issue view <number> --json subIssues,blockedBy,blocking`.

## Triage sweeps

Group by action bucket: AI review needed, needs grooming, agent-ready, human-required, blocked/waiting, stale, uncategorized. Read prior comments and triage notes before changing state so resolved questions are not re-asked. Leave durable notes on under-specified issues: what is known, what remains unknown, and the specific question or artifact needed.
