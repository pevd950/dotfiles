---
name: raindrop-mcp
description: Work with Raindrop.io bookmarks through the official remote MCP endpoint, using a direct JSON-RPC helper when Codex does not expose the Raindrop MCP tool namespace. Use for verifying Raindrop access, searching bookmarks, reading bookmark content, inspecting collections/tags/highlights, and carefully managing bookmark metadata when explicitly requested.
---

# Raindrop MCP

## Core rules

- When `mcp__raindrop__...` tools are not exposed in the session, call the official endpoint `https://api.raindrop.io/rest/v2/ai/mcp` directly through the bundled helper. `codex mcp list` is configuration-only — it does not prove the tools are callable here.
- Auth: `RAINDROP_ACCESS_TOKEN`; source the host's local shell exports first if it is not already set.
- Resolve the helper relative to this SKILL.md (`SKILL_DIR`); do not hard-code a home path.
- Prove access with a live read before claiming Raindrop works: `python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call fetch_current_user`.
- Read-only by default. No create/update/delete/merge/retag of bookmarks, collections, or highlights unless the user explicitly asks; for mutations, first read the affected object and state exactly what will change.

## Common reads

```bash
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" tools
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_bookmarks '{"query":"swift concurrency","limit":10}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call fetch_bookmark_content '{"bookmark_id":123456}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_collections '{"limit":50}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_tags '{"limit":50}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_highlights '{"limit":20}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_misplaced_bookmarks '{"limit":20}'
python3 "$SKILL_DIR/scripts/raindrop_mcp.py" call find_mistagged_bookmarks '{"limit":20}'
```

## Response style

Summarize the useful fields — no raw bookmark payload dumps unless requested. Include direct bookmark URLs when they help the user act. For organization audits, group findings into small actionable batches rather than cleaning the whole library at once.
