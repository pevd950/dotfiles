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

Apply current user routing defaults when no stronger owner is established; do not copy provider preferences into this skill or move an existing record merely to match a default.

## Placement and mutation

1. Load the selected provider's owning skill or inspect its live tool schema. Link source material in the selected provider's documented field and format, applying user preferences rather than copying source content. For private sources, include only the brief context needed by the authorized audience.
2. Before creating, inspect existing projects, lists, sections, labels/tags, and nearby related tasks when available. Never default to a generic Inbox when a better destination is evident.
3. Search for an existing task before creating a duplicate.
4. Preserve recurrence, real due/deadline semantics, priority, assignment, parent/child structure, labels, and paused state when updating. Splitting or reorganizing must retain every unfinished requirement in the canonical record or linked successor; do not mark the original complete merely because it was reorganized.
5. Make the smallest authorized mutation and read it back. Report the chosen system and placement.

Honor scoped standing task-management authorization as well as the current request. Routine organization within that scope need not wait for redundant approval. For commitments outside that scope, prepare a labeled draft or provider-native quick-add handoff instead.

Write realistic next actions with a clear outcome. Separate actionable work, waiting dependencies (with owner or resume condition when known), optional work, and evidence-backed completion. Preserve existing owners and paused work. Do not invent deadlines or mechanically roll unfinished tasks to each new day; retain real deadlines and reschedule planned work only within the applicable grant. Keep permanent guidance as reference bullets rather than recurring unfinished checkboxes.

## Ownership boundaries

- For project bugs, features, and substantial coding work, the owning repository's issue tracker is authoritative for the implementation plan, acceptance criteria, decisions, and delivery history.
- A personal task-manager item may coexist with a GitHub Issue to track when the user plans to work on it. Keep that item short, link it to the Issue, and do not copy the Issue's technical plan into it.
- Treat these records as different responsibilities rather than duplicates: closing an Issue means the project work is resolved; completing the personal task means the user's scheduled commitment is handled. Require evidence for the specific completion claim; a handled personal commitment does not prove implementation or acceptance criteria are met. Do not assume one state change authorizes the other.
- Craft, Notes, and document skills own their content mechanics, not task-manager selection. A document-local checklist is appropriate only after that document system has been selected as the task surface.
- Provider-specific schemas, recurrence behavior, Inbox semantics, and permission rules belong in the provider's own skill or live tool documentation.
- Cross-host context may explain routing, but it is supplementary and possibly stale; verify the selected task system live before writing.

## Safety

Treat task or Issue creation, completion/closure, reassignment, and notification as real writes. Establish applicable authority from the current request or an explicit standing grant, including the actual destination, audience, and operation. A grant for personal task maintenance does not authorize closing an implementation Issue, bypassing acceptance gates, public publication, or changes to employer/team repositories outside explicit engagement scope. Private repository visibility alone neither makes a write public nor authorizes it. Ask only when a material ambiguity or change exceeds established authority; continue independent authorized work. Preserve safeguards for secrets, credentials, permissions/security, destructive actions, merges, and deployments. Never expose private task links or contents to a broader system without authorization.
