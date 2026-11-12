---
name: craft
description: Write and organize Craft documents, plans, notes and task blocks the way the user would, through the Craft MCP plugin or the direct HTTP API. Use whenever a request involves Craft, a Craft link, a plan or workboard kept in Craft, or saving durable notes there.
---

# Craft

## Writing in Craft

Write what the user would jot down, in the structure Craft provides. This applies to every plan, note and update, not only when a polished page is requested.

- **Store the state, not the story.** Record what is true now, what was decided and what happens next. Leave out how the work went and what you checked; link the evidence.
- **One idea per block, a line or two each.** A paragraph longer than a few lines goes in a nested page or a toggle, or is left out.
- **Status first.** The top of a document says where things stand in a line or two. Current work comes before finished work.
- **Anything to be done is a task block** with a short imperative title, and every step of a plan is one. Its context, evidence and sub-steps go inside the task block as its own content, with a child task per part. The user reads tasks from the phone's task view, which shows only the task block and what is inside it, so indented siblings after the task do not appear there. Schedule a task for the day it will be worked; give child tasks the same date when they should show in the daily view. Tick it with the date and a one-line result.
- **Detail and history collapse.** Reference detail goes in a toggle or nested page with a clear title. Session reports and logs are one line per entry inside a collapsed History toggle or nested page, newest first.
- **Update in place.** When a fact changes, change the block that states it.
- **Use the native block for the job:** headings for sections, tables for comparisons and lists of like items, a callout for the one thing to read first, toggles for detail, nested pages for long material, collections when rows need typed properties.
- **Links are labeled,** and tags follow private routing, such as a plan's status tag.

Which system owns a commitment is the `task-management` skill's question; when Craft holds the task, preserve its schedule and repeat state on updates. Block choices and Markdown quirks are in `references/formatting.md`.

## Transport

Two interchangeable transports: the Craft MCP plugin and Craft's direct HTTP API.

1. Use the plugin when its tools are in this session's tool inventory and the read tool's `connection info` shows the expected space and timezone. A configured or remembered plugin is not proof it is callable.
2. Use the API when the plugin errors, has expired authentication, is connected to the wrong space, lacks a write tool, or the host is headless. Read `references/http-api.md` and probe:

   ```shell
   SKILL_DIR="<directory-containing-this-SKILL.md>"
   python3 "$SKILL_DIR/scripts/craft_api.py" GET /connection
   ```

3. Use the desktop app or a browser only when neither path supports the operation or the authenticated UI is itself the source of truth.

The plugin's tools take a command string; it is not a local `craft` executable. `--help` on any command and `blocks learn <topic>` document the syntax. `references/plugin-mcp.md` holds only the quirks verified here.

## Workflow

1. Find the destination before writing: an explicit link or configured destination, otherwise folders and an exact-title search. Reuse a matching document, nested page, collection item or dated section.
2. Resolve a Craft link before block operations. A URL document ID, document record, page block and writable root can differ.
3. Read before writing: target IDs, surrounding content, schema where relevant, and enough state to undo the change.
4. Create a nested page as a structured page block; a Markdown heading does not create a page that accepts child blocks.
5. Make the smallest change, directly in the right folder or document, then read it back before reporting.
6. Return descriptive, verified document or block links, native mobile links where supported.

## Files and images

Attach the final copy saved under the user's durable-file policy; temporary, chat-pasteboard, localhost, `file://`, and disposable build paths do not last as references. Use the real MIME type and verify the readback is the intended visible image or file block.

The plugin's file-picker tool is interactive. The API supports raw-byte uploads and is appropriate for unattended work; see `references/http-api.md`.

## Daily notes and collections

- Make daily views easy to scan: distinguish actions, waiting, optional work, and done items where useful. Keep standing guidance as reference, not tasks.
- Record material outcomes with timestamps and verified links in the existing note. Link to canonical tasks instead of copying them.
- A date-titled regular document is not a native Daily Note. Use the transport's Daily Note/date position and verify by date.
- Read a collection's schema before row writes. Preserve existing property keys and every field when an operation replaces the full schema.
- Keep collection properties compact and filterable; put long narrative detail in the item page body.
- Deleting a collection item also removes its content; treat it as destructive.

## Drift

When observed behavior contradicts this skill, preserve a sanitized reproduction and update the relevant transport reference rather than creating a second Craft skill.
