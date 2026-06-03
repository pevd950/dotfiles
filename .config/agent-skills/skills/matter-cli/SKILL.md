---
name: matter-cli
description: Work with a Matter reading library through the local Matter CLI. Use when Codex needs to verify Matter access, inspect queue/inbox/archive items, summarize or synthesize Matter articles, clean up Matter tags, conservatively tag untagged items, compare Matter with Gmail/Substack/newsletters, create Todoist reading tasks from Matter queue items, or generate Matter app-opening iPhone links from Matter item ids.
---

# Matter CLI

## Core Rules

- Use the local CLI directly. The default install path is `$HOME/.matter/bin/matter`; if it is unavailable, check `command -v matter`.
- Prove access with a live read before claiming Matter works: `matter account` is the lightweight auth/reachability check.
- Treat `codex mcp list` and plugin discovery as irrelevant for Matter library reads; Matter is accessed through the CLI.
- If a Matter CLI command fails with connectivity text such as `Unable to connect. Is the computer able to access the url?`, retry in a network-capable/escalated context before diagnosing auth failure.
- Keep changes conservative. Do not move, archive, delete, retag, or mutate Matter items unless the user asked for that exact operation.
- Preserve the `sent to kindle` tag. Matter applies it through its Kindle workflow, so do not remove or normalize it.

## Common Reads

Use queue order for reading-list work:

```bash
"$HOME/.matter/bin/matter" items list --status queue --order library_position --limit 20
```

Use inbox order for incoming feed/newsletter work:

```bash
"$HOME/.matter/bin/matter" items list --status inbox --order inbox_position --limit 20
```

Use search before pulling full article bodies:

```bash
"$HOME/.matter/bin/matter" search "query" --type items --limit 10
```

Pull full article text only when needed for summarization, classification, or synthesis:

```bash
"$HOME/.matter/bin/matter" items get itm_abc123 --include markdown
```

## Tag Work

- Page through tags until `has_more: false`; do not assume the first page is complete.
- Expect rate limits during tag cleanup. Pause and retry instead of dropping work.
- Prefer obvious-only tagging. Leave ambiguous feed placeholders, open threads, or weakly classifiable items unchanged.
- Use the established canonical tag set unless the user asks to revise it:
  `software-engineering`, `frontend`, `ai`, `politics-society`, `work`, `reference`, `research-papers`, `health`, `lifestyle`, `product`, `philosophy`, `homelab`, `opinion`, plus untouched `sent to kindle`.

Useful commands:

```bash
"$HOME/.matter/bin/matter" tags list --plain
"$HOME/.matter/bin/matter" tags add --item itm_abc123 ai
"$HOME/.matter/bin/matter" tags remove --item itm_abc123 old-tag
"$HOME/.matter/bin/matter" tags rename old-tag new-tag
```

## Matter App Links

Matter API item ids such as `itm_8J1dX` are not the ids used by Matter's routed app/web deep links. `matter:item:itm_...` only launches the app and does not navigate to the article.

To create an iPhone app-opening article link:

1. Remove the `itm_` prefix.
2. Decode the remaining suffix as base62 using alphabet `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`.
3. Use `https://www.getmatter.com/d/entry/<numeric-content-id>`.

Example:

```text
itm_8J1dX -> 122745215 -> https://www.getmatter.com/d/entry/122745215
```

Use `scripts/matter_link.py` for deterministic conversion:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/matter-cli/scripts/matter_link.py" itm_8J1dX
```

## Todoist Reading Tasks

When surfacing Matter queue items into Todoist:

- Create one task per article.
- Put the Matter app link in the visible task title, not only in the body:
  `Read: [<article title>](https://www.getmatter.com/d/entry/<numeric-content-id>)`
- Include `matter:item:<id>` in the description for dedupe.
- Include `Matter content id: <numeric-content-id>`.
- Include the original source URL separately as `Source URL`.
- Apply the `read` Todoist label only. Do not add a `matter` label; the visible Matter link and `matter:item:<id>` description line are enough source provenance. Preserve existing due date/priority choices unless the user asks to change them.

## Automation Notes

The durable automation for this workflow lives at:

```text
${CODEX_HOME:-$HOME/.codex}/automations/matter-reading-queue/automation.toml
${CODEX_HOME:-$HOME/.codex}/automations/matter-reading-queue/memory.md
```

When editing that automation, validate the TOML after changes:

```bash
python3 -c 'import os, pathlib, tomllib; codex_home = pathlib.Path(os.environ.get("CODEX_HOME", pathlib.Path.home() / ".codex")); tomllib.loads((codex_home / "automations/matter-reading-queue/automation.toml").read_text()); print("automation toml ok")'
```
