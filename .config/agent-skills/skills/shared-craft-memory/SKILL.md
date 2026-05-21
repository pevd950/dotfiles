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
- Do not hard-code private Craft block IDs, personal names, addresses, or host-specific paths into reusable skill files.

## Read Protocol

Use the Craft MCP, not ad hoc export files.

1. Resolve the Craft link before reading blocks.
2. Read only the sections relevant to the task.
3. For general orientation, read:
   - how to use this doc
   - source priority
   - host registry
   - project registry
   - active cross-host context
   - open loops
   - latest decision log entries
4. For a project-specific request, read that project's registry entry and then verify against the project repo, project Craft docs, Todoist project, and other live systems as needed.
5. State when an answer is based on shared memory and has not been live-verified.

## Update Protocol

Update shared memory only when the user asks or when the task explicitly includes memory maintenance.

- Store one fact per bullet.
- Prefer compact dated entries.
- Add correction notes instead of silently rewriting history when a prior fact was wrong.
- Keep volatile items in active context or open loops with a review date.
- Move stale or completed items out of active sections after live verification.
- Never store secrets, tokens, passwords, private keys, full medical details, payment details, or unnecessary personal identifiers.
- Use canonical links to point to source systems instead of copying long source content.

## Recommended Structure

If the memory document needs restructuring, prefer these top-level areas:

- How To Use This Doc: short behavior rules for all agents.
- Source Priority: explicit authority order for live systems, repo instructions, local memory, and shared memory.
- Host Registry: each host's role, limitations, and local-only caveats.
- Project Registry: canonical links for repos, Craft folders/docs, Todoist projects, and source-of-truth notes.
- Active Cross-Host Context: current items any agent may need, each with a review date.
- Open Loops: unresolved work with owner, next action, due/review date, and source link.
- Decision Log: durable decisions with date, rationale, confidence, and revisit trigger.
- Agent Handoffs: timestamped notes from one host/agent to another.
- Integration Inventory: what is configured, where to verify it, and known failure modes; never include secret values.

## Agent Handoff Shape

Use this shape for cross-host handoffs:

```text
- Date:
- Agent/host:
- Area:
- What changed:
- Verified:
- Remaining action:
- Links:
```

Keep handoffs short enough to scan on a phone. Link to the canonical source instead of duplicating full logs.

## Safety

- Ask before writing if the update would expose sensitive personal, financial, health, tenant, client, or project-confidential details to a broader audience than the current source.
- For operational actions, shared memory is not approval. Get explicit confirmation at action time before sending messages, submitting forms, uploading files, booking services, spending money, or mutating external systems.
- If access to Craft MCP is unavailable, report the gap and do not fabricate memory state.
