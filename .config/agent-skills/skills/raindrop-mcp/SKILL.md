---
name: raindrop-mcp
description: Work with Raindrop.io bookmarks through the official remote MCP endpoint, using a direct JSON-RPC helper when Codex does not expose the Raindrop MCP tool namespace. Use for verifying Raindrop access, searching bookmarks, reading bookmark content, inspecting collections/tags/highlights, and carefully managing bookmark metadata when explicitly requested.
---

# Raindrop MCP

## Core Rules

- Use the official Raindrop.io MCP endpoint directly when `mcp__raindrop__...` tools are not exposed in the current session:

```text
https://api.raindrop.io/rest/v2/ai/mcp
```

- Source the host's local shell exports before reads when `RAINDROP_ACCESS_TOKEN` is not already available:

```bash
source /path/to/local/exports
```

- Let `SKILL_DIR` mean the directory containing this `SKILL.md`. Resolve the helper relative to the skill file; do not hard-code a user's home path.

- Prove access with a live read before claiming Raindrop works:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call fetch_current_user
```

- Treat `codex mcp list` as configuration-only. It does not prove Raindrop tools are callable in the current Codex session.
- Prefer read-only operations. Do not create, update, delete, merge, or retag bookmarks/collections/highlights unless the user explicitly asks for that mutation.
- For mutating operations, first read the affected bookmark, collection, tag, or highlight and state the exact object that will change.

## Common Reads

List available MCP tools:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" tools
```

Fetch current account/library stats:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call fetch_current_user
```

Search bookmarks:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_bookmarks '{"query":"swift concurrency","limit":10}'
```

Fetch bookmark content:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call fetch_bookmark_content '{"bookmark_id":123456}'
```

Inspect organization:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_collections '{"limit":50}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_tags '{"limit":50}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_highlights '{"limit":20}'
```

Find cleanup candidates:

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_misplaced_bookmarks '{"limit":20}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_mistagged_bookmarks '{"limit":20}'
```

## Response Style

- Summarize only the useful fields; do not dump raw bookmark payloads unless requested.
- Include direct bookmark URLs when they help the user act.
- For organization audits, group findings into small actionable batches rather than trying to clean the whole library at once.
