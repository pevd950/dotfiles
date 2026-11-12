# Craft MCP Plugin

The plugin is an MCP integration whose read and write tools take a CLI-like `command` string; there is no local `craft` binary.

## Finding the syntax

The tool descriptions list every command. For exact flags run `<entity> <action> --help`, and for block JSON shapes, Markdown precedence and limits run `blocks learn` (topics include `markdown`, `concepts`, `limitations`, `json`, and each block type). Read those instead of relying on a remembered command list.

Probe readiness with `connection info`, and confirm the expected space and timezone. On an internal error, expired authentication, the wrong space, a missing capability, or a repeated transient failure, switch to the direct HTTP API in `http-api.md`.

## Quirks verified here

- **Inside a task block.** Pass the task block's own ID as the page: `blocks add --id <taskBlockId> --position end ...` writes rows as the task's content. Move existing sibling rows inside with `blocks move --ids <rowIds> --targetId <taskBlockId> --position end`, then reset them to `indentationLevel` 0. `blocks add --siblingId <taskBlockId>` with an indentation level creates siblings, not content. Observed 2026-11-05.
- **Placement.** `blocks move` takes only `--position start|end` within a target page. To place a block next to another, add it with `--siblingId <blockId> --position before|after`. `tasks add --location document` put the new task at the top of the document (observed 2026-11-12); move it afterwards.
- **Links.** Resolve a Craft link first and use the returned `rootBlockId` for block operations; a URL document ID is not necessarily the writable root.
- **Markdown.** Pass real newline characters, not literal backslash-n text. Two leading spaces are one indentation level, and toggle children must be indented. `blocks update --markdown` can reset text style and indentation; for a wording-only edit keep them with `--json`.
- **Tables** are updated by sending the whole table as Markdown.
- **Search and lists.** `search --limit` accepts at most 20. `folders list --filter` takes a JavaScript regular expression, so inline flags such as `(?i)` fail. `tasks list --scope all` scans every task block in the space; it is not a union of the other scopes.
- **Collections.** Read the schema before writes and use exact property names; for item flags use display names from the live schema, and prefer one JSON array for bulk rows.
- **Dates.** Report resolved relative dates in `YYYY-MM-DD` form.
- **Styling** is a partial update, except that applying a theme may replace theme-owned styling. Read the page styling back after changes.
- **Files.** The file-picker tool is interactive. For unattended raw-byte uploads use the HTTP API.
- **Readback.** Read mutations back through the read tool. If that readback fails, verify through the API or report the write as unverified.
