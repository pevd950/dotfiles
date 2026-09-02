Keep this file limited to stable, cross-repository personal preferences.

## Task systems

- Apple Reminders: shared household and personal-life coordination, especially items that belong on existing shared lists.
- Todoist: my individual project and work execution, including personally owned projects.
- A system named in the request, or already established by the owning project or domain, takes precedence over these defaults.
- Never default new tasks to a generic Inbox or Reminders List. Inspect existing projects, lists, sections, and labels and choose the best fit. Use Inbox only when nothing fits or I explicitly ask.
- For project bugs, features, and substantial coding work, the owning repository's GitHub Issue is the source of truth for the technical plan, acceptance criteria, and implementation history. A Todoist or Reminders item may track when I intend to work on it and should link to the Issue rather than duplicate its technical detail.
- When a task references a GitHub Issue, pull request, or comment, or any other third-party source, link to the source instead of copying its content. If the source is private, include a brief summary of the relevant context in the task description. For Apple Reminders, include the source url in the notes field, for Todoist, include a markdown link(s) in the description field.
- When a live source reveals a concrete near-term action that the chosen task system does not track, offer a clearly labeled draft or quick-add handoff. Create the task only when I explicitly ask.
- Include sensible defaults for task title, project, section, label, and due date when creating a new task. Use the request context to infer these defaults. If the request context is insufficient, ask for clarification before creating the task.

## Notes and links

Craft is my note-taking app and knowledge base: durable notes, documents, plans, profiles, references, and long-form context. Treat it as a rich document system, not a Markdown sink. Use hierarchy, nested pages, styling, callouts, tables, toggles, collections, covers, and other native structure liberally when they materially improve readability or navigation.

- Keep one source of truth per kind of state. Add concise backlinks instead of copying whole checklists or histories.
- Prefer stable cross-device links with descriptive labels. Where the destination supports it, wrap `craftdocs://` links in labeled Markdown links.
- Link from private systems to public items. Never put private note, task, local-file, or personal links in public GitHub content without explicit approval.

## Visual evidence on GitHub

When an authorized GitHub issue, pull request, or comment would be materially clearer with visual evidence, attach the smallest useful screenshot or video beside the claim it supports. Prefer before/after evidence for visual changes. Give images meaningful alt text and identify the tested commit or build, scenario, platform, device, and OS when relevant. Before upload, inspect media for secrets, private data, notifications, account identifiers, and unrelated UI. The upload is external publication under the same authorization rules as the GitHub write.

## Generated files

When `AI_INBOX_DIR` is set, put user-facing generated files there unless they belong in the current repository or another durable system. Use descriptive filenames with dates or task slugs. If it is unset, follow the owning workspace's artifact convention rather than inventing a machine-specific path.

Before attaching a generated or local file to Craft, save its final copy under a clear name in a durable iCloud-backed location, preferring `AI_INBOX_DIR` when nothing else owns it. Temporary, chat-pasteboard, localhost, `file://`, and disposable build paths are not durable attachments.

## Privacy and confirmation

Do not expose private information to third parties without explicit authorization.

Private, reversible work (reading, analysis, drafting, organization) may proceed without confirmation. Unless the most recent relevant request already specifies the exact action and target, confirm before: public external communication or publication, purchases or bookings, job applications or signatures, destructive actions, permission or security changes, production changes, deployments, or merges. After any state-changing action, report what changed.

Treat tracked dotfiles and shared configuration as potentially public. Keep secret values, private links, account identifiers, and host topology out of tracked files unless I explicitly approve the disclosure.

## Git

Keep Git non-interactive. Commands like plain `git rebase --continue` can open an editor and hang the session, so use no-editor forms such as `GIT_EDITOR=true git rebase --continue`.

## Hosts

For host-targeted work, resolve the active host from `AGENT_HOST_ALIAS`, falling back to `hostname -s`. Before reading subject context, validate that it maps uniquely through ignored local routing or the configured context root's routing directory. If the identity is unset, unknown, or ambiguous, treat shared context as unavailable without blocking ordinary local work. Don't assume tools, paths, credentials, or services transfer between hosts.

Agents on other hosts are coworkers with partial, potentially relevant context, not one shared team or a substitute for live delegation. For host selection, host-targeted work, cross-host handoffs, or a capability or blocker that may differ elsewhere, consult the configured shared context without waiting for me to ask. Read narrowly and verify current facts in their owning systems.

SSH hosts have two alias classes:

- `<host>-codex`: restricted agent account, no 1Password approval needed. Use for unattended or background work.
- `<host>`: my account. Use when work needs user-owned files, apps, Keychain items, or administrative context.

Never silently switch identities when a route fails.

## Chrome project workspaces

Chrome tab groups are long-lived project workspaces, not per-task sessions.

Before creating a tab for project work, inspect the open user tabs and index them by tab-group name, repository URL, page title, and recency. Select and claim a tab from the single best-matching existing project group, preferring an appropriate existing tab in that group over a new one. Create a new group only when no unambiguous match exists or reusing a tab could destroy unfinished user work. Name groups by stable canonical project name and never create separate groups for individual Codex tasks or turns. Giving a new browser session the same name does not reconnect it to an existing group; verify the group through the open-tab inventory first.

## Software design

Optimize for long-term changeability by reducing change amplification, cognitive load, and unknown unknowns. Working code is only the baseline.

- Prefer deep modules: small, simple interfaces that provide substantial cohesive functionality and hide implementation decisions. Avoid classitis, thin wrappers, pass-through methods, and layers that merely rename another layer.
- Line count is not a proxy for modularity. Split code when the pieces hold genuinely independent knowledge; keep related code together when separation would leak information or create coupled fragments.
- Decompose by information and responsibility, not execution order. Keep each design decision in one place and give each layer a distinct abstraction.
- Pull unavoidable complexity downward: give callers sensible defaults and handle common setup, policy, edge cases, and recovery internally rather than exporting configuration, call-order requirements, flags, or exceptions.
- Design general-purpose mechanisms around current requirements, separating reusable mechanism from application-specific policy. No speculative features.
- Make the common case obvious and simple. Define errors and special cases out of existence when practical; otherwise consolidate them by how callers can meaningfully handle them.
- When a feature exposes a missing abstraction, improve the abstraction instead of accumulating tactical special cases.
- For consequential design decisions, sketch at least two materially different designs and compare interface complexity, information hiding, coupling, and common-case usability.
- Use precise names and consistent conventions. Comments document contracts, invariants, ownership, units, non-obvious behavior, and rationale; they do not narrate the code.

## UI copy

No narrative or decorative copy. Never invent welcome text, taglines, explanatory subtitles, helper paragraphs, card descriptions, or prose that restates what the layout and controls already communicate.

Include only necessary labels, values, statuses, validation and error messages, safety-critical guidance, accessibility text, and content the product explicitly requires. Keep empty states factual and action-oriented. Prefer clearer structure, labels, and interactions over explaining the interface in prose, and match the existing product's copy density.
