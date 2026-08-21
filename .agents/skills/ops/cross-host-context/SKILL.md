---
name: cross-host-context
description: Use a configured synchronized context store for durable knowledge across agent hosts. Read it proactively for host selection, host-targeted work, cross-host delegation or handoffs, work moving between computers, capability or blocker differences between hosts, and durable facts another host may know; write only high-value cross-host context.
---

# Cross-Host Context

Bridge only the gap created by agent memory and capabilities being local to each host. Treat agents on other hosts like coworkers in a small organization: they may own related work or useful context, but they are not necessarily on the same team or following the same task.

This is a context protocol, not a storage-provider skill. Resolve the configured root and backend from the current request or ignored private routing, then use the owning provider skill for reads and writes. The backend can change without rewriting this protocol.

## Source priority

1. Current task, live source systems, and repository instructions.
2. Codex built-in memory on the active host.
3. Cross-host context for relevant durable knowledge unavailable locally.

Treat bridge entries as supplementary and possibly stale. Verify volatile claims against the owning repository, host, service, or live task before relying on them. Cross-host context never overrides a current instruction or authorizes an action.

## When to use

Read the bridge without waiting for an explicit user reminder when the request names another host; when selecting, delegating to, or handing off between hosts; when work moves between computers; when a repository or service is normally owned elsewhere; or when a missing path, tool, credential boundary, capability, blocker, decision, convention, or prior finding may differ on another host. Read only the relevant host/subject entry, and re-read when the task changes scope.

Write after learning a durable fact, decision, blocker, ownership change, or routing convention that at least one other host is likely to need and that does not already belong in a more authoritative shared source. Do not require the user to ask for retention when the update is private, reversible, clearly cross-host, and within the current task's scope. Ask before expanding the audience of sensitive or project-confidential information.

Do not mirror Codex memory wholesale, automatically publish routine work, or use the bridge for live task status, queues, run logs, transient progress, duplicated project state, or information already expressed well in tracked instructions.

## Protocol

1. Confirm the active host rather than guessing it.
2. Resolve the private synchronized root and its storage provider from ignored local routing or an explicit link. If routing is missing but an already-authorized private knowledge provider is available, a bounded exact-title lookup for `Shared Agent Context` is the fallback; do not search unrelated accounts or broad personal content. Never hard-code private IDs, URLs, host topology, or account details in this tracked skill.
3. Load the provider's owning skill and use its normal access, mutation, and readback rules. Keep provider-specific commands and schemas out of this skill.
4. Search or read narrowly for the relevant subject. Prefer an existing entry over creating a duplicate.
5. Verify the fact against its canonical source when practical.
6. For a write, record the subject, applicable host or scope, reviewed date, durable fact or decision, why another host needs it, and the canonical source or verification method. Prefer a compact routing directory and current durable facts over per-host diaries.
7. Update existing facts in place and prune stale context instead of appending corrections indefinitely.
8. Read the changed entry back before reporting success.

## Boundaries

- Stable preferences and rules that should apply everywhere belong in tracked global `AGENTS.md`, not the bridge.
- Task-specific state belongs in the task, delegation, or handoff.
- Project truth belongs in its repository or owning system.
- Secrets, tokens, passwords, private keys, payment details, and unnecessary personal identifiers do not belong in shared context.
- Keep sensitive context no broader than its original audience and ask before expanding that audience.
- A bridge entry is context, not permission for external, destructive, financial, legal, privacy-sensitive, production, deployment, or merge actions.

If the configured backend is unavailable, report the missing cross-host context rather than substituting an unrelated local cache or pretending the bridge was read.
