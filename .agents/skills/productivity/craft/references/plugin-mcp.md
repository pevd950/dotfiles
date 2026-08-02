# Craft MCP Plugin

The Craft plugin is an MCP integration. Its read and write tools accept a CLI-like `command` string, but there is no requirement for a local `craft` binary. Use the plugin through the MCP tools exposed in the current session.

## Readiness

1. Confirm the Craft plugin tools are present in the current tool inventory.
2. Probe the read tool with `connection info`.
3. Confirm the expected space and timezone.
4. On an internal error, expired authentication, wrong space, missing capability, or repeated transient failure, switch to the direct HTTP API in `http-api.md`.

Do not treat a configured MCP URL or installed plugin record as proof the tools are callable.

## Read commands

The plugin read tool supports command strings such as:

- `connection info`
- `folders list [--filter <regex>]`
- `documents list [--location <location> | --folder <folderId>]`
- `documents resolve-link <url>`
- `search <query> [--location <location>]`
- `blocks get <rootBlockId> [--depth <depth>] [--format json|markdown]`
- `blocks get --date today`
- `tasks list [--scope active|upcoming|inbox|logbook|document|all]`
- `collections list [--document <rootBlockId>]`
- `collections schema --collection <collectionId>`
- `collections items-get --collection <collectionId>`
- `collections views-list --collection <collectionId>`
- `whiteboards elements get --whiteboard <whiteboardId>`
- `images view --url <image-url>`

Batch independent reads with semicolons when the tool supports it. Use `--help` on the narrow entity/action when the live schema may have changed.

## Write commands

The plugin write tool supports command strings such as:

- `folders create --name <name> [--parent <folderId>] [--icon <emoji>]`
- `documents create --title <title> [--destination unsorted|templates | --folder <folderId>]`
- `blocks add --id <pageId> --markdown <text> [--position start|end]`
- `blocks add --siblingId <blockId> --markdown <text> [--position before|after]`
- `blocks update --id <blockId> --markdown <text>`
- `blocks move --id <blockId> --targetId <pageId> [--position start|end]`
- `blocks delete --id <blockId>`
- `tasks add|update|delete ...`
- `collections create|rename ...`
- `collections items-add|items-update|items-delete ...`
- `collections views-create|views-update|views-delete|views-set-active ...`
- `comments add --comments <json>`
- `whiteboards create ...` and `whiteboards elements add|update|delete ...`

Use the interactive file-picker tool when the user needs to select or drag a local file. For unattended raw-byte uploads, use the HTTP API.

## Mechanics and pitfalls

- Resolve a Craft link first and use the returned `rootBlockId` for block operations; a URL document ID is not necessarily the writable root.
- Pass actual newline characters in markdown, not literal backslash-n text.
- Two leading spaces represent one Craft indentation level. Toggle children must be indented.
- Read collection schemas before writes and use exact property names.
- Use explicit dates in `YYYY-MM-DD` form when reporting resolved relative dates.
- Read back every mutation through the plugin read tool. If readback fails, do not claim the write landed; verify through the API or report it as unverified.
