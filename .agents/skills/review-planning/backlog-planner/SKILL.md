---
name: backlog-planner
description: "Create or refine backlog items with clear scope and acceptance criteria using the gh CLI; use when planning work, writing tickets, or breaking down epics (trigger keywords: backlog, issue, ticket, epic, roadmap)."
---

# Backlog Planner

Turn ideas into issues an agent or human can implement without private chat history. Search for duplicates and in-flight PRs before creating; read the full issue, comments, labels, related PRs, and board status before changing an existing one. Before any write, resolve the repository and authenticated account with `gh repo view` and `gh auth status`, then inspect the repository's labels and project fields. Follow repository policy; use the taxonomy below only where those labels and status values already exist, and never create or rename taxonomy unless asked. Ask before bulk-creating issues unless the user explicitly requested filing them.

## Issue quality bar

- Body structure: Overview, Current State, Acceptance Criteria, Technical Context, Validation Plan.
- Concrete file paths, functions, endpoints, screens, commands, logs, or error text whenever known.
- Facts separated from hypotheses; suspected root causes never presented as confirmed.
- Dependencies and blockers modeled explicitly, with related issues and PRs linked.
- Validation plan matched to the changed surface: unit, integration, local server, simulator, or manual API checks.
- Scope fits a focused PR, or the planned slices are named. Split work that spans multiple components or has unclear sequencing.

## Default readiness labels — one active at a time

- `ai-needs-review`: body materially drafted or rewritten by AI; needs human review.
- `needs-grooming`: human-reviewed but still missing scope, acceptance criteria, blockers, or validation detail.
- `agent-ready`: human-reviewed and implementable. Verify the quality bar first; for bugs, attempt reproduction or name the missing repro detail before applying.
- `human-required`: cannot or should not be completed end-to-end by an agent (secret provisioning, account setup, production credential changes, legal/business decisions, manual external actions). Name the exact human action.
- `plan-me` / `!no-plan`: optional planning-automation trigger and opt-out only — never readiness states.

Labels classify and gate readiness; execution state lives on the project board. Closed issues drop readiness labels. Do not add legacy, duplicate, or execution-state labels unless repo policy defines them as current.

## Project board status

When the board defines these values, use `Backlog` → `Next` → `Ready` → `In progress` → `In review` → `Done`. New issues start in `Backlog`; near-term but blocked or not-yet-ready priorities go to `Next`; `agent-ready` work goes to `Ready`; actively owned work to `In progress`; open-PR work to `In review`. With different status names, map each semantic stage to the closest existing value. If no equivalent exists or board tooling is unavailable, report the intended transition instead of creating fields, statuses, or substitute labels.

## GitHub as live artifact

Issues and PRs are durable working memory: preserve decisions, scope changes, blockers, and validation evidence there, not only in chat. Convert new information into the right action — update body, add comment, create sub-issue, add dependency, or no-op — and keep artifacts synchronized with actual repo state.

## Sub-issues

Use for multi-component parallelizable epics, 3+ distinct deliverables or PRs, or efforts beyond ~1-2 days needing progress tracking. Skip for single change sets, small fixes, or repos without sub-issue support — use a checklist and issue links instead.

- `scripts/gh-sub-issues.sh list|add|remove <parent> [<child>...] [--repo OWNER/REPO] [--limit N]`
- Verify with `list` before reporting sub-issues attached.

## Blocking relationships

Always model as `TARGET issue is blocked by BLOCKER issue` (convert "A blocks B" to "B is blocked by A"). Use the issue dependency API endpoints directly — `gh issue view` does not expose dependency data. To add: look up the blocker's numeric REST `id`, read the target's `blocked_by` list, skip duplicates, add via the target's `blocked_by` endpoint, then re-read to verify. To remove: same lookup, delete form of the endpoint, re-read to verify.

## Triage sweeps

Group by action bucket: AI review needed, needs grooming, agent-ready, human-required, blocked/waiting, stale, uncategorized. Read prior comments and triage notes before changing state so resolved questions are not re-asked. Leave durable notes on under-specified issues: what is known, what remains unknown, and the specific question or artifact needed.
