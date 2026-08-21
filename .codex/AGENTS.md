Keep this file limited to stable, cross-repository personal preferences.

I may use different task systems for different areas, including Todoist and Apple Reminders. Follow the system named in the request or established by the owning project/domain instead of assuming one global default. Never default new tasks to a generic Inbox: inspect existing projects, lists, sections, and labels and choose the best fit. Use Inbox only when nothing fits or I explicitly ask.

When a live source reveals a concrete near-term action that is not tracked in the chosen task system, offer a clearly labeled draft or quick-add handoff instead of creating the task unless I explicitly ask you to create it.

Craft is my note-taking app and knowledge base. Use it for durable notes, documents, plans, profiles, references, and long-form context. Treat Craft as a rich document system, not a Markdown sink: use hierarchy, nested pages, styling, callouts, tables, toggles, collections, covers, and other native structure liberally when they materially improve readability or navigation.

Keep one source of truth for each kind of state and add concise backlinks instead of copying whole checklists or histories. Prefer stable cross-device links with descriptive labels. When the destination supports it, wrap `craftdocs://` links in labeled Markdown links. Link from private systems to public items; never place private note, task, local-file, or personal links in public GitHub content without explicit approval.

When `AI_INBOX_DIR` is set, put user-facing generated files there if they do not belong in the current repository or another durable system. Use descriptive filenames with dates or task slugs. Before attaching a generated or local file to Craft, make sure its final copy is saved in a durable iCloud-backed location—prefer `AI_INBOX_DIR` when it has no other owner—and is named clearly. Do not use temporary, chat-pasteboard, localhost, `file://`, or disposable build paths as durable attachments. If `AI_INBOX_DIR` is unset, use the owning workspace's artifact convention rather than inventing a machine-specific path.

Do not expose private information to third parties without explicit authorization.

Private, reversible work (reading, analysis, drafting, organization) may proceed without confirmation. Unless the latest request already specifies the exact action and target, confirm before: external communication or publication, purchases or bookings, job applications or signatures, destructive actions, permission or security changes, production changes, deployments, or merges. After a state-changing action, report what changed.

Treat tracked dotfiles and shared configuration as potentially public. Keep secret values, private links, account identifiers, and host topology out of tracked files unless I explicitly approve the disclosure.

Keep Git operations non-interactive: commands like plain `git rebase --continue` can open an editor and hang the session. Use no-editor forms such as `GIT_EDITOR=true git rebase --continue`.

For host-targeted work, resolve the active host from `AGENT_HOST_ALIAS`, falling back to `hostname -s`. Don't assume tools, paths, credentials, or services transfer between hosts.

Treat agents on other hosts as coworkers with partial, potentially relevant context, not as one shared team or a substitute for live delegation. For host selection, host-targeted work, cross-host handoffs, or a capability/blocker that may differ elsewhere, consult the configured shared context without waiting for me to request it; read narrowly and verify current facts in their owning systems.

SSH hosts have two alias classes: `<host>-codex` (restricted agent account, no 1Password approval needed—use for unattended or background work) and `<host>` (my account—use when work needs user-owned files, apps, Keychain items, or administrative context). Never silently switch identities when a route fails.
