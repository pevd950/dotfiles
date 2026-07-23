# Craft Formatting Patterns

Use this reference when the user asks for a polished, rich, visual, or highly scannable Craft document. Keep the root page glanceable and move detail into native Craft structures.

## Layout Pattern

Prefer this order for durable reference pages:

1. Purpose quote or callout
2. Short "how to use this page" callout
3. At-a-glance table, status matrix, or phase map
4. Section dividers between major groups
5. Toggle cards or nested pages for detailed entries
6. Final action/recommendation section

Example:

```markdown
> **Purpose:** One sentence that explains what this page helps the reader decide or do.

<callout>**How to use this page:** Start with the table, then open detail cards only where needed.</callout>

## At a Glance

| Item | Status | Owner | Next step |
|---|---|---|---|
| Example | Active | Pablo | Review detail card |

***

## Detail Cards

+ Example detail card
  - **Summary:** Keep the summary short.
  - **Why it matters:** Explain the practical value.
  - **Link:** [Source](https://example.com)
```

## Craft Blocks That Read Well

- **Callouts:** Use for "read this first", caveats, recommendations, or mutation checklists. Avoid wrapping whole sections in callouts.
- **Tables:** Use before long prose for comparisons, resource lists, scorecards, schedules, and reading paths. Markdown tables become native Craft tables and preserve inline links.
- **Toggles:** Use for repeated detail cards. Start with `+ Title`; child bullets need two leading spaces.
- **Collections:** Use when rows need typed properties, state, ownership, or durable row-level detail pages. Read schema before edits.
- **Nested pages:** Use for long runbooks, logs, source notes, and deep reference material that would make the root page too heavy.
- **Tasks:** Use only when Craft-native task state is explicitly useful. This user normally uses Todoist for active commitments.
- **Code blocks:** Prefer structured `type: "code"` blocks with `rawCode` and `language` when using the API directly.

## Styling Pattern

For user-facing polished notes:

1. Search for a relevant cover with `blocks search-unsplash "<query>"`.
2. Apply the cover with attribution.
3. Choose a restrained theme unless the user asks for a bold visual style.
4. Apply separators sparingly to major section breaks.
5. Read back `.styling` and a markdown rendering before handoff.

Safer defaults:

- `--theme-id black-white` or `--theme-id default` for durable reference pages.
- `--font system` for operational or technical notes.
- `--separator washi --washi-pattern hex|grid|wave` for a little visual structure without making the page noisy.

Avoid strong tinted backgrounds for reference pages unless the user explicitly wants that look; they can make long notes harder to read.

## Live Sample Hook

If `CRAFT_FORMATTING_SAMPLE_URL` is set in the local environment and Craft access is available, use it as a private live sample for visual structure. Resolve the link first, read the sample, extract reusable layout/style patterns, and do not copy private content or hard-code the URL into tracked/shared files.

## Verification Checklist

- The page title is correct.
- The top of the page is glanceable without opening every toggle.
- Long repeated detail is behind toggles, nested pages, or collection item pages.
- Tables and links survived readback.
- Callouts are used for important summaries, not as decoration.
- Styling readback shows the intended theme, font, cover, and separator style.
