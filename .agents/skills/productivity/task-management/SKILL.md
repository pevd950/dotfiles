---
name: task-management
description: Choose and operate the user's intended task or work-tracking system without coupling note, calendar, or project skills to one provider. Use for creating, capturing, updating, organizing, completing, or linking tasks and commitments; task-manager selection; Inbox placement; quick-add handoffs; GitHub Issues for bugs or implementation work; or deciding between Todoist, Reminders, Craft tasks, and project trackers.
---

# Task Management

Select the task system and placement before using a provider-specific tool. Preserve one authoritative record for each responsibility and keep provider policy out of unrelated skills.

## Selection

Use this priority:

1. The system and destination explicitly named in the current request.
2. Repository, project, or domain instructions that establish the task owner.
3. The existing task or backlink being updated.
4. Current user preferences and live connected systems.

Do not treat an old note, cross-host entry, remembered preference, or whichever connector is easiest to call as proof of the current choice. If multiple systems remain plausible and the choice materially changes where the commitment lives, ask. Otherwise use the strongest contextual owner and state the choice.

When no stronger owner is established, prefer Apple Reminders for shared household and personal-life coordination, especially work that belongs on an existing shared list. Prefer Todoist for the user's individual project and work execution, including personally owned projects. These are routing defaults, not reasons to duplicate a task or move an existing record out of its established system.

## Placement and mutation

1. Load the selected provider's owning skill or inspect its live tool schema.
2. Before creating, inspect existing projects, lists, sections, labels/tags, and nearby related tasks when available. Never default to a generic Inbox when a better destination is evident.
3. Search for an existing task before creating a duplicate.
4. Preserve recurrence, due/deadline semantics, priority, assignment, parent/child structure, and labels when updating.
5. Make the smallest authorized mutation and read it back. Report the chosen system and placement.

When the user has not asked for creation, prefer a clearly labeled draft or provider-native quick-add handoff over silently creating a commitment.

## Ownership boundaries

- For project bugs, features, and substantial coding work, the owning repository's issue tracker is authoritative for the implementation plan, acceptance criteria, decisions, and delivery history.
- A personal task-manager item may coexist with a GitHub Issue to track when the user plans to work on it. Keep that item short, link it to the Issue, and do not copy the Issue's technical plan into it.
- Treat these records as different responsibilities rather than duplicates: closing an Issue means the project work is resolved; completing the personal task means the user's scheduled commitment is handled. Do not assume one state change authorizes the other.
- Craft, Notes, and document skills own their content mechanics, not task-manager selection. A document-local checklist is appropriate only after that document system has been selected as the task surface.
- Provider-specific schemas, recurrence behavior, Inbox semantics, and permission rules belong in the provider's own skill or live tool documentation.
- Cross-host context may explain routing, but it is supplementary and possibly stale; verify the selected task system live before writing.
- Keep one authoritative record for each responsibility: the Issue for project state and the personal task for the user's commitment. Link supporting records instead of copying technical detail or status histories.

## Safety

Treat task or Issue creation, completion/closure, reassignment, and notification as real writes. An explicit request naming the action and target authorizes only that scoped write. Confirm whenever the system, repository, visibility, destination, audience, or commitment is materially ambiguous. Never expose private task links or contents to a broader system without authorization.
