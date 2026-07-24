---
name: poke-notify
description: "Use Poke's inbound API message webhook only when the user explicitly asks for Poke or confirms the webhook incident is resolved. Do not use it as a default completion, handoff, or fallback notification relay."
---

# Poke Notify

Use only when the user explicitly asks for Poke, or confirms the webhook incident is resolved and asks to resume Poke relays. Never for routine completion/blocker/handoff relays, and never as an ActionBuddy fallback while the incident is active or unverified. Poke is a relay/messenger, not the reviewer or executor of the task.

## Requirements

- Endpoint: `https://poke.com/api/v1/inbound/api-message`, auth `Authorization: Bearer $POKE_API_KEY` (already in the shell env; never print, store, commit, or echo the value).
- Payload must include a non-empty `message`. The helper makes an outbound HTTPS request and may need network permission in restricted sandboxes.

## Message shape

Write it as a handoff, not a ping — include the minimum context the recipient needs to act without reopening the thread:

`For the user from <agent>: <status/update>. Context: <one-line handoff>. Links: <label> <url> [| <label> <url>]. Next step: <review/merge/respond/etc>. No action needed from you beyond relaying this message.`

- One compact paragraph; URLs as plain text (not Markdown) so they stay clickable; only real links (PRs, issues, CI runs, docs, designs) — omit empty sections.
- If a review is requested, say what kind: review PR, answer blocker, inspect CI, read issue context. If no action is needed, say so.
- If the handoff depends on local-only context, summarize it instead of referencing a path the recipient cannot open from a phone.
- Avoid context-free imperatives like `go to the laptop`; they make Poke infer the wrong role.

## Workflow

1. Validate: `scripts/send_notification.py --check --message "..."` (the helper schema-validates before any delivery).
2. Send only after the check passes: `scripts/send_notification.py --send --message "..."`.
3. DNS, timeout, or network-access errors in a sandboxed session → retry the same validated message with the session's approved network-escalation mechanism when policy permits. Still failing → stop and report a concise redacted blocker; these errors mean the message was not delivered, so no silent fallbacks and no repeated retries.
4. Report only the redacted result to the user.

The canonical skill lives in `~/.agents/skills/productivity/poke-notify/`; provider-specific locations should symlink to it.
