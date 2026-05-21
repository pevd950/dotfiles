---
name: shared-craft-memory
description: Use a configured Craft document as supplemental shared memory across agents and hosts. Use when a user asks to review, reconcile, update, or hand off cross-host assistant context, shared operating rules, project registries, open loops, or agent-to-agent notes.
---

# Shared Craft Memory

## Purpose

Use a Craft document as supplemental shared memory for agents running on different hosts. This does not replace built-in agent memory, repo instructions, project files, or live source systems.

## Source Priority

1. Live systems are authoritative for current status: Todoist, GitHub, Craft project docs, email, calendars, ticket systems, local repos, and APIs.
2. Repository and project instructions are authoritative for project-specific workflow.
3. Built-in/local agent memory is authoritative for host-local quirks and prior agent-specific context.
4. Shared Craft memory is orientation and coordination context only.

If shared memory conflicts with a live source or local project instructions, trust the live/local source and propose a correction to shared memory.

## Finding The Memory Document

- Prefer a Craft deeplink provided by the user in the current conversation.
- Otherwise use `CRAFT_SHARED_MEMORY_URL` when it is set.
- If neither is available, search Craft for an exact title such as `AGENTS MEMORY` only when the user explicitly asks for shared memory work.
- On a new host, the user or agent may set `CRAFT_SHARED_MEMORY_URL` in that host's local ignored shell exports file so the memory document can be found without hard-coding the link into tracked dotfiles.
- Do not hard-code private Craft block IDs, personal names, addresses, or host-specific paths into reusable skill files.

## Host Identity

Before reading host-targeted messages or writing shared memory, determine the current host identity:

1. Prefer `AGENT_HOST_ALIAS` when it is set in a host-local ignored shell exports file.
2. Otherwise run `hostname -s` and use that short hostname.
3. Match the value against the Host Registry. If the hostname is unknown, use the raw value and add a short Host Registry or handoff note so future agents can map it.

Use the resolved host identity consistently:

- In Agent Handoffs, write `Agent/host: Codex on <Host>`.
- In Inbox / Host Messages, use the host name in `From` and/or `To`.
- When checking messages, read items addressed to the current host and `Any`.
- Do not infer host identity from prior conversation memory if a live shell check is available.

## Read Protocol

Use the Craft MCP, not ad hoc export files.

1. Resolve the current host identity.
2. Resolve the Craft link before reading blocks.
3. Read only the sections relevant to the task.
4. For general orientation, read:
   - Start Here
   - Latest Changes
   - Active Cross-Host Context
   - Open Loops
   - Inbox / Host Messages collection items addressed to the current host or `Any`
   - relevant index subpages: Host Registry, Project Registry, Agent Handoffs, Integration Inventory, and Decision Log
5. For a project-specific request, read that project's registry entry and then verify against the project repo, project Craft docs, Todoist project, and other live systems as needed.
6. State when an answer is based on shared memory and has not been live-verified.

## Update Protocol

Update shared memory when the user asks, when the task explicitly includes memory maintenance, or when a material cross-host fact changed and future agents are likely to need it. Do not update it for routine progress that is already captured better in a repo, Todoist, GitHub, Craft project doc, or another live system.

- Store one fact per bullet.
- Prefer compact dated entries.
- Keep the root page dashboard-like and human-scannable. Do not add large tables or long logs to the root.
- Add correction notes instead of silently rewriting history when a prior fact was wrong.
- Keep volatile items in active context or open loops with a review date.
- Move stale or completed items out of active sections after live verification.
- Never store secrets, tokens, passwords, private keys, full medical details, payment details, or unnecessary personal identifiers.
- Use canonical links to point to source systems instead of copying long source content.
- When updating opportunistically, keep the write small and mention it in the final handoff.
- Use the Inbox / Host Messages collection for host-to-host coordination, not ordinary project tasks.
- For actionable work that each host must complete independently, create one Inbox / Host Messages item per host. Do not use one multi-recipient row because one host marking it `Done` would incorrectly complete it for every recipient.
- Use multi-recipient `To` values only for FYI/broadcast messages where shared status is acceptable.
- Mark a host message `Seen` only after reading it and `Done` only after acting or verifying it no longer needs action.

## Recommended Structure

Use a compact dashboard root with nested pages for detail:

- Start Here: short behavior rules, source priority, and safety reminders.
- Latest Changes: the most recent 3-5 dated changes, newest first.
- Active Cross-Host Context: current items any agent may need, kept short.
- Open Loops: unresolved work with owner, next action, due/review date, and source link.
- Index: page cards for detail pages.

Use these detail pages:

- Inbox / Host Messages: a Craft collection for cross-host messages.
- Host Registry: host roles, limitations, auth/tool caveats, and verification notes.
- Project Registry: canonical links for repos, Craft folders/docs, Todoist projects, and source-of-truth notes.
- Agent Handoffs: timestamped notes from one host/agent to another.
- Integration Inventory: what is configured, where to verify it, and known failure modes; never include secret values.
- Decision Log: durable decisions with date, rationale, confidence, and revisit trigger.

Use collections only for workflow state. The Inbox / Host Messages collection is appropriate because rows have recipient, sender, status, area, review date, and optional link. Registries and inventories should stay as reference pages with compact tables or bullets unless they become workflow queues.

For per-host tasks, create separate rows:

- Good: `Kakarot: pull dotfiles...` with `To = Kakarot`, `Broly: pull dotfiles...` with `To = Broly`.
- Avoid: one `To = Kakarot, Broly, Tapion` row for work each host must complete independently.

Inbox / Host Messages collection schema:

- Message: item title / short action or notice.
- To: multi-select host target, including `Any` when host-independent.
- From: single-select sender host, `User`, or `Any`.
- Status: `Open`, `Seen`, `Done`, or `Stale`.
- Area: short text such as `Dotfiles / shared memory rollout`.
- Review Date: date for reassessment.
- Link: optional canonical source URL.

## Agent Handoff Shape

Use this shape for cross-host handoffs:

```text
Date:
Agent/host:
Area:
What changed:
Verified:
Remaining action:
Links:
```

Keep handoffs short enough to scan on a phone. Link to the canonical source instead of duplicating full logs.

## Safety

- Ask before writing if the update would expose sensitive personal, financial, health, tenant, client, or project-confidential details to a broader audience than the current source.
- For operational actions, shared memory is not approval. Get explicit confirmation at action time before sending messages, submitting forms, uploading files, booking services, spending money, or mutating external systems.
- If access to Craft MCP is unavailable, report the gap and do not fabricate memory state.
