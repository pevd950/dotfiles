---
name: craft
description: Use Craft through the Craft MCP plugin or direct HTTP API for reading, searching, creating, updating, moving, styling, uploading, and organizing Craft documents, blocks, collections, daily notes, and task blocks. Use whenever a request involves Craft, a Craft link, or saving durable notes in Craft.
---

# Craft

Use one workflow across two interchangeable transports: the Craft MCP plugin and Craft's direct HTTP API. Prefer the plugin when it is exposed and healthy; use the API as a complete fallback. Treat both as production access to private user data.

## Transport selection

1. Inspect the current session's tool inventory. Configuration or a remembered plugin installation does not prove the Craft plugin is callable.
2. When the Craft plugin is exposed, probe it with the read tool's `connection info` command. Confirm the expected space and timezone before relying on it.
3. Classify failures accurately. Internal errors, expired authentication, wrong-space connections, missing write tools, or headless-host limitations are reasons to use the direct API.
4. For the API path, read `references/http-api.md` and probe:

   ```shell
   SKILL_DIR="<directory-containing-this-SKILL.md>"
   python3 "$SKILL_DIR/scripts/craft_api.py" GET /connection
   ```

5. Use desktop or browser interaction only when neither programmatic path supports the required operation or the authenticated UI is itself the source of truth.

The plugin uses MCP tools with a command-style `command` argument. It is not a local `craft` executable. Read `references/plugin-mcp.md` for its command surface.

## Common workflow

Apply these rules regardless of transport:

1. Verify the connection, expected space, and timezone.
2. Discover the correct destination before writing. Prefer an explicit private link or configured destination; otherwise inspect folders and search by exact title.
3. Resolve Craft links before block operations. A URL document ID, document record, page block, and writable root may differ.
4. Read before writing. Capture the target IDs, surrounding content, schema when relevant, and enough state to undo the change.
5. Avoid duplicates. Search for the exact intended document, nested-page, collection-item, or dated-section title before creating it.
6. Use native structure. Create structured page blocks for nested pages; markdown headings alone do not create pages that accept child blocks.
7. Make the smallest authorized mutation, then read the changed object back before reporting success.
8. Create directly in the correct folder or document instead of leaving cleanup in an unsorted location.
9. Return private Craft deeplinks as descriptive Markdown links. Never paste raw private links into public GitHub content, tracked files, or other public systems.

## Rich documents

Keep root pages glanceable. Use native callouts, tables, toggles, pages, and collections where the content benefits; move repeated detail into item bodies or nested pages.

Read `references/formatting.md` before creating or substantially restructuring a polished user-facing document.

## Files and images

Before attaching a generated or local file to Craft:

1. Apply the user's durable-file location and naming policy before upload.
2. Confirm the final file is available in that location.
3. Do not attach temporary, chat-pasteboard, localhost, `file://`, or disposable build paths as durable references.
4. Use the real MIME type and verify the readback is the intended visible image or file block.

The plugin's file-picker tool is interactive. The API supports raw-byte uploads and is appropriate for unattended work; see `references/http-api.md`.

## Daily notes and collections

- A date-titled regular document is not a native Daily Note. Use the transport's Daily Note/date position and verify by date.
- Read a collection's schema before row writes. Preserve existing property keys and every field when an operation replaces the full schema.
- Keep collection properties compact and filterable; put long narrative detail in the item page body.
- Treat collection-item deletion as destructive because it also removes the item's content.

## Craft task blocks

This skill explains how to operate Craft task blocks, not which task system should own a commitment. Resolve that choice from the current request, user/repository instructions, or the provider-neutral `task-management` skill. When Craft is selected, confirm the intended location, preserve scheduling/repeat state on updates, and read the task back after mutation.

## Safety

Reads and reversible, clearly authorized writes with immediate verification are normally safe. Confirm before destructive changes, permanent deletion, publication, permission changes, or writes outside the requested scope. Never log API keys, private links, personal identifiers, space IDs, or private document contents unnecessarily.

When observed behavior contradicts this skill, preserve a sanitized reproduction and update the relevant transport reference rather than creating a second Craft skill.
