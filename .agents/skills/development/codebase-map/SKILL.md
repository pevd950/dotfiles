---
name: codebase-map
description: Build a concise map of a codebase area before implementation. Use when asked to zoom out, orient a new agent, find where behavior lives, trace a subsystem, or identify the right files, flows, and validation commands.
---

# Codebase Map

## What this skill does
- Orients the agent in an unfamiliar or complex codebase area before editing.
- Traces entrypoints, data flow, side effects, tests, docs, and validation commands.
- Produces a compact map that helps future work start from evidence instead of guesses.

## When to use it
- Trigger phrases: "zoom out", "map this area", "orient me", "where does this live", "trace this subsystem", "give a new agent context", "find the right seam".
- Use before implementation when the relevant files, ownership, or flow are unclear.
- Use for handoffs when another agent needs durable context.
- Do not use as an architecture critique by default; use `architecture-scout` when the task is to judge or improve boundaries.

## Default stance
- Read broad enough to avoid wrong assumptions, then narrow quickly.
- Prefer local instructions, docs, tests, and code over memory or guesses.
- Keep the output concise and actionable.
- Separate confirmed facts from likely paths and open questions.
- Avoid proposing large changes unless the user asks for recommendations.

## Workflow

### 1. Anchor the question
Identify:
- feature, bug, workflow, endpoint, screen, command, or subsystem being mapped
- intended use of the map: implementation, debugging, review, onboarding, or issue planning
- target depth: quick orientation, implementation-ready handoff, or deep subsystem map

### 2. Find entrypoints
Search for:
- routes, commands, jobs, actions, screens, controllers, views, or handlers
- public APIs, generated clients, schemas, migrations, or configuration
- tests that already exercise the behavior
- docs or runbooks that describe expected behavior

Use fast targeted searches. Avoid reading the entire repo when the area can be narrowed.

### 3. Trace flow
Map:
- caller -> entrypoint -> service/domain logic -> persistence/provider/external side effect
- request/response or input/output shape
- configuration and feature flags
- auth, permissions, ownership, and validation
- error paths and observability
- async/background work, retries, streaming, or cancellation
- data lifecycle: creation, update, read, deletion, migration, cache, or index

### 4. Identify local patterns
Look for:
- nearby analogous features
- naming conventions
- test style and fixtures
- dependency injection or adapter patterns
- generated code workflow
- validation commands used by the repo

### 5. Summarize the map
Include:
- key files and what each owns
- main flow in 5-10 bullets
- tests and validation commands
- extension seams or likely edit points
- unknowns, risks, or questions
- related issues, PRs, or docs when known

### 6. Handoff for another agent
When preparing context for another agent:
- include exact paths and commands
- include what was searched and what was not found
- include known constraints and out-of-scope areas
- include validation expectations
- keep it self-contained enough to continue without private chat history

## Expected outputs
- Concise subsystem map.
- File/function/endpoint/test references.
- Data and control flow summary.
- Existing patterns to follow.
- Likely implementation seams.
- Validation commands and remaining unknowns.

## Do not
- Do not turn orientation into an unbounded architecture review.
- Do not claim behavior from naming alone; verify with code or tests.
- Do not list every file if only a few are relevant.
- Do not recommend refactors unless asked or unless the map would be misleading without a risk note.
