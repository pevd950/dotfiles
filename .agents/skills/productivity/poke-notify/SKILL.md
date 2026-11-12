---
name: poke-notify
description: "Provider implementation behind the notify-user skill (Poke inbound webhook). Use only to repair the Poke webhook helper or when the user explicitly asks for Poke. Enabled by default in the fan-out and soft-skips when POKE_API_KEY is unset."
---

# Poke Notify (provider)

Backend for the notify-user skill. Routine completion, blocker, and ready-for-review relays go through notify-user, not this skill.

Poke is **enabled** in the default notify-user provider list (ActionBuddy → CodexBuddy → Poke). Soft-skip when `POKE_API_KEY` is unset. Poke is a relay/messenger, not the reviewer or executor of the task.

## Requirements

- Endpoint: `https://poke.com/api/v1/inbound/api-message`, auth `Authorization: Bearer $POKE_API_KEY` (read from the shell environment).
- Payload must include a non-empty `message`. The helper makes an outbound HTTPS request and may need network permission in restricted sandboxes.

## Message shape

notify-user folds `title` / `subtitle` / `message` into one paragraph before calling this helper. If invoking the helper directly for repair, write a handoff, not a ping:

`For the user from <agent>: <status/update>. Context: <one-line handoff>. Links: <label> <url> [| <label> <url>]. Next step: <review/merge/respond/etc>. No action needed from you beyond relaying this message.`

- One compact paragraph; URLs as plain text (not Markdown) so they stay clickable; only real links (PRs, issues, CI runs, docs, designs) — omit empty sections.
- If a review is requested, say what kind: review PR, answer blocker, inspect CI, read issue context. If no action is needed, say so.
- If the handoff depends on local-only context, summarize it; the recipient reads on a phone and cannot open local paths.
- Give context with every request: a bare imperative like `go to the laptop` makes Poke infer the wrong role.

## Repair / direct helper

```bash
python3 "$HOME/.agents/skills/productivity/poke-notify/scripts/send_notification.py" --check --message "..."
python3 "$HOME/.agents/skills/productivity/poke-notify/scripts/send_notification.py" --send --message "..."
```

DNS, timeout, or network-access errors in a sandboxed session → retry the same validated message with the session's approved network-escalation mechanism when policy permits. Still failing → stop and report a concise redacted blocker.
