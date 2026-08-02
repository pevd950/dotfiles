# Direct HTTP API

This is the complete standalone path for working with Craft when the Craft MCP plugin is unavailable, unhealthy, connected to the wrong space, or impractical on a headless host. An agent using this reference must be able to complete real Craft work without relying on plugin commands. Treat it as production access to real Craft data.

## Environment and auth

Required local-only variables (from a host-local ignored secrets file or shell startup — ask the user to add them if missing; do not assume a specific path): `CRAFT_API_BASE_URL` (ends in `/api/v1`), `CRAFT_API_KEY`, and optional `CRAFT_FORMATTING_SAMPLE_URL` (private live formatting sample). Never write API keys, private Craft links, user-specific paths, or space IDs into tracked files, PR bodies, Craft demo pages, or logs.

Use the bundled helper for routine calls — it centralizes auth, avoids printing secrets, requires an HTTPS base URL without userinfo, and follows only strictly same-origin redirects. Set `SKILL_DIR` to the directory containing the parent `SKILL.md`, not this `references/` directory. Other skills needing Craft API access should call this helper instead of reimplementing HTTP:

```shell
python3 "$SKILL_DIR/scripts/craft_api.py" GET /connection
```

Known drift: `Authorization: Bearer $CRAFT_API_KEY` has worked where `x-craft-api-key` returned 401 — try bearer first, keep the header as fallback. For manual curl: `curl -fsS -H "Accept: application/json" -H "Authorization: Bearer $CRAFT_API_KEY" "$CRAFT_API_BASE_URL/documents"`. Custom clients must set a normal `User-Agent`; Python `urllib`'s default is blocked by Craft/Cloudflare (error 1010). Beware shell expansion leaking `$CRAFT_API_KEY` into payloads — use single quotes, JSON arguments, or the helper.

## Workflow

1. Probe `GET /connection`; confirm the expected space and timezone.
2. Discover placement (`GET /folders`) and targets (`GET /documents`, `/documents/search`, `/blocks?id=...`).
3. Read before writing: capture block/document/folder/collection IDs and enough current content to roll back.
4. Resolve the writable root before body writes. Returned deeplinks, `documentLink`, `clickableLink`, document IDs, and page-block IDs are locators, not proof of a writable block: after `POST /documents`, read the candidate with `GET /blocks?id=<candidate>`; if the read fails or reveals a wrapper/link, resolve it before inserting. For nested pages use a structured `type:"page"` block — markdown headings do not create pages that accept child blocks.
5. Make the smallest mutation, then read back the changed object before notifying or handing off. When placement matters, create directly into the right folder instead of leaving cleanup in `unsorted`.
6. Return Craft deeplinks as labeled Markdown links (`[Release notes](craftdocs://open?...)`) — no raw `craftdocs://` strings in GitHub, Todoist, Craft notes, or reports unless explicitly requested.

## Endpoint map

Reads:

- `GET /connection` — space metadata and URL templates.
- `GET /folders` — built-in locations plus user folders and document counts.
- `GET /documents` — prefer `location`, `folderId`, date filters, and `fetchMetadata=true` over unbounded listings.
- `GET /blocks?id=<id>&maxDepth=<n>` or `?date=today` — content; `fetchMetadata=true` for authorship/modification times; `--accept text/markdown` when rendered markdown beats structured JSON. Document IDs are root block IDs.
- `GET /documents/search?include=<term>` — cross-document; supports `regexps`, `documentIds`, `location`, `folderIds`, date filters, `fetchBlocks=true`.
- `GET /blocks/search?blockId=<id>&pattern=<regex>` — within a document or page; takes `blockId`, not `documentId`; `beforeBlockCount`/`afterBlockCount` for context. Patterns are RE2; keep them narrow against personal data.
- `GET /collections`; `GET /collections/{id}/schema` (`format=schema` returns the editable form); `GET /collections/{id}/items` (`maxDepth=0` for properties only).
- `GET /tasks?scope=<active|upcoming|inbox|logbook|document>` — `document` requires `documentId`.
- `GET /whiteboards/{whiteboardBlockId}/elements` — experimental Excalidraw-style data.

Writes:

- `POST /documents` (`{"documents":[{"title":"..."}]}` + optional `destination`); `PUT /documents/move` (moves/restores between folders, `unsorted`, `templates`; daily notes cannot move); `DELETE /documents` (soft-delete to trash).
- `POST /folders`, `PUT /folders/move`, `DELETE /folders` — folder deletion moves contents up, not away.
- `POST /blocks` (insert structured blocks or markdown at `pageId`/`siblingId`); `PUT /blocks`; `PUT /blocks/move`; `DELETE /blocks`.
- `POST|PUT|DELETE /tasks` — locations `{"type":"inbox"}`, `{"type":"dailyNote","date":"today"}`, `{"type":"document","documentId":"..."}`; info may include `state`, `scheduleDate`, `deadlineDate`; completing inbox tasks may move them to logbook.
- `POST /collections` (experimental — verify immediately); `PUT /collections/{id}/schema` (replaces the whole schema: include every field to keep and preserve existing `key` values); `POST|PUT|DELETE /collections/{id}/items`.
- `POST /comments`, `POST /upload` (raw bytes plus query `position` and `pageId`/`date`/`siblingId`), whiteboard writes — experimental; verify with read-back.

Filter exclusivity: `documentIds` cannot combine with `location`/`folderIds`; `location` cannot combine with `folderId`/`folderIds`. Date filters accept ISO dates and `today`/`tomorrow`/`yesterday` — resolve user-facing dates explicitly when reporting.

## Daily notes

A document titled like `2026.05.30` is a regular document, not that day's Daily Note. Read with `GET /blocks --query date=today --query maxDepth=3`. On `NOT_FOUND_ERROR`, create by inserting at a date position — `POST /blocks` with `{"position":{"date":"today","position":"end"},"markdown":"..."}` — never by creating a document. Verify with `GET /blocks?date=<date>`; a `/documents/search` hit is not proof a native daily note exists.

## Collections

Read the schema before row writes. Live behavior may require the collection's content-property key directly (such as `capability`) plus a `properties` object, rather than a generic `title`. Use semantically correct property types (`url` for links; don't degrade to `text` unless schema creation rejects `url`). Use `allowNewSelectOptions` only when new option values are intended. Two-way relations sync automatically — set only one side. Collection items can have page bodies; use them for detail while keeping row properties compact. Item deletion also deletes that content — treat as destructive. Verify rows after mutation.

## Images and uploads

Upload raw bytes with the real MIME type (`--body-file ./image.png --content-type image/png`); generic `application/octet-stream` creates a `file` block instead of a visible `image` block. Verify read-back shows `type: "image"` with `https://r.craft.do/...` URLs; if not, retry the same bytes with the correct MIME type, then remove the accidental file block. Local paths and `file://` URLs are not durable in Craft, and MCP-path `file://`/localhost image URLs can fail with a misleading "Document not found". To recover images from expired Codex chat pasteboards, decode `input_image` base64 payloads from the session JSONL structurally and save stable local copies. Desktop fallback: put bitmap data (not the file list) on the clipboard — `osascript` can set it to `(read (POSIX file "<path>") as JPEG picture)` — and paste into the open document.

## Formatting

For polished, rich, or highly scannable documents, read `references/formatting.md` first (layout patterns, block choices, styling, and the API/MCP markdown mechanics: newline shape, tokens, toggles, highlights, indentation). If `CRAFT_FORMATTING_SAMPLE_URL` is set and live access exists, inspect that private sample for structure without copying private content or storing the URL in shared files.

## Tasks note

Todoist owns active tasks and commitments. Create Craft tasks only when Craft is specifically requested or is the natural home for document-local checklist items.

## Safety

Safe by default: reads, clearly disposable content, and reversible writes with immediate verification. Avoid permanent deletes unless explicitly asked; before deleting test content, confirm the target IDs were created by the current run. When a response contradicts documentation, preserve the observed behavior in task notes or a skill update.
