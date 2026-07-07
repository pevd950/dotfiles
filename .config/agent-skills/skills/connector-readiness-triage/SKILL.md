---
name: connector-readiness-triage
description: "Classify connector, plugin, MCP, browser-control, API-helper, and CLI readiness before fallback; use when a tool is remembered, configured, missing, unauthenticated, partially working, schema-mismatched, or host-specific."
---

# Connector Readiness Triage

Use this skill before declaring a connector unavailable or switching to a fallback. Its job is to classify the failure accurately, not to repair every tool.

## When To Use It

- A remembered tool, app, MCP server, plugin, browser controller, CLI, or API helper is not callable in the current session.
- A connector exists but auth, schema, endpoint behavior, or host availability is uncertain.
- A workflow has a preferred connector plus a fallback, such as Craft MCP before Craft API.
- Different hosts appear to have different tool exposure.

## Triage Steps

1. Identify the desired capability:
   - Read, search, write, export, upload, browser control, task creation, notification, or host control.
2. Check current exposure:
   - Prefer the current tool inventory or session-provided app list.
   - Use `tool_search` for deferred MCP/plugin tools when available.
   - Do not rely on remembered plugin-cache paths or another host's inventory.
3. Run the lowest-risk probe that proves readiness:
   - Connection/status/list/read calls before writes.
   - Tiny bounded search before broad scans.
   - Schema/readback checks before mutations.
4. Classify the result using the categories below.
5. Choose the fallback that preserves the user's intent with the least risk.
6. Report the category, probe, fallback, and remaining gap.

## Categories

- `missing exposure`: expected tool is not available in this session.
- `expired auth`: tool is exposed but auth/session/token fails.
- `partial capability`: some operations work, but the needed operation is unavailable or blocked.
- `schema mismatch`: tool exists, but arguments, endpoint shape, or response shape differs from examples or memory.
- `transient service fault`: timeout, rate limit, 5xx, flaky native host, or temporary app state.
- `host-local limitation`: works on another host but is absent or differently configured here.
- `permission boundary`: technically possible, but needs explicit user confirmation or a safer surface.
- `unsupported operation`: no exposed tool or safe fallback can perform the requested operation.

## Fallback Rules

- Prefer an official connector or MCP tool when it is exposed and healthy.
- Use a local API helper when it is the documented fallback for that workflow.
- Use a CLI only after checking it is installed, authenticated, and scoped to the right account/project.
- Use browser control only when the authenticated UI is the source of truth or no API path exists.
- Stop and report the blocker when the fallback would be destructive, externally visible, security-sensitive, or likely to leak private data.

## Report Shape

Use this compact shape in final reports, Craft notes, or source-gap logs:

```text
Connector:
Desired capability:
Probe:
Classification:
Fallback:
Validation:
Remaining gap:
```

## Routing

- Craft MCP/API behavior belongs in `craft-api` after this skill classifies the readiness issue.
- GitHub CLI, Git transport, DNS, credential helper, or Keychain layers belong in a GitHub/Git preflight skill when available.
- Notification delivery details belong in `actionbuddy-notify` or `poke-notify`.
- Automation checkpoint mechanics belong in `automation-run-hygiene`.
- Host-specific setup notes belong in ignored local config or shared Craft memory, not in this reusable skill.
