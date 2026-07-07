---
name: backlog-planner
description: "Create or refine backlog items with clear scope and acceptance criteria using the gh CLI; use when planning work, writing tickets, or breaking down epics (trigger keywords: backlog, issue, ticket, epic, roadmap)."
---

# Backlog Planner

## What this skill does
- Turns ideas into actionable backlog items with clear scope and criteria.
- Uses the gh CLI to create/update issues with labels and milestones.
- Decomposes large efforts into smaller, sequenced tasks using sub-issues when supported.
- Optimizes issues for handoff to human reviewers and coding agents by making context, dependencies, and validation expectations explicit.

## When to use it
- Trigger phrases: "backlog", "issue", "ticket", "epic", "roadmap".
- Use when planning work or creating issues for others to implement.

## Step-by-step workflow
1) Confirm repo context with `gh repo view --json nameWithOwner -q .nameWithOwner` and verify `gh auth status`.
2) Check for duplicates with `gh issue list --search "keywords" --state all --limit 20`; also search related PRs when implementation may already exist or be in flight.
3) List labels with `gh label list --limit 200` and map to type, component, priority, and workflow labels that match the repo policy.
4) Read the full issue, comments, current labels, related PRs, and project-board status before changing an existing issue.
5) List milestones with `gh api repos/{owner}/{repo}/milestones --jq '.[].title'` and select if relevant.
6) Draft or update the issue body with clear Overview, Current State, Acceptance Criteria, Technical Context, and Validation Plan.
7) Create or update the issue with `gh issue create` / `gh issue edit` using `--label` and `--milestone`.
8) If the work is an epic, decide on sub-issues and manage them with `scripts/gh-sub-issues.sh` when supported.

## Issue quality bar
- Every issue should be self-contained enough that an agent can start work without private chat history.
- Include concrete file paths, functions, endpoints, screens, commands, logs, or error text when they are known.
- Separate facts from hypotheses. Do not present suspected root causes as confirmed without evidence.
- Include dependencies and blockers explicitly, including related issues or PRs.
- Include a validation plan that matches the changed surface, such as unit tests, integration tests, local server checks, simulator validation, or manual API calls.
- Keep scope realistic. Split work that spans multiple components, has unclear sequencing, or is larger than a focused PR.

## GitHub as live artifact
- Treat issues and PRs as durable working memory when they are the active artifact.
- Preserve decisions, scope changes, blockers, validation expectations, and important evidence in the issue or PR instead of leaving them only in chat.
- Convert new information into the right artifact action: update issue body, add issue comment, update PR body, add PR comment, create sub-issue, add dependency, or no-op.
- Ask before bulk-creating many issues unless the user explicitly requested filing them.
- Keep GitHub artifacts synchronized with actual repo state and validation evidence.

## Label workflow
- Use labels for issue classification and readiness, not execution state.
- Prefer one active readiness label at a time: `ai-needs-review`, `needs-grooming`, or `agent-ready`.
- Use `ai-needs-review` when an issue body was materially drafted or rewritten by AI and still needs human review.
- Use `needs-grooming` after human review when the issue still needs scope, acceptance criteria, blockers, or validation detail before implementation.
- Use `agent-ready` after human review when the issue is ready for an implementation agent.
- Use `human-required` when the issue cannot or should not be completed end-to-end by an agent, such as secret provisioning, account setup, production credential changes, legal/business decisions, or manual external-system actions. Include the exact human action required.
- Use `plan-me` only as an optional planning automation trigger. Do not treat it as a readiness state.
- Use `!no-plan` only as an optional planning automation opt-out.
- Do not add legacy, duplicate, or execution-state labels unless the repo explicitly defines them as current policy.
- Closed issues should not keep readiness labels.

## Project status workflow
- Prefer project-board fields for execution status when a repo uses a board with a `Status` field.
- A common status flow is: `Backlog` -> `Next` -> `Ready` -> `In progress` -> `In review` -> `Done`.
- New issues usually start in `Backlog`.
- Move near-term but blocked or not-yet-ready issues to `Next` when the user or project policy indicates they are a priority.
- Move planned implementation work to `Ready` when the issue has `agent-ready`.
- Move actively owned work to `In progress` by updating the project status, not by adding substitute labels.
- Move issues with an open PR under review to `In review`.
- Move merged or completed work to `Done`.
- If project-board status tooling is unavailable, report the intended status change instead of inventing substitute labels.

## Triage workflow
- For a triage overview, group issues by useful action buckets: AI review needed, needs grooming, agent-ready, human-required, blocked/waiting, stale, and uncategorized.
- Before changing state, read prior comments and triage notes so resolved questions are not re-asked.
- For bug issues, attempt reproduction or identify the missing reproduction detail before marking them `agent-ready`.
- When an issue is under-specified, leave durable triage notes that capture what is known, what remains unknown, and the specific question or artifact needed.

## Agent-ready checklist
Before applying `agent-ready`, verify:
- Scope fits a focused PR or explicitly names the planned slices.
- Acceptance criteria are specific and testable.
- Known files, endpoints, screens, commands, logs, or error text are included when available.
- Facts and hypotheses are separated.
- Dependencies and blockers are modeled explicitly.
- Validation plan is specific to the changed surface.
- Related issues and PRs were checked.
- Human decisions are resolved, marked out of scope, or represented with `human-required`.

## Sub-issues: when and how
Use sub-issues when:
- The work spans multiple components or teams and can be parallelized.
- The epic requires 3+ distinct deliverables or 3+ PRs.
- The effort is larger than ~1-2 days and needs progress tracking.

Avoid sub-issues when:
- The task is a single change set or under ~4 hours.
- The work is a simple bug fix or small docs update.
- Sub-issues are not enabled for the repo; use a checklist instead.

Workflow:
1) Create the parent epic issue with a clear scope and target milestone.
2) Identify existing related issues; only create new sub-issues when needed.
3) Use `scripts/gh-sub-issues.sh add <parent> <child...>` to attach sub-issues.
4) Verify the relationship with `scripts/gh-sub-issues.sh list <parent>` before reporting that sub-issues were added.
5) If sub-issues are not supported, add a task checklist in the epic and link related issues.

## Scripts
- `scripts/gh-sub-issues.sh list <parent> [--repo OWNER/REPO] [--limit N]`
- `scripts/gh-sub-issues.sh add <parent> <child...> [--repo OWNER/REPO]`
- `scripts/gh-sub-issues.sh remove <parent> <child...> [--repo OWNER/REPO]`
- If the script reports that sub-issues are not available, use a checklist and issue links instead.

## Blocking relationships
For GitHub issue dependencies, always model the relationship as:

`TARGET issue is blocked by BLOCKER issue.`

If the request is phrased as "A blocks B", convert it to:

`B is blocked by A.`

How to set a blocker:
1) Look up the blocking issue's numeric REST `id` from the issue payload.
2) Read the target issue's existing `blocked_by` list using the issue dependency API endpoint.
3) If the blocker is already present, do not add a duplicate.
4) Add the blocking issue as a blocker on the target issue using the target issue's `blocked_by` dependency endpoint.
5) Verify by reading the target issue's `blocked_by` list again after the change.

How to remove a blocker:
1) Look up the same blocking issue numeric REST `id`.
2) Use the delete form of the target issue's `blocked_by` dependency endpoint.
3) Verify by reading the target issue's `blocked_by` list after the change.

Do not rely on `gh issue view` for dependency data. Use the issue dependency API endpoints directly.

## Expected outputs / formatting
- Issue template with Overview, Current State, Acceptance Criteria, Technical Context.
- Selected labels and milestone (if available).
- Sub-issue plan or checklist with clear titles and ordering.
- Duplicate/related-work search summary, including any relevant existing issues or PRs.
- Validation plan and dependency/blocker notes when relevant.

## Example prompts
- "Draft a backlog issue for adding export support."
- "Break this epic into smaller, sequenced tasks."
- "Create a ticket with clear acceptance criteria for this feature."
- "Use gh to create an issue with labels and a milestone."
