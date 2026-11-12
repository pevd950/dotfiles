---
name: matter-reading
description: "Pablo's conventions for his Matter reading library: the tag set, the Kindle tag, article links that open the Matter app on iPhone, and Todoist reading tasks. Use with the Matter connector when tagging or cleaning up Matter items, linking a Matter article, or creating reading tasks from the queue."
---

# Matter reading

Reach Matter through the session's Matter connector (in Codex its tools sit under `mcp__codex_apps__matter`). It previews a change and then applies it: apply the changes the request covers and read them back. The queue is the reading list; the inbox is incoming feeds and newsletters.

## Tags

- Canonical set, unless the user revises it: `software-engineering`, `frontend`, `ai`, `politics-society`, `work`, `reference`, `research-papers`, `health`, `lifestyle`, `product`, `philosophy`, `homelab`, `opinion`.
- Leave the `sent to kindle` tag exactly as it is. Matter applies it through its Kindle workflow.
- Tag only what is obvious. Leave ambiguous feed placeholders, open threads and weakly classifiable items unchanged.
- Page through the tag list until it reports no more; the first page is not the whole set. During a cleanup, pause and retry on rate limits so no item is skipped.

## Article links

An API item id such as `itm_8J1dX` is not the id in Matter's app links, and `matter:item:itm_...` only launches the app. To link an article so it opens in Matter on iPhone, strip the `itm_` prefix, decode the rest as base62 (alphabet `0-9A-Za-z` in that order), and use `https://www.getmatter.com/d/entry/<numeric-content-id>`. Example: `itm_8J1dX` gives `122745215`.

The helper does the conversion, resolved relative to this file:

```bash
python3 "$SKILL_DIR/scripts/matter_link.py" itm_8J1dX
```

## Todoist reading tasks

One task per article:

- Title: `Read: <article title>`.
- Description, one item per line: `[Open in Matter](https://www.getmatter.com/d/entry/<numeric-content-id>)`, `[Source](<original url>)`, `matter:item:<id>` (the key for spotting duplicates), and `Matter content id: <numeric-content-id>`.
- Label `read` only. Leave an existing task's due date and priority as they are unless asked to change them.
