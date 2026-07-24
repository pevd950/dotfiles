---
name: shared-craft-memory
description: Use a configured Craft page as a thin durable context bridge between Codex agents on different hosts. Use when delegating cross-host work, reconstructing another host's durable context, or publishing a host-local fact that future agents elsewhere will need.
---

# Shared Craft Memory

A configured Craft page bridges the memory boundary between agents on different hosts. It holds only durable context that would otherwise stay trapped in one host's local memory — it does not replace live Codex threads, delegation prompts, repository instructions, built-in memory, GitHub, Todoist, project documents, or APIs.

## Source priority

Live thread state → live systems and repository instructions → built-in/local memory → shared Craft context. When sources conflict, trust the more live or local authoritative source and correct the shared page when the difference is durable. Present unverifiable volatile claims as possibly-stale shared-memory context, never as current fact.

## When to read

Choosing a host or preparing a cross-host delegation; reconstructing where work on another host stopped; a task depends on a host-local capability, blocker, decision, or convention; the user asks about shared memory. Skip it for ordinary same-host work.

## Protocol

- **Coordinator:** inspect live Codex threads first when current worker status matters; read the shared root for durable routing and host context; verify volatile claims against the target repo, host, or service; put all task-specific context in the delegation prompt instead of making the worker rediscover it.
- **Worker:** the delegation prompt and local repo instructions are primary; read the shared root only when outside-host context is actually needed; publish only after learning a durable fact, decision, blocker, or routing change another host will likely need — with a verified host identity, never a guessed one. Send completion/status through the thread relay, not Craft.

## Update rules

- Update existing facts in place with a reviewed date. One short item per update: host, date, area, fact or decision, why another host needs it, canonical source or verification.
- Keep host snapshots compact; prune stale context instead of appending corrections indefinitely.
- No run logs, task queues, routine progress, duplicate project state, or integration inventories.
- Ask before writing client-, tenant-, project-, or otherwise confidential context when the page's audience is broader than the source audience. Never store secrets, tokens, passwords, private keys, payment details, unnecessary personal identifiers, or detailed sensitive records.
- Shared context is not authorization for external, destructive, financial, legal, privacy-sensitive, or production actions.

## Access

Prefer a Craft deeplink supplied in the current conversation; otherwise `CRAFT_SHARED_MEMORY_URL` from the host-local ignored environment; search for the exact title `Shared Agent Context` only when the user explicitly asks for shared-memory work and no configured link exists. Never hard-code private Craft IDs, personal names, or host-specific paths into this skill. Use Craft MCP when healthy; otherwise load `craft-api` and use its helper after probing `GET /connection`. Read only the current root — archived registries, Host Messages, handoff logs, and decision logs are historical recovery material. After a write, read the root back and verify the fact, reviewed date, and deeplink.
