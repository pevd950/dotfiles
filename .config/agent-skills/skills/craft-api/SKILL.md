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
2. Discover locations with `GET /folders` when placement matters, then discover targets with `GET /documents`, `GET /documents/search`, or `GET /blocks?id=<blockId>`.
3. Read before writing. Capture target block IDs, document IDs, folder IDs, collection schema, and enough current content to roll back.
4. Make the smallest mutation that satisfies the request.
5. Read back the changed block, document, folder listing, collection, task, or comment anchor.
6. Return the Craft app deeplink from `/connection.urlTemplates`, `clickableLink`, or the MCP/tool output when available.

## Endpoint Map

Common read endpoints:

- `GET /connection`: space metadata and URL templates.
- `GET /folders`: built-in locations plus user folders and document counts.
- `GET /documents`: documents exposed to the API connection. Prefer `location`, `folderId`, date filters, and `fetchMetadata=true` over unbounded all-document listings when possible.
- `GET /blocks?id=<id>&maxDepth=<n>` or `GET /blocks?date=today`: block/document/daily-note content. Add `fetchMetadata=true` when authorship or modification times matter. Use `--accept text/markdown` when rendered markdown is more useful than structured JSON.
- `GET /documents/search?include=<term>`: cross-document search. Supports `include`, `regexps`, `documentIds`, `location`, `folderIds`, date filters, and `fetchBlocks=true`.
- `GET /blocks/search?blockId=<id>&pattern=<regex>`: within-document or within-page search. Use `blockId`, not `documentId`.
- `GET /collections`: collection discovery.
- `GET /collections/{collectionId}/schema`: schema for row validation. `format=schema` returns editable schema; default `json-schema-items` helps validate item payloads.
- `GET /collections/{collectionId}/items`: collection rows. Use `maxDepth=0` when only properties are needed.
- `GET /tasks?scope=<active|upcoming|inbox|logbook|document>`: tasks across the space. `scope=document` requires `documentId`.
- `GET /whiteboards/{whiteboardBlockId}/elements`: experimental Excalidraw-style whiteboard data.

Common write endpoints:

- `POST /documents`: create page shells with `{"documents":[{"title":"..."}]}` and optional `destination`.
- `PUT /documents/move`: move or restore documents between folders, unsorted, and templates. Daily notes cannot be moved.
- `DELETE /documents`: soft-delete documents to trash. Restore with `PUT /documents/move`.
- `POST /folders`, `PUT /folders/move`, `DELETE /folders`: manage folder hierarchy. Deleting folders moves contained documents/subfolders up, not permanently away.
- `POST /blocks`: insert structured blocks or markdown at `pageId`/`siblingId`.
- `PUT /blocks`: update text/block fields.
- `PUT /blocks/move`: reorder or move blocks.
- `DELETE /blocks`: delete specified blocks.
- `POST /tasks`: add tasks to inbox, daily notes, or documents.
- `PUT /tasks`: update task markdown, state, schedule/deadline dates, or location.
- `DELETE /tasks`: delete tasks.
- `POST /collections`: create collections. Experimental; verify shape immediately.
- `PUT /collections/{collectionId}/schema`: replace collection schema. Preserve existing property keys for fields to keep.
- `POST /collections/{collectionId}/items`: add rows.
- `PUT /collections/{collectionId}/items`: update rows.
- `DELETE /collections/{collectionId}/items`: delete rows.
- `POST /comments`: add anchored comments. Treat as experimental and verify.
- `POST /upload`: upload and insert files. Requires raw bytes plus query `position` and `pageId`, `date`, or `siblingId`; treat as experimental and verify.
- `POST /whiteboards`, `POST|PUT|DELETE /whiteboards/{whiteboardBlockId}/elements`: create and edit whiteboards. Experimental; verify with read-back.

## Documents, Folders, and Placement

- Document IDs are root block IDs. Use a document ID with `GET /blocks?id=<documentId>` to fetch document content.
- Locations are either built-ins (`unsorted`, `templates`, `trash`, `daily_notes` for listing/searching) or folder IDs from `GET /folders`.
- For new durable notes, create the page shell with `POST /documents`, then insert body blocks with `POST /blocks` at `position:{pageId:"...",position:"end"}`. Verify with `GET /blocks`.
- When placement matters, list folders first and create directly into the right destination instead of creating in `unsorted` and leaving cleanup to the user.
- When moving documents, use `destination:{folderId:"..."}` or `destination:{destination:"unsorted"|"templates"}`. Use delete only for a deliberate soft-delete to trash.

## Search

- Use `GET /documents/search` first for broad discovery. Add `fetchBlocks=true` when the matching block IDs or styling are needed.
- Use `GET /blocks/search` after identifying a target document or nested page and pass `blockId=<root-or-page-id>`.
- For local context around a match, use `beforeBlockCount`, `afterBlockCount`, and `fetchBlocks=true`.
- Search patterns are RE2-compatible. Avoid unsupported PCRE-only constructs, and keep regexes narrow against personal data.
- Search and listing filters are mutually exclusive in a few combinations: `documentIds` cannot be used with `location` or `folderIds`; `location` cannot be used with `folderId`/`folderIds`.
- Date filters accept ISO dates and relative dates like `today`, `tomorrow`, and `yesterday`; resolve user-facing dates explicitly when reporting results.

## Daily Notes

Use Craft's native daily-note surface for date-based notes. A document titled like
`2026.05.30` is only a regular document and will not appear as that day's Craft
Daily Note.

Read today's native daily note with:

```shell
python3 "$SKILL_DIR/scripts/craft_api.py" GET /blocks --query date=today --query maxDepth=3
```

If Craft returns `NOT_FOUND_ERROR` for the daily note, create it by inserting
content at a date position, not by creating a document:

```shell
python3 "$SKILL_DIR/scripts/craft_api.py" POST /blocks \
  --json '{"position":{"date":"today","position":"end"},"markdown":"# Daily Command Center\n\n## Scratchpad"}'
```

For a specific day, use the ISO date string in the position and read query, such
as `date=2026-05-30`. After creation, verify with `GET /blocks?date=<date>`;
do not rely on `GET /documents/search` as proof that a native daily note exists.

## Formatting Notes

- Markdown insertion is sensitive to newline shape. In shell commands, pass real newlines, not literal `\n` sequences. Read back the document and fix escaped `\n` artifacts.
- For multiple list items, insert them together with real single newlines. If updating a single existing list item to multiple items fails, insert the replacement list after a nearby sibling, then delete the old block.
- For code blocks, prefer structured API blocks with `type: "code"`, `rawCode`, and `language`. Markdown code fences may round-trip as inline code in some MCP paths.
- Craft-specific markdown tokens from the API docs include `<page>`, `<card>`, `<pageTitle>`, `<content>`, `<callout>`, `<caption>`, `<highlight color="...">`, `==yellow highlight==`, `<comment id="...">`, `$inline math$`, `$$block math$$`, `[text](block://blockId)`, and `[text](date://YYYY-MM-DD)`.
- Two leading spaces represent one Craft indentation level. Preserve indentation when editing nested lists and nested pages.
- Collection tags such as `<collection>`, `<collectionItem>`, `<property>`, `<contentPreview>`, and `<itemsPreview>` are output-only. Do not send them as input.
- Inline highlights use Craft's named color set, not arbitrary hex. Known accepted names include `yellow`, `green`, `mint`, `cyan`, `blue`, `purple`, `pink`, `red`, `gray`, and gradient variants such as `gradient-blue`, `gradient-purple`, `gradient-red`, `gradient-yellow`, and `gradient-brown`.
- Shell expansion can leak secrets into Craft if a payload is built with unescaped `$CRAFT_API_KEY` or `$CRAFT_API_BASE_URL`. Use single quotes, JSON arguments, or helper scripts so examples remain literal.
- API client defaults matter. Avoid default Python `urllib` headers; set a user agent explicitly.

## Images and Attachments

- Local paths and `file://` URLs are not durable inside Craft documents. Do not leave transient pasteboard paths as the only image record.
- For API upload, use raw bytes, not JSON. Example:

```shell
python3 "$SKILL_DIR/scripts/craft_api.py" POST /upload \
  --query position=end \
  --query pageId="$CRAFT_PAGE_ID" \
  --body-file ./image.png \
  --content-type application/octet-stream
```

- Craft image blocks need a resolved Craft-accessible URL. In MCP paths, `file://` or localhost image URLs can fail with misleading "Document not found" errors; treat that as an unsupported image insertion path, not necessarily a missing document.
- If the source image came from a Codex chat and the original pasteboard file has expired, recover `input_image` payloads from the relevant Codex session JSONL structurally with a JSON parser, decode `data:image/...;base64,...`, and save stable local copies before trying to insert them elsewhere.
- When the Craft desktop app is available, a reliable fallback is to copy the bitmap data itself to the clipboard, not the file list, then paste into the open Craft document. On macOS, `osascript` can set the clipboard to `(read (POSIX file "<image path>") as JPEG picture)`.
- Verify image insertion by reading the document back and confirming blocks of `type: "image"` with `https://r.craft.do/...` URLs. Remove accidental generic `type: "file"` blocks created by pasting a file list instead of image data.

## Collections

- Read schema before adding or updating rows.
- For item writes, prefer the default `GET /collections/{collectionId}/schema` JSON Schema over docs examples. Observed live behavior may require the collection content-property key directly, such as `capability`, plus a `properties` object, instead of a generic `title` field.
- Use semantically correct collection property types when supported. Observed live behavior accepts `url` properties for link fields; do not degrade links to `text` unless schema creation rejects `url` or the field intentionally needs arbitrary prose.
- For schema updates, include every field that should remain and keep existing `key` values stable. The update endpoint replaces the schema, not just the listed fields.
- Select properties may reject new values unless the request explicitly allows creating options. Only use `allowNewSelectOptions` when the user intends to add new option values.
- Two-way relations are synced automatically in the background. Set only one side for consistency.
- Collection items can have page bodies. Use that for details while keeping row properties compact.
- Deleting collection items also deletes content inside those items. Treat item deletion as destructive unless the items are clearly disposable or the user explicitly asked.
- Verify rows with `GET /collections/{collectionId}/items` after mutation.

## Tasks

- Craft task APIs are separate from document block insertion. Use them when the user explicitly wants Craft tasks or when preserving Craft-native task metadata matters.
- Scopes: `inbox`, `active`, `upcoming`, `logbook`, and `document`. Use `documentId` with `scope=document`.
- Task locations for writes are `{"type":"inbox"}`, `{"type":"dailyNote","date":"today"}`, or `{"type":"document","documentId":"..."}`.
- Task info can include `state`, `scheduleDate`, and `deadlineDate`. Marking inbox tasks done or canceled may move them to logbook.
- This user normally uses Todoist for active tasks and commitments. Do not create Craft tasks as a replacement for Todoist unless Craft is specifically requested or is the natural home for document-local checklist items.

## Whiteboards

- Whiteboards use Excalidraw-like element JSON and are experimental. Create an empty whiteboard with `POST /whiteboards`, then append elements with `POST /whiteboards/{whiteboardBlockId}/elements`.
- Read existing elements before modifying or deleting them, and keep element IDs stable when updating.

## Safety

- Treat the API as production access to real Craft data.
- Safe tests: reads, creating clearly disposable content, or reversible writes with immediate verification.
- Avoid permanent deletes unless explicitly asked. If deleting test content, first confirm the target IDs were created by the current run.
- If an API response contradicts documentation, preserve the observed behavior in the task notes or skill update. Known drift: `Bearer` auth has worked where `x-craft-api-key` returned `401`.
