# Craft Blocks and Markdown Quirks

How to choose a block, and what the Markdown paths do with it. The writing rules are in the parent `SKILL.md`.

## Choosing a block

- **Task:** anything to be done. Short title; detail inside the task block.
- **Toggle:** detail, history and repeated cards that most readers skip. Start with `+ Title`; child bullets need two leading spaces.
- **Nested page:** long runbooks, logs, source notes and deep reference material that would make the root page heavy.
- **Table:** comparisons, resource lists, scorecards, schedules. Markdown tables become native tables and keep inline links.
- **Callout:** the one thing to read first, a caveat or a recommendation. One per page section at most; a whole section in a callout defeats it.
- **Collection:** rows that need typed properties, state, ownership or their own detail page. Read the schema before edits.
- **Line:** a break between major groups, used sparingly.
- **Code:** a structured `type: "code"` block with `rawCode` and `language` when using the API directly.

A reference page reads best as: status or at-a-glance table, then sections, then toggles or nested pages for the detail.

Themes, fonts, covers and decorative separators are for when the user asks for a styled page. Explore the live options first (`blocks explore-themes`, `blocks explore-washi`, `blocks search-unsplash`) and read the styling back.

## Markdown mechanics (API and plugin)

- Markdown insertion is sensitive to newline shape. Pass real newlines, not literal `\n` sequences; read back and fix escaped `\n` artifacts.
- Insert multiple list items together with real single newlines. If updating one list item into several fails, insert the replacement list after a nearby sibling, then delete the old block.
- Two leading spaces are one indentation level. Preserve indentation when editing nested lists and nested pages.
- A Markdown heading or title does not create a nested page. Create a structured page block, then resolve and read it before writing its body.
- Multi-paragraph callout Markdown creates several callout blocks.
- `***` or `---` creates a line block.
- Code fences can round-trip as inline code on some plugin paths; prefer structured code blocks.
- Craft tokens: `<page>`, `<card>`, `<pageTitle>`, `<content>`, `<callout>`, `<caption>`, `<highlight color="...">`, `==yellow highlight==`, `<comment id="...">`, `$inline math$`, `$$block math$$`, `[text](block://blockId)`, and date links in the form `date://YYYY-MM-DD`.
- Collection tags (`<collection>`, `<collectionItem>`, `<property>`, `<contentPreview>`, `<itemsPreview>`) are output-only.
- A GitHub rich preview is a `richUrl` block holding only the URL. Craft fills in its title and image afterwards, so a plain-looking read right after insertion is not a failure; read again later, or check in the app when the card matters.
- Date links (`[13 Nov](date://2026-11-13)`) link to that day's note; bold them where a date leads an entry. Tables are written as Markdown only, and the API rejects indenting one under a toggle.
- A PUT that rewrites a caption must resend the `<caption>` tags, or the block falls back to body text.
- Leave `taskInfo` out of formatting edits to a completed task: resending `state: done` resets its completion time, and sending `completedAt` alone reopens it.
- Craft rate-limits rapid writes (HTTP 429 after roughly 15 quick calls); pace bulk edits or retry with backoff.
- Inline highlights use Craft's named colors, not hex: `yellow`, `green`, `mint`, `cyan`, `blue`, `purple`, `pink`, `red`, `gray`, and gradients such as `gradient-blue`.

## Before handing off

- The top of the page reads at a glance without opening a toggle.
- Everything to be done is a task block, and long detail sits behind a toggle or nested page.
- Tables and links survived the readback.
