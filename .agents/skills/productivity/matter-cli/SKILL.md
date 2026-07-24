---
name: matter-cli
description: Work with a Matter reading library through the local Matter CLI. Use when Codex needs to verify Matter access, inspect queue/inbox/archive items, summarize or synthesize Matter articles, clean up Matter tags, conservatively tag untagged items, compare Matter with Gmail/Substack/newsletters, create Todoist reading tasks from Matter queue items, or generate Matter app-opening iPhone links from Matter item ids.
---

# Matter CLI

## Core rules

- Default install path `$HOME/.matter/bin/matter`; fall back to `command -v matter`. Matter is accessed through this CLI — MCP/plugin discovery is irrelevant for library reads.
- Prove access with `matter account` before claiming Matter works. Connectivity errors like `Unable to connect. Is the computer able to access the url?` mean retry in a network-capable/escalated context before diagnosing auth failure.
- Keep changes conservative: do not move, archive, delete, retag, or mutate items unless the user asked for that exact operation.
- Preserve the `sent to kindle` tag — Matter applies it through its Kindle workflow; never remove or normalize it.

## Common reads

```bash
"$HOME/.matter/bin/matter" items list --status queue --order library_position --limit 20   # reading-list work
"$HOME/.matter/bin/matter" items list --status inbox --order inbox_position --limit 20    # incoming feed/newsletter work
"$HOME/.matter/bin/matter" search "query" --type items --limit 10
"$HOME/.matter/bin/matter" items get itm_abc123 --include markdown   # full text only when needed
```

## Tag work

- Page through tags until `has_more: false`; the first page is not the whole set.
- Expect rate limits during cleanup — pause and retry instead of dropping work.
- Obvious-only tagging: leave ambiguous feed placeholders, open threads, and weakly classifiable items unchanged.
- Canonical tag set (unless the user revises it): `software-engineering`, `frontend`, `ai`, `politics-society`, `work`, `reference`, `research-papers`, `health`, `lifestyle`, `product`, `philosophy`, `homelab`, `opinion`, plus untouched `sent to kindle`.
- Commands: `tags list --plain`, `tags add --item <id> <tag>`, `tags remove --item <id> <tag>`, `tags rename <old> <new>`.

## Matter app links

API item ids like `itm_8J1dX` are not the ids in Matter's routed deep links, and `matter:item:itm_...` only launches the app. To build an iPhone article link: strip the `itm_` prefix, decode the suffix as base62 (alphabet `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz`), and use `https://www.getmatter.com/d/entry/<numeric-content-id>`. Example: `itm_8J1dX` → `122745215` → `https://www.getmatter.com/d/entry/122745215`.

Use the helper for deterministic conversion, resolved relative to this SKILL.md:

```bash
python3 "$SKILL_DIR/scripts/matter_link.py" itm_8J1dX
```

## Todoist reading tasks

One task per article, with:

- The Matter app link in the visible title: `Read: [<article title>](https://www.getmatter.com/d/entry/<numeric-content-id>)`
- Description lines: `matter:item:<id>` (dedupe key), `Matter content id: <numeric-content-id>`, and `Source URL: <original url>`.
- The `read` Todoist label only — no `matter` label. Preserve existing due date/priority choices unless asked to change them.

## Automation

The durable automation lives at `${CODEX_HOME:-$HOME/.codex}/automations/matter-reading-queue/` (`automation.toml`, `memory.md`). After editing it, validate the TOML with `python3 -c 'import tomllib, pathlib; tomllib.loads(pathlib.Path("<path>/automation.toml").read_text())'`.
