Keep this file limited to stable, cross-repository personal preferences.

I use Apple Reminders for shared household and personal-life coordination, especially items that belong on existing shared lists. I use Todoist for my individual project and work execution, including personally owned projects. Follow a system named in the request or already established by the owning project/domain before applying these defaults. Never default new tasks to a generic Inbox: inspect existing projects, lists, sections, and labels and choose the best fit. Use Inbox only when nothing fits or I explicitly ask.

For project bugs, features, and substantial coding work, the owning repository's GitHub Issue is the source of truth for the technical plan, acceptance criteria, and implementation history. A corresponding Todoist or Reminders item may track when I intend to work on it and should link to the Issue instead of duplicating its technical detail.

When a live source reveals a concrete near-term action that is not tracked in the chosen task system, offer a clearly labeled draft or quick-add handoff instead of creating the task unless I explicitly ask you to create it.

Craft is my note-taking app and knowledge base. Use it for durable notes, documents, plans, profiles, references, and long-form context. Treat Craft as a rich document system, not a Markdown sink: use hierarchy, nested pages, styling, callouts, tables, toggles, collections, covers, and other native structure liberally when they materially improve readability or navigation.

Keep one source of truth for each kind of state and add concise backlinks instead of copying whole checklists or histories. Prefer stable cross-device links with descriptive labels. When the destination supports it, wrap `craftdocs://` links in labeled Markdown links. Link from private systems to public items; never place private note, task, local-file, or personal links in public GitHub content without explicit approval.

When `AI_INBOX_DIR` is set, put user-facing generated files there if they do not belong in the current repository or another durable system. Use descriptive filenames with dates or task slugs. Before attaching a generated or local file to Craft, make sure its final copy is saved in a durable iCloud-backed location—prefer `AI_INBOX_DIR` when it has no other owner—and is named clearly. Do not use temporary, chat-pasteboard, localhost, `file://`, or disposable build paths as durable attachments. If `AI_INBOX_DIR` is unset, use the owning workspace's artifact convention rather than inventing a machine-specific path.

Do not expose private information to third parties without explicit authorization.

Private, reversible work (reading, analysis, drafting, organization) may proceed without confirmation. Unless the latest request already specifies the exact action and target, confirm before: external communication or publication, purchases or bookings, job applications or signatures, destructive actions, permission or security changes, production changes, deployments, or merges. After a state-changing action, report what changed.

Treat tracked dotfiles and shared configuration as potentially public. Keep secret values, private links, account identifiers, and host topology out of tracked files unless I explicitly approve the disclosure.

Keep Git operations non-interactive: commands like plain `git rebase --continue` can open an editor and hang the session. Use no-editor forms such as `GIT_EDITOR=true git rebase --continue`.

For host-targeted work, resolve the active host from `AGENT_HOST_ALIAS`, falling back to `hostname -s`, then validate that it maps uniquely through ignored local routing or the configured context root's routing directory before reading subject context. If the identity is unset, unknown, or ambiguous, treat shared context as unavailable without blocking ordinary local work. Don't assume tools, paths, credentials, or services transfer between hosts.

Treat agents on other hosts as coworkers with partial, potentially relevant context, not as one shared team or a substitute for live delegation. For host selection, host-targeted work, cross-host handoffs, or a capability/blocker that may differ elsewhere, consult the configured shared context without waiting for me to request it; read narrowly and verify current facts in their owning systems.

SSH hosts have two alias classes: `<host>-codex` (restricted agent account, no 1Password approval needed—use for unattended or background work) and `<host>` (my account—use when work needs user-owned files, apps, Keychain items, or administrative context). Never silently switch identities when a route fails.

## Software design

Optimize for long-term changeability by reducing change amplification, cognitive load, and unknown unknowns. Working code is only the baseline.

- Prefer deep modules: small, simple interfaces that provide substantial cohesive functionality and hide implementation decisions. Avoid classitis, thin wrappers, pass-through methods, and layers that merely rename another layer.
- Do not use line count as a proxy for modularity. Split code when the pieces contain genuinely independent knowledge; keep related code together when separation would leak information or create coupled fragments.
- Decompose by information and responsibility, not execution order. Keep each design decision in one place, and ensure each layer introduces a distinct abstraction.
- Pull unavoidable complexity downward. Give callers sensible defaults and handle common setup, policy, edge cases, and recovery internally rather than exporting configuration, call-order requirements, flags, or exceptions.
- Design general-purpose mechanisms around current requirements, separating reusable mechanism from application-specific policy. Do not add speculative features.
- Make the common case obvious and simple. Define errors and special cases out of existence when practical; otherwise consolidate them according to how callers can meaningfully handle them.
- When a feature exposes a missing abstraction, improve the abstraction instead of accumulating tactical special cases.
- For consequential design decisions, sketch at least two materially different designs and compare interface complexity, information hiding, coupling, and common-case usability.
- Use precise names and consistent conventions. Comments should document contracts, invariants, ownership, units, non-obvious behavior, and rationale—not narrate the code.

## UI copy

Do not add narrative or decorative copy to interfaces. Never invent welcome text, taglines, explanatory subtitles, helper paragraphs, card descriptions, or prose that merely restates what the layout and controls already communicate.

Default to only necessary labels, values, statuses, validation and error messages, safety-critical guidance, accessibility text, and content explicitly required by the product. Keep empty states factual and action-oriented. Prefer clearer structure, labels, and interactions over explaining the interface in prose, and match the existing product’s copy density.
