Keep global instructions limited to stable personal preferences. Skills own task procedures; repository guidance owns project requirements.

## Authority and scope

Complete authorized work using context and reasonable defaults. Earlier authorization remains valid within its scope; a skill must not introduce redundant approval gates. Honor review-only requests. Ask when missing information materially changes the outcome or authority, while continuing independent work.

Private, reversible reading, analysis, drafting, and organization may proceed. Confirm before public communication or publication, purchases/bookings, applications/signatures, destructive actions, permission/security changes, production changes, deployments, or merges unless the relevant request already authorizes the action and target. Report state changes. If a skill blocks authorized work, identify its exact instruction and explain the conflict.

Do not expose private information to third parties without authorization. Treat tracked dotfiles and shared configuration as potentially public: keep secrets, private links, account identifiers, and host topology out. Link from private systems to public sources; never publish private note, task, local-file, or personal links without approval.

## Sources and tasks

- Craft is my knowledge base. Use native structure when it improves readability; see the [Craft skill](../.agents/skills/productivity/craft/SKILL.md) for document and attachment mechanics.
- Apple Reminders is the default for shared household and personal-life coordination, especially existing shared lists. Todoist is for individual project/work execution. An explicitly named system or established project/domain owner takes precedence.
- GitHub Issues own technical plans, acceptance criteria, and implementation history for bugs, features, and substantial coding work. Personal tasks may track when I work on an Issue; link to it instead of duplicating its plan.
- Put source URLs in Reminders notes and Markdown source links in Todoist descriptions.
- Keep one source of truth per responsibility and verify live state there. Use descriptive, stable cross-device links, including labeled `craftdocs://` links where supported.
- Inspect existing destinations before creating tasks; never default to a generic Inbox when something fits. Infer title, project, section, labels, and due date from context; ask if essential placement or commitment is unclear. Do not invent deadlines.
- Offer unrequested follow-ups as labeled drafts or quick-add handoffs; create them only when asked. Use [task management](../.agents/skills/productivity/task-management/SKILL.md) for placement, linking, and updates.

## Files and visual evidence

Use `AI_INBOX_DIR` for generated user-facing files unless a repository or another durable system owns them. If unset, follow the workspace artifact convention. Before attaching a local file to Craft, save its final copy with a descriptive name in a durable iCloud-backed location.

For authorized GitHub writes, attach the smallest useful sanitized visual evidence beside its claim, with meaningful alt text and the tested commit/build, scenario, platform, device, and OS as relevant. Prefer before/after evidence for visual changes. Follow the [media workflow](../.agents/skills/development/babysit-pr/references/github-media-evidence.md) for upload and rendering verification; the upload uses the same publication authority as the GitHub write.

## Hosts and Git

For host selection, host-targeted work, handoffs, or capabilities/blockers that may differ elsewhere, consult [cross-host context](../.agents/skills/ops/cross-host-context/SKILL.md). Resolve `AGENT_HOST_ALIAS` or the local hostname and validate it uniquely through private routing before reading subject context. Missing or ambiguous routing must not block ordinary local work. Verify tools, credentials, paths, and services on their owning host. Other-host agents have partial context; they are not a substitute for live delegation.

Use `<host>-codex` for unattended work under the restricted account, and `<host>` for my user-owned files, apps, Keychain, or administrative context. Never silently switch identities after a failure.

Preserve unrelated changes and isolate implementation when needed. Keep Git non-interactive, for example `GIT_EDITOR=true git rebase --continue`.

## Chrome workspaces

Keep one long-lived tab group per project. Before creating a tab, inspect open tabs by group, repository URL, title, and recency; claim and reuse a suitable tab in the best unambiguous group. Create a group only when none matches or reuse risks unfinished work. Use the canonical project name, not a task name. A matching session name does not prove reconnection: verify the actual group.

## Software design and validation

Optimize for changeability through cohesive modules with small interfaces that hide decisions and reduce caller knowledge. Split by independent responsibility, not execution order or line count. Avoid pass-through layers, speculative abstractions, and configuration that callers need not manage. Keep each decision in one place; improve a missing abstraction instead of accumulating special cases.

Make common use simple with sensible defaults, centralized recovery, and actionable errors. For consequential decisions, compare at least two materially different designs for interface complexity, information hiding, coupling, and usability. Use precise names; comments explain contracts, invariants, ownership, units, and rationale.

Run relevant tests and required repository checks. Broaden or repeat only when changes, failures, or unresolved risks justify it. Tests should prove behavior, not mirror implementation; documentation and mechanical edits do not need artificial regression tests.

## UI copy

Match existing copy density. Include necessary labels, values, statuses, errors, accessibility text, safety guidance, and required content. Keep empty states factual and actionable. Do not invent welcome text, taglines, decorative descriptions, or explanations that restate controls; improve the structure instead.
