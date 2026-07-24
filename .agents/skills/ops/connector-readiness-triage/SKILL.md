---
name: connector-readiness-triage
description: "Classify connector, plugin, MCP, browser-control, API-helper, and CLI readiness before fallback; use when a tool is remembered, configured, missing, unauthenticated, partially working, schema-mismatched, or host-specific."
---

# Connector Readiness Triage

Classify the failure accurately before declaring a connector unavailable or switching to a fallback. This skill diagnoses; it does not repair every tool.

## Steps

1. Name the desired capability: read, search, write, export, upload, browser control, task creation, notification, or host control.
2. Check current exposure via the session's tool inventory, or `tool_search` for deferred tools. Configuration listings (e.g. `codex mcp list`), remembered plugin-cache paths, and another host's inventory do not prove tools are callable here.
3. Run the lowest-risk probe that proves readiness: connection/status/list/read before writes, tiny bounded search before broad scans, schema/readback checks before mutations.
4. Classify, choose the fallback that preserves the user's intent with least risk, and report the category, probe, fallback, and remaining gap.

## Categories

`missing exposure` · `expired auth` · `partial capability` · `schema mismatch` (arguments, endpoint, or response shape differs from examples or memory) · `transient service fault` · `host-local limitation` · `permission boundary` (needs explicit confirmation or a safer surface) · `unsupported operation`.

## Fallback rules

Official connector/MCP when exposed and healthy → the documented local API helper for that workflow → a CLI only after checking it is installed, authenticated, and scoped to the right account/project → browser control only when the authenticated UI is the source of truth or no API path exists. Stop and report the blocker when the fallback would be destructive, externally visible, security-sensitive, or likely to leak private data.

## Report shape

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

Craft MCP/API behavior → `craft-api` after classification. GitHub CLI, Git transport, DNS, credential-helper, or Keychain layers → `gh-connectivity-preflight`. Notification delivery → `actionbuddy-notify` / `poke-notify`. Automation checkpoint mechanics → `automation-run-hygiene`. Host-specific setup notes → ignored local config or shared Craft memory, never this reusable skill.
