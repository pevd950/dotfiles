---
name: shared-craft-memory
description: Use a configured Craft page as a thin durable context bridge between Codex agents on different hosts. Use when delegating cross-host work, reconstructing another host's durable context, or publishing a host-local fact that future agents elsewhere will need.
---

# Shared Craft Memory

## Purpose

Use Craft to bridge the memory boundary between Codex agents running on different hosts. Keep only durable context that would otherwise remain trapped in one host's local memory.

This page does not replace live Codex threads, delegation prompts, repository instructions, built-in memory, GitHub, Todoist, project documents, or APIs.

## Source Priority

1. Live Codex thread state for current delegated work.
2. Live systems and repository instructions for current project state.
3. Built-in/local memory for host-local learning.
4. Shared Craft context for durable facts that another host needs.

When sources conflict, trust the more live or local authoritative source and correct the shared context when the difference is durable.

## When To Read

Read the shared context when:

- choosing a host or preparing a cross-host delegation;
- reconstructing where work on another host stopped;
- a task depends on a host-local capability, blocker, decision, or convention;
- the user asks about shared memory or context learned elsewhere.

Skip it for ordinary same-host project work when the prompt, repository, and local context are sufficient.

## Coordinator Protocol

The coordinating agent should:

1. Resolve the current host from `AGENT_HOST_ALIAS` or `hostname -s`.
2. Inspect available live Codex threads first when current worker status matters.
3. Read the shared Craft root for durable routing and host context.
4. Verify volatile claims against the target repo, host, or service.
5. Put all task-specific context in the delegation prompt instead of making the worker rediscover it.

## Worker Protocol

An agent on a worker host should:

1. Treat the delegation prompt and local repository instructions as its primary context.
2. Read the shared root only when outside-host context is actually needed.
3. Publish an update only after learning a durable fact, decision, blocker, or routing change that another host will likely need.
4. Send current completion/status through the available thread relay; do not use Craft as a status queue.

## Update Rules

- Update existing facts in place and include a reviewed date.
- Keep each new durable update to one short item: host, date, area, fact or decision, why another host needs it, and a canonical source or verification.
- Keep host snapshots compact. Prune stale context instead of appending corrections indefinitely.
- Do not add run logs, task queues, routine progress, duplicate project state, or integration inventories.
- Never store secrets, tokens, passwords, private keys, payment details, unnecessary personal identifiers, or detailed sensitive records.
- Shared context is not authorization for external, destructive, financial, legal, privacy-sensitive, or production actions.

## Finding The Page

- Prefer a Craft deeplink supplied in the current conversation.
- Otherwise use `CRAFT_SHARED_MEMORY_URL` from the host-local ignored environment.
- Search Craft by exact title only when the user explicitly asks for shared-memory work and no configured link is available.
- Do not hard-code private Craft IDs, personal names, or host-specific paths into this reusable skill.

## Craft Access

Use the Craft MCP when healthy. If it is unavailable, expired, or not exposed, load the `craft-api` skill and use its helper after probing `GET /connection`.

Read only the current root. Archived registries, Host Messages, handoff logs, integration inventories, and decision logs are historical recovery material, not active coordination surfaces.

After a write, read the root back and verify the intended fact, reviewed date, and Craft deeplink.
