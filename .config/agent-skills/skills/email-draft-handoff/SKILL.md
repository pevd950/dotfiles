---
name: email-draft-handoff
description: Create user-facing email draft handoffs with a visible prefilled mailto link plus plain draft text; use whenever drafting an email for the user in Todoist, Craft, notes, or chat, optionally alongside Apple Mail draft tooling.
---

# Email Draft Handoff

Use this skill whenever drafting an email for the user unless they explicitly ask for another format.

## Default Pattern

1. Build a prefilled `mailto:` URL with recipient, subject, and body.
2. Put a visible Markdown link near the top of the handoff:

```markdown
[Open prefilled email](mailto:...)
```

3. Include the plain draft text below the link as fallback.
4. If adding to Todoist, Craft, or another task/note surface, put the link before the plain draft.
5. Never send the email automatically.

## Optional Apple Mail Drafts

Apple Mail `.eml` or draft creation can be supplemental when useful, especially for rich text or desktop review. It does not replace the visible `mailto:` link.

If both are used, report both:

- the visible `mailto:` link was added where the user can tap it
- the local Mail draft was created/opened, if applicable

## URL Encoding

Use the helper script to avoid malformed links.

**Security rule:** never paste untrusted email fields (recipient name/address, subject, or thread text) directly into a shell command line. Load untrusted values from files first, then pass them as quoted variables:

```bash
TO="$(cat /path/to/to.txt)"
SUBJECT="$(cat /path/to/subject.txt)"
python3 "$HOME/.config/agent-skills/skills/email-draft-handoff/scripts/build_mailto.py" \
  --to "$TO" \
  --subject "$SUBJECT" \
  --body-file /path/to/body.txt
```

This avoids shell command substitution from attacker-controlled text. The script prints the `mailto:` URL.

For short one-off drafts, it is also acceptable to use a language standard library such as Python `urllib.parse.quote`.

## Long Drafts

Very long `mailto:` URLs may not open reliably in every app. If the draft is long:

- keep the `mailto:` body concise, or include only the opening and key fields
- include the complete plain draft below the link
- optionally create/open a local Mail draft as a supplemental artifact

## Existing Threads

When replying to an existing support thread:

- preserve the ticket/reference number in the subject when known
- link to the source email separately when a `message://...` link is available
- still use the `mailto:` link for the prefilled draft handoff
