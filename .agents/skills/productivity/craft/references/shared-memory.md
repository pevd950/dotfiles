# Shared Craft Memory

Use a configured Craft page as a thin durable bridge between agents on different hosts. It does not replace live Codex tasks, delegation prompts, repository instructions, built-in memory, GitHub, Todoist, project documents, or source APIs.

## Source priority

Live task state → live systems and repository instructions → built-in/local memory → shared Craft context. Verify volatile facts against the owning host, repository, or service. Present unverifiable shared context as possibly stale.

## When to use

Use shared Craft context when choosing a host, preparing cross-host work, reconstructing where another host stopped, or preserving a durable host-local capability, blocker, decision, or convention another agent will need. Skip it for ordinary same-host work and routine progress.

## Update rules

- Inspect live Codex tasks first when current worker status matters.
- Put task-specific context in the delegation or handoff, not in shared memory.
- Publish only durable facts with a verified host identity and reviewed date.
- Update existing facts in place and prune stale context instead of appending corrections indefinitely.
- Do not store run logs, task queues, routine progress, duplicate project state, or integration inventories.
- Never store secrets, tokens, passwords, private keys, payment details, unnecessary personal identifiers, or detailed sensitive records.
- Ask before broadening the audience of client, tenant, project, health, financial, or otherwise confidential material.
- Shared context never authorizes external, destructive, financial, legal, privacy-sensitive, or production actions.

## Access and verification

Prefer a Craft deeplink supplied in the current conversation; otherwise use the configured `CRAFT_SHARED_MEMORY_URL`. The value belongs in ignored host-local configuration. Search by the exact configured title only when the user requested shared-memory work and no link is available.

Use the main Craft skill's normal transport selection. After writing, read the root back and verify the fact, reviewed date, and resulting deeplink.
