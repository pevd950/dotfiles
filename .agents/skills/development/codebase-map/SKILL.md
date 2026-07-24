---
name: codebase-map
description: Build a concise map of a codebase area before implementation. Use when asked to zoom out, orient a new agent, find where behavior lives, trace a subsystem, or identify the right files, flows, and validation commands.
---

# Codebase Map

Produce a compact, evidence-based map of a codebase area. This is orientation, not architecture critique — use `architecture-scout` to judge or improve boundaries.

Anchor first: what is being mapped, what the map is for (implementation, debugging, review, onboarding, issue planning), and the depth required. Trace the real flow — entrypoints, domain logic, persistence and provider side effects, auth and validation, error paths, async work — and note the local patterns a change should follow: nearby analogous features, test style and fixtures, DI/adapter conventions, generated-code workflow, and the repo's validation commands.

## Map contents

- Key files and what each owns.
- Main flow in 5-10 bullets.
- Tests and validation commands.
- Existing patterns to follow and likely edit seams.
- Confirmed facts separated from likely paths and open questions.
- Related issues, PRs, or docs when known.

## Handoff for another agent

Make it self-contained enough to continue without private chat history: exact paths and commands, what was searched and what was not found, known constraints and out-of-scope areas, validation expectations.

Do not claim behavior from naming alone, list files that are not relevant, or recommend refactors unless asked (or the map would mislead without a risk note).
