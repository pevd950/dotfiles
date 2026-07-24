---
name: email-draft-handoff
description: Create user-facing email draft handoffs with a visible prefilled mailto link plus plain draft text; use whenever drafting an email for the user in Todoist, Craft, notes, or chat, optionally alongside Apple Mail draft tooling.
---

# Email Draft Handoff

Use this pattern whenever drafting an email for the user, unless they explicitly ask for another format. Never send the email automatically.

## Default pattern

1. Build a prefilled `mailto:` URL with recipient, subject, and body.
2. Put a visible Markdown link near the top of the handoff — before the plain draft when adding to Todoist, Craft, or another task/note surface: `[Open prefilled email](mailto:...)`
3. Include the plain draft text below the link as fallback.

Apple Mail `.eml`/draft creation is supplemental (rich text, desktop review) and never replaces the visible `mailto:` link; when both are used, report both.

## URL encoding — security rule

Never paste untrusted email fields (recipient name/address, subject, thread text) directly into a shell command line. Load untrusted values from files, then pass them as quoted variables to the helper, which prints the `mailto:` URL:

```bash
TO="$(cat /path/to/to.txt)"
SUBJECT="$(cat /path/to/subject.txt)"
python3 "$HOME/.agents/skills/productivity/email-draft-handoff/scripts/build_mailto.py" \
  --to "$TO" --subject "$SUBJECT" --body-file /path/to/body.txt
```

For short one-off drafts, a language standard library (Python `urllib.parse.quote`) is also acceptable.

## Long drafts

Very long `mailto:` URLs may not open reliably. Keep the `mailto:` body concise (opening and key fields), include the complete plain draft below the link, and optionally create a local Mail draft as a supplemental artifact.

## Existing threads

Preserve the ticket/reference number in the subject when known; link the source email separately when a `message://...` link is available; still provide the `mailto:` link for the prefilled draft.
