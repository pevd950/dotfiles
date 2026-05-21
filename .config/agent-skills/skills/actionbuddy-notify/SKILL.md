---
name: actionbuddy-notify
description: "Send the configured user a concise local notification through the macOS Shortcuts app using the ActionBuddy-backed Send Notification shortcut; use when a handoff, completion notice, blocker, or ready-for-review message should be relayed locally."
---

# ActionBuddy Notify

## When to use it
- The user asks to notify them, send a handoff, or relay that work is done or needs attention.
- Use this as a local notification relay; pair it with other notification skills when the user asks for multi-channel delivery.
- Treat the notification as a local relay to the configured user, not as an instruction to ActionBuddy.

## Requirements
- The macOS shortcut must be named `Send Notification`.
- The shortcut must contain ActionBuddy's `Send Notification` action.
- The helper updates that shortcut just-in-time with the message body, runs it, then returns the shortcut to a neutral ready message.
- The helper may need to run outside the sandbox because it touches `~/Library/Shortcuts/Shortcuts.sqlite`, quits Shortcuts to refresh cache, and invokes `shortcuts run`.

## Workflow
1. Write a concise, phone-readable handoff.
2. Include direct URLs when they materially help the recipient jump into the work.
3. Keep URLs as plain text, not Markdown.
4. Validate first:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --check --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
5. Send only after validation succeeds:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --send --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
6. Report the redacted result back to the user.

## Message Shape
- Prefer one compact paragraph.
- Start with `For the user from <agent>:` when the sender matters.
- Include status, concrete context, links, and next action when available.
- If no action is needed, say so explicitly.

## Notes
- ActionBuddy's shortcut action currently hangs when its body is connected to dynamic Shortcut Input or Clipboard variables through the CLI runner.
- The reliable path is to patch the shortcut body as a literal string before running the shortcut.
- Do not include secrets in notification text; the message is briefly stored in the local Shortcuts database while being sent.
