---
name: task-management
description: Choose and operate the user's intended task or work-tracking system without coupling note, calendar, or project skills to one provider. Use for creating, capturing, updating, organizing, completing, or linking tasks and commitments; task-manager selection; Inbox placement; quick-add handoffs; GitHub Issues for bugs or implementation work; or deciding between Todoist, Reminders, Craft tasks, and project trackers.
---

# Task Management

Select the task system and placement before using a provider-specific tool. Preserve one authoritative record for each responsibility.

## Selection

Use this priority:

1. The system and destination explicitly named in the current request.
2. Repository, project, or domain instructions that establish the task owner.
3. The existing task or backlink being updated.
4. Current user preferences and live connected systems.

An old note, cross-host entry, remembered preference, or the connector that is easiest to call is a hint, not the current choice. If multiple systems remain plausible and the choice materially changes where the commitment lives, ask. Otherwise use the strongest contextual owner and state the choice.

Apply the user's current routing defaults when no stronger owner is established, and leave an existing record where it already lives.

## Placement and mutation

1. Load the selected provider's owning skill or inspect its live tool schema. Link source material in the selected provider's documented field and format, applying user preferences rather than copying source content. For private sources, include only the brief context needed by the authorized audience.
2. Before creating, inspect existing projects, lists, sections, labels/tags, and nearby related tasks when available, and place the task in the destination that fits. Never default to a generic Inbox when one fits.
3. Search for an existing task and update it when one matches.
4. Preserve recurrence, due dates, deadlines, priority, owners, structure, labels, and paused work. When splitting or reorganizing, keep unfinished requirements in the canonical record or linked successors. Reorganization is not completion. Complete a task when evidence shows its outcome, when the user says it is no longer needed, or when it is a duplicate or was created by mistake; clearing a duplicate or mistaken task you created needs no further approval.
5. Make the smallest authorized mutation and read it back. Report the chosen system and placement.

The current request or an explicit standing grant can cover task creation and routine maintenance. Continue within that scope; draft commitments outside it.

Use realistic next actions and show blocking dependencies. Keep permanent guidance as reference, not tasks. New tasks are due today unless the user gives another date or says later; keep real dates and deadlines, and leave unfinished work's dates as they are.

## Writing the task

Write the task as the user would have entered it, with fields carrying what is known instead of prose explaining it.

- **Title:** the action, short and imperative.
- **Fields:** project or list, section, labels, due date, duration and priority carry what they can. Set the ones you know or can sensibly infer from the request and its context, and leave a field empty when nothing fits: a made-up priority or duration is worse than none. Leave what the fields already say out of the description.
- **Description:** only what the user needs at the moment of doing the task: the few crucial details, then links. Leave out the story of the request, what the agent did or checked, and anything the title already says. Often two or three lines; sometimes only links.
- **Links:** each related record gets one labeled link that opens its native app on iPhone: the plan or document (the app link the document tool returns, such as a Craft `craftdocs://` link), the GitHub Issue or PR (its `github.com` URL opens the GitHub app), the source message or page. Use only link forms a tool returned or the user has verified.
- **Tasks an agent raises for the user:** add a link to the chat that raised it and to the related plan or Issue, so the task shows what it belongs to. Use the host's own link to the session when it gives one. Otherwise the agent bus prints a verified one: `codex-buddy-mcp --agent link --to <handle> --platform ios --markdown` (the helper ships inside the Codex Buddy Host app; `--agent peers` lists handles). With no verified link, name the chat by its title.
- **Steps:** checklist steps are subtasks or a linked checklist, not a numbered description.

## Ownership boundaries

- For project bugs, features, and substantial coding work, the owning repository's issue tracker is authoritative for the implementation plan, acceptance criteria, decisions, and delivery history.
- A workboard row or plan document (see the plan-execution skill) tracks progress on agent work and links each repository item to its Issue. It is never the destination for an Issue's implementation detail, acceptance criteria, or delivery history.
- A personal task-manager item may coexist with a GitHub Issue to track when the user plans to work on it. Keep that item short, link it to the Issue, and do not copy the Issue's technical plan into it.
- Require evidence for the outcome being claimed. Completing a personal task does not prove implementation or acceptance; closing an Issue needs its own authority and evidence.
- Use a document-local checklist only once that document system has been selected as the task surface.
- Cross-host context may explain routing, but it is supplementary and possibly stale; verify the selected task system live before writing.
