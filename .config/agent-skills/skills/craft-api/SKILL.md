---
name: craft-api
description: Use Craft through its HTTP API as a durable fallback when Craft MCP is unavailable, expired, or impractical on headless hosts. Use for reading, searching, creating, updating, moving, or deleting Craft documents, blocks, collections, comments, uploads, and connection metadata via CRAFT_API_BASE_URL and CRAFT_API_KEY.
---

# Craft API

Use this skill when Craft MCP is missing, unauthenticated, expired, or awkward to use from a headless host. Prefer Craft MCP when it is available because it provides higher-level commands, but treat the API as the durable fallback for real read/write work.

## Environment

Assume the shell environment is already loaded. Before calling the API, verify that the required variables are present:

```shell
test -n "$CRAFT_API_BASE_URL"
test -n "$CRAFT_API_KEY"
```

Expected local-only variables:

- `CRAFT_API_BASE_URL`: connection URL ending in `/api/v1`
- `CRAFT_API_KEY`: private key for that connection

If those variables are missing, ask the user to add them to a host-local ignored secrets file or shell startup path. Do not assume a specific home directory, dotfiles layout, shell, or secrets-file path.

Never write API keys, private Craft links, user-specific paths, or space IDs into tracked skill files, PR bodies, Craft demo pages, or logs.

## Auth

Observed behavior: Craft API connections may succeed with `Authorization: Bearer $CRAFT_API_KEY` even when docs or examples mention `x-craft-api-key`. Try bearer auth first; keep `x-craft-api-key` as a fallback for connections that require it.

Use the bundled helper for routine calls because it centralizes auth and avoids printing secrets. Let `SKILL_DIR` mean the directory containing this `SKILL.md`, then run:

```shell
python3 "$SKILL_DIR/scripts/craft_api.py" GET /connection
python3 "$SKILL_DIR/scripts/craft_api.py" GET /documents
```

Resolve the script relative to this `SKILL.md` file. Do not assume the current working directory is the skill folder, and do not hard-code a user's home path.
When another skill needs Craft API access, call this helper instead of reimplementing HTTP in shell, Python, or curl unless you are deliberately debugging the helper itself.

For manual `curl`, prefer:

```shell
curl -fsS \
  -H "Accept: application/json" \
  -H "Authorization: Bearer $CRAFT_API_KEY" \
  "$CRAFT_API_BASE_URL/documents"
```

If writing your own HTTP client, set a normal `User-Agent`. Python `urllib`'s default user-agent was blocked by Craft/Cloudflare with error 1010, while `curl` and the helper script's curl-like user-agent worked.

## Workflow

1. Probe `GET /connection` and confirm the expected space/timezone.
2. Discover targets with `GET /documents`, `GET /documents/search`, or `GET /blocks?id=<blockId>`.
3. Read before writing. Capture target block IDs and enough current content to roll back.
4. Make the smallest mutation that satisfies the request.
5. Read back the changed block, document, collection, or comment anchor.
6. Return the Craft app deeplink from `/connection.urlTemplates` or the MCP/tool output when available.

## Endpoint Map

Common read endpoints:

- `GET /connection`: space metadata and URL templates.
- `GET /documents`: documents exposed to the API connection.
- `GET /blocks?id=<id>&maxDepth=<n>`: block/document content.
- `GET /documents/search?include=<term>`: cross-document search.
- `GET /blocks/search?documentId=<id>&pattern=<regex>`: within-document search.
- `GET /collections`: collection discovery.
- `GET /collections/{collectionId}/schema`: schema for row validation.
- `GET /collections/{collectionId}/items`: collection rows.

Common write endpoints:

- `POST /blocks`: insert structured blocks or markdown at `pageId`/`siblingId`.
- `PUT /blocks`: update text/block fields.
- `PUT /blocks/move`: reorder or move blocks.
- `DELETE /blocks`: delete specified blocks.
- `POST /collections/{collectionId}/items`: add rows.
- `PUT /collections/{collectionId}/items`: update rows.
- `DELETE /collections/{collectionId}/items`: delete rows.
- `POST /comments`: add anchored comments. Treat as experimental and verify.
- `POST /upload`: upload and insert files. Treat as experimental and verify.

## Formatting Notes

- Markdown insertion is sensitive to newline shape. In shell commands, pass real newlines, not literal `\n` sequences. Read back the document and fix escaped `\n` artifacts.
- For multiple list items, insert them together with real single newlines. If updating a single existing list item to multiple items fails, insert the replacement list after a nearby sibling, then delete the old block.
- For code blocks, prefer structured API blocks with `type: "code"`, `rawCode`, and `language`. Markdown code fences may round-trip as inline code in some MCP paths.
- Craft-specific markdown tokens seen working: `<callout>...</callout>`, blockquotes, task lists, toggles, headings, nested lists, links, and washi separators through MCP styling.
- Inline highlights use Craft's named color set, not arbitrary hex. Known accepted names include `yellow`, `green`, `mint`, `cyan`, `blue`, `purple`, `pink`, `red`, `gray`, and gradient variants such as `gradient-blue`.
- Shell expansion can leak secrets into Craft if a payload is built with unescaped `$CRAFT_API_KEY` or `$CRAFT_API_BASE_URL`. Use single quotes, JSON arguments, or helper scripts so examples remain literal.
- API client defaults matter. Avoid default Python `urllib` headers; set a user agent explicitly.

## Collections

- Read schema before adding or updating rows.
- Select properties may reject new values unless the request explicitly allows creating options. Only use `allowNewSelectOptions` when the user intends to add new option values.
- Collection items can have page bodies. Use that for details while keeping row properties compact.
- Verify rows with `GET /collections/{collectionId}/items` after mutation.

## Safety

- Treat the API as production access to real Craft data.
- Safe tests: reads, creating clearly disposable content, or reversible writes with immediate verification.
- Avoid permanent deletes unless explicitly asked. If deleting test content, first confirm the target IDs were created by the current run.
- If an API response contradicts documentation, preserve the observed behavior in the task notes or skill update. Known drift: `Bearer` auth has worked where `x-craft-api-key` returned `401`.
