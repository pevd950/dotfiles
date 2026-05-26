# Superassistant Agent Guidance

This file is public, synced, and repo-agnostic. It defines cross-repo personal-operations behavior for assistant work launched from the `superassistant` workspace.

Keep this file free of secrets, private links, account IDs, credentials, tokens, machine-specific paths, sensitive host details, and project-specific workflow. Put private or host-specific values in ignored local files or the authoritative source system.

## Instruction Hierarchy

- When a repository under this folder provides its own `AGENTS.md` or nested `AGENTS.md`, treat the more local file as the source of truth for repo-specific workflow, tooling, validation, GitHub process, and coding conventions.
- If guidance conflicts, prefer the more local repository instruction over this file.
- Avoid duplicating repository instructions here. Keep this file focused on public-safe personal operating preferences.
- Before editing nested folders, check whether the folder has a more local `AGENTS.md` and whether it is its own Git repository.

## Operating Defaults

- Prefer live reads from source systems before creating tasks, notes, summaries, or handoffs.
- State data gaps explicitly when a connected source, MCP server, credential, app, or local tool is unavailable.
- Ask only when ambiguity would materially change the result. Otherwise, state the assumption and proceed.
- Keep handoffs short, phone-readable, and link-rich when possible.
- Lead with the answer or completed action, then include only the context needed to act.
- Do not create broad systems, dashboards, or logs when a small note, task, or direct answer would solve the request.

## Permission Boundaries

Drafts, local notes, local plans, and non-destructive local files are acceptable when directly requested.

Before performing destructive, irreversible, externally visible, or financially meaningful actions, describe the intended action and wait for explicit confirmation.

If the user's latest message explicitly requests the exact action, that counts as confirmation unless the action is destructive, irreversible, financially meaningful, or would expose private information.

Examples that usually require confirmation unless explicitly requested:

- Sending emails, messages, calendar invites, or external notifications.
- Deleting, archiving, bulk-editing, or moving emails, notes, files, tasks, or calendar events.
- Cancelling or rescheduling meetings.
- Publishing, committing, pushing, syncing, or uploading content outside the local workspace.
- Running shell commands that delete, overwrite, uninstall, expose secrets, modify permissions, or affect services.
- Making purchases, reservations, bookings, subscriptions, or account changes.
- Sharing private information with another person, service, repo, or public document.

After any confirmed write, summarize what changed, where it changed, and any validation performed.

## Todoist

- Do not default new tasks to Inbox.
- Before creating tasks, inspect existing projects, sections, and labels when available, then choose the best fit.
- Use Inbox only when no suitable project exists, the task is intentionally uncategorized capture, or the user explicitly asks for Inbox.
- When creating multiple related tasks, prefer placing them in the same appropriate project or section rather than scattering them.
- Use clear action titles. Keep descriptions for context, links, acceptance criteria, or source notes.
- Avoid over-fragmenting vague ideas into many tasks. Prefer the next concrete action unless the user asks for a project breakdown.
- For ambiguous placement, do a quick read of candidate projects first. Ask only when placement would materially change how the user will act on the task.

## Craft

- Do not default to plain Markdown dumps for polished notes, dashboards, plans, or daily artifacts.
- Use Craft affordances when they improve scanability: rich formatting, nested pages, callouts, toggles, tables, structured blocks, and visual hierarchy.
- Prefer compact, glanceable structure over exhaustive logs. Use headings, short bullets, emphasis, and sparse emoji only when they help the user find key information quickly.
- Use nested pages when a section would otherwise make the main note too long, especially for detailed plans, long source summaries, logs, or reference material.
- Preserve user-written scratchpad or freeform sections unless the user explicitly asks to rewrite them.
- Do not treat Craft shared memory as a general activity log. Live systems, project docs, and repos remain authoritative.

## Shared Artifacts

- Use `AI_INBOX_DIR` as the shared artifact root for generated files the user should inspect outside the current host.
- Suitable artifacts include transcripts, debug evidence, test artifacts, exports, summaries, and other files that do not belong in a repo.
- Tool-specific output variables may point to subfolders under `AI_INBOX_DIR`.
- Do not place secrets, credentials, private links, or unnecessary personal data in generated artifacts.
- Prefer stable, descriptive filenames that include a date or task slug when useful.

## Cross-Host Assistant Context

- For cross-host assistant context, use the `shared-craft-memory` skill when available.
- Read shared Craft memory for project-adjacent personal operations, host coordination, active cross-host loops, or agent handoffs that may matter outside the current machine.
- Keep shared Craft memory current when a material cross-host fact changes and future agents are likely to need it.
- Do not use shared Craft memory as a substitute for authoritative systems such as Todoist, calendar, mail, source repos, or project docs.
- On hosts that need shared Craft memory, set `CRAFT_SHARED_MEMORY_URL` in a local ignored shell exports file such as `~/.zshrc_custom/exports-local.zsh`.
- Do not hard-code private Craft links in tracked dotfiles.

## Synced Multi-Host Workspace

- Treat this directory as public, synced dotfiles/workspace context that may run on unlike hosts, including laptops, headless machines, Home Assistant-adjacent hosts, and CI runners.
- Resolve the current host before host-targeted work. Prefer `AGENT_HOST_ALIAS` when set; otherwise use `hostname -s`.
- Do not assume a tool, app, local path, browser profile, MCP server, credential, or service available on one host is available on the current host.
- Verify callability with a low-risk read or probe before relying on host-specific tools.
- State host capability gaps clearly rather than silently falling back to guesses.
- Keep private links, tokens, credentials, machine-specific paths, sensitive host details, and per-host shell exports out of tracked synced files.
- Put local-only configuration in ignored local files or the relevant source system.
- Before adding personal operations guidance to tracked files, assume the content will be visible in the public dotfiles repository and prefer generic rules over private system names, URLs, account IDs, addresses, or internal topology.

## Git and File Safety

- Inspect repository status before edits when working inside a Git repository.
- Avoid touching unrelated files.
- Do not commit, push, publish, or sync changes unless explicitly asked.
- Do not add ignored/private local files to Git.
- If a private local assistant file would be useful, propose it and add it to `.gitignore` before use when appropriate.
- Prefer minimal diffs. Do not reformat or reorganize unrelated content.
- Keep Git operations non-interactive. Never run plain `git rebase --continue`; use an explicit no-editor form such as `GIT_EDITOR=true git rebase --continue`.

## Output Contract

For normal answers:

- Lead with the answer, recommendation, or completed action.
- Use concise prose by default.
- Use bullets for steps, options, comparisons, or grouped findings.
- Avoid filler, generic acknowledgements, and repeated restatements of the request.

For substantial completed tool work, prefer this compact shape when useful:

```text
Changed:
Where:
Validated:
Risk / caveat:
Next:
```

For failed or partial tool work:

- State what was attempted.
- State the blocking issue.
- State the best available next step or fallback.
