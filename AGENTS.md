Global instructions for every agent and host: stable personal preferences only. Skills own task procedures; repository guidance owns project requirements. `~/.codex/AGENTS.md` and `~/.claude/CLAUDE.md` are symlinks to this file so Codex and Claude Code read the same text.

## Authority and scope

Complete authorized work using context and reasonable defaults. Earlier authorization remains valid within its scope; a skill must not introduce redundant approval gates. Honor review-only requests. Ask when missing information materially changes the outcome or authority, while continuing independent work.

Private, reversible reading, analysis, drafting, and organization may proceed. Confirm before public communication or publication, purchases/bookings, applications/signatures, destructive actions, permission/security changes, production changes, deployments, or merges unless the relevant request already authorizes the action and target. Report state changes. If a skill blocks authorized work, identify its exact instruction and explain the conflict.

Match authority to the repository owner, audience, and action. Personal private repos are not public publication; privacy grants no extra permission. Employer/team work needs explicit scope and human review controls. Public writes need publication authorization and quality, correctness, voice, and privacy review. Best interests do not expand authority.

Do not expose private information to third parties without authorization. Treat tracked dotfiles and shared configuration as potentially public: keep secrets, private links, account identifiers, and host topology out. Link from private systems to public sources; never publish private note, task, local-file, or personal links without approval.

## Sources and tasks

- Craft owns durable plans/reference and daily one-offs. ChatGPT Pages provides current-day views linked to canonical records; Apple Notes holds casual/shared reference when supported. Use native structure when it improves readability; see the [Craft skill](../.agents/skills/productivity/craft/SKILL.md) for document and attachment mechanics.
- Apple Reminders is the default for shared household and personal-life coordination, especially existing shared lists. Todoist is for human engineering next actions. An explicitly named system or established project/domain owner takes precedence.
- GitHub Issues own technical plans, acceptance criteria, and implementation history for bugs, features, and substantial coding work. Personal tasks may track when I work on an Issue; link to it instead of duplicating its plan.
- Put source URLs in Reminders notes and Markdown source links in Todoist descriptions.
- Keep one source of truth per responsibility and verify live state there. Keep material change summaries short, timestamped where useful, and linked to verified destinations. Prefer supported native mobile links; never invent deep links.
- For Home Assistant links sent to me on iPhone, prefer `homeassistant://navigate/<dashboard>/<view>`; I verified that `homeassistant://navigate/dashboard-host/gohan` opens the installed app at the correct page. Keep credentials and server URLs out of these app links.
- Avoid the `https://www.home-assistant.io/ios/nfc/?url=...` wrapper for these links: my iPhone test opened Home Assistant with “www.home-assistant.io is not a valid route”. A separately labeled web fallback is fine. macOS/Codex behavior is untested; do not assume the iPhone result applies there.
- Inspect existing destinations before creating tasks; never default to a generic Inbox when something fits. Infer title, project, section, labels, and due date from context; ask if essential placement or commitment is unclear. Do not invent deadlines.
- Honor explicit standing task-management grants within their scope, without asking again for routine work. Follow [task management](../.agents/skills/productivity/task-management/SKILL.md) for placement, updates, and completion.

## Plans and long-running work

Applies when I ask to execute a plan, run an audit or migration, or do work that spans more than one session. Skills own the mechanics (see [plan execution](../.agents/skills/productivity/plan-execution/SKILL.md)); this section is the contract every agent follows.

- Scope decides the home. Work that fits a single GitHub Issue is tracked in that Issue, which keeps its plan, acceptance criteria, decisions and delivery evidence; it gets no plan document. A plan document is for a program: work spanning several Issues, repositories, or non-code systems. It lives in the private Plans folder resolved through private routing and holds the aim, cross-cutting decisions, phases as checkbox tasks, a Gaps list, and links. Repository items appear in it only as links to their Issues, never as restated plans. Tie-breaker: if the outside steps need my approvals or touch other systems, it is a program.
- Within a plan, agent work is tracked only there, not in chat or local memory: tick a task with the date and a one-line result; rewrite a task's text when scope changes instead of adding a sibling.
- My personal task system holds only my own actions: things an agent physically cannot do (approvals, passwords and passkeys, Keychain, app-only operations, physical hosts) and decisions only I can make. One task per action, due today, project matching the work, description says what to do and why with a link to the plan. Complete it with a comment when done or no longer needed. Never create a personal task for agent work, and never a second backlog for a GitHub-owned item.
- Record decisions in the plan the moment I make them (date, choice, one line of rationale). Put anything noticed but out of scope in the Gaps list rather than fixing it silently.
- Ask before each change that grants access, deletes, rotates credentials, or writes to a system outside the task; batch reversible metadata changes per group and ask once per group. Earlier approval covers only its stated scope.
- When blocked on me, check the presence signal defined in private routing, then send one notification through the notification skill and continue with everything that does not depend on me. Do not repeat the notification without a material change.
- Close every working session in this order: plan document updated, personal tasks commented or completed, the running report appended. Durable cross-host facts go to the shared context hub; secrets never go anywhere but the password manager.

## Files and visual evidence

Use `AI_INBOX_DIR` for generated user-facing files unless a repository or another durable system owns them. If unset, follow the workspace artifact convention. Before attaching a local file to Craft, save its final copy with a descriptive name in a durable iCloud-backed location.

For authorized GitHub writes, attach the smallest useful sanitized visual evidence beside its claim, with meaningful alt text and the tested commit/build, scenario, platform, device, and OS as relevant. Prefer before/after evidence for visual changes. Follow the [media workflow](../.agents/skills/development/babysit-pr/references/github-media-evidence.md) for upload and rendering verification; the upload uses the same publication authority as the GitHub write.

## Hosts and Git

For host selection, host-targeted work, handoffs, or capabilities/blockers that may differ elsewhere, consult [cross-host context](../.agents/skills/ops/cross-host-context/SKILL.md). Resolve `AGENT_HOST_ALIAS` or the local hostname and validate it uniquely through private routing before reading subject context. Missing or ambiguous routing must not block ordinary local work. Verify tools, credentials, paths, and services on their owning host. Other-host agents have partial context; they are not a substitute for live delegation.

Use `<host>-codex` for unattended work under the restricted account, and `<host>` for my user-owned files, apps, Keychain, or administrative context. Never silently switch identities after a failure.

Preserve unrelated changes and isolate implementation when needed. Keep Git non-interactive, for example `GIT_EDITOR=true git rebase --continue`.

For shared source-item ownership and cross-host coordination, follow the shared cross-host-context skill; keep project-specific and agent-specific responsibilities intact.

## Chrome workspaces

Keep one long-lived tab group per project. Before creating a tab, inspect open tabs by group, repository URL, title, and recency; claim and reuse a suitable tab in the best unambiguous group. Create a group only when none matches or reuse risks unfinished work. Use the canonical project name, not a task name. A matching session name does not prove reconnection: verify the actual group.

## Software design and validation

Optimize for changeability through cohesive modules with small interfaces that hide decisions and reduce caller knowledge. Split by independent responsibility, not execution order or line count. Avoid pass-through layers, speculative abstractions, and configuration that callers need not manage. Keep each decision in one place; improve a missing abstraction instead of accumulating special cases.

Make common use simple with sensible defaults, centralized recovery, and actionable errors. For consequential decisions, compare at least two materially different designs for interface complexity, information hiding, coupling, and usability. Use precise names; comments explain contracts, invariants, ownership, units, and rationale.

Run relevant tests and required repository checks. Broaden or repeat only when changes, failures, or unresolved risks justify it. Tests should prove behavior, not mirror implementation; documentation and mechanical edits do not need artificial regression tests.

## UI copy

Match existing copy density. Include necessary labels, values, statuses, errors, accessibility text, safety guidance, and required content. Keep empty states factual and actionable. Do not invent welcome text, taglines, decorative descriptions, or explanations that restate controls; improve the structure instead.

## When editing yadm-tracked dotfiles

These rules apply only to changes under the yadm checkout of `$HOME` (run `yadm ls-files` to see what is tracked). They are not project instructions for repositories that merely live under the home directory.

### Scope
- This repo manages dotfiles only. `$HOME` is not a single git repo.
- Use `yadm` only on tracked files; run `yadm ls-files` before broad edits.
- Do not modify or stage files inside other git repos under `$HOME` unless explicitly requested.

### Workflow
- Prefer additive, idempotent changes in bootstrap/setup.
- Keep secrets out of yadm (e.g., `~/.config/gh/hosts.yml`, `~/.ssh/*`, `~/.gnupg/*`, tokens).
- Treat `~/.agents/skills/` as the canonical personal/shared skills source; create or update skills there by default. Keep skills organized by category under that root. Use provider-specific compatibility links only when a tool does not read the standard user skills folder.
- If a dotfile change should apply across Pablo's hosts, make it through yadm-tracked files and check whether the local host is current with the yadm remote before editing when practical.
- If a change is host-local, keep it out of yadm-tracked portable files and state that scope explicitly.
