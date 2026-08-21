---
name: task-management
description: Choose and operate the user's intended task system without coupling note, calendar, or project skills to one provider. Use for creating, capturing, updating, organizing, completing, or linking tasks and commitments; task-manager selection; Inbox placement; quick-add handoffs; or deciding between systems such as Todoist, Reminders, and Craft tasks.
---

# Task Management

Select the task system and placement before using a provider-specific tool. Preserve one authoritative task record and keep provider policy out of unrelated skills.

## Selection

Use this priority:

1. The system and destination explicitly named in the current request.
2. Repository, project, or domain instructions that establish the task owner.
3. The existing task or backlink being updated.
4. Current user preferences and live connected systems.

Do not treat an old note, cross-host entry, remembered preference, or whichever connector is easiest to call as proof of the current choice. If multiple systems remain plausible and the choice materially changes where the commitment lives, ask. Otherwise use the strongest contextual owner and state the choice.

## Placement and mutation

1. Load the selected provider's owning skill or inspect its live tool schema.
2. Before creating, inspect existing projects, lists, sections, labels/tags, and nearby related tasks when available. Never default to a generic Inbox when a better destination is evident.
3. Search for an existing task before creating a duplicate.
4. Preserve recurrence, due/deadline semantics, priority, assignment, parent/child structure, and labels when updating.
5. Make the smallest authorized mutation and read it back. Report the chosen system and placement.

When the user has not asked for creation, prefer a clearly labeled draft or provider-native quick-add handoff over silently creating a commitment.

## Ownership boundaries

- Craft, Notes, and document skills own their content mechanics, not task-manager selection. A document-local checklist is appropriate only after that document system has been selected as the task surface.
- Provider-specific schemas, recurrence behavior, Inbox semantics, and permission rules belong in the provider's own skill or live tool documentation.
- Cross-host context may explain routing, but it is supplementary and possibly stale; verify the selected task system live before writing.
- Keep one authoritative task record; link to supporting notes, documents, issues, or calendar events instead of copying status histories.

## Safety

Treat task creation, completion, reassignment, and notification as real writes. An explicit request naming the action and target authorizes that scoped write; otherwise confirm when the system, destination, audience, or commitment is materially ambiguous. Never expose private task links or contents to a broader system without authorization.
