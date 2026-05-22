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
- ActionBuddy's notification body must be wired to `Shortcut Input`.
- The helper writes the message to a temporary text file and runs the shortcut with `shortcuts run "Send Notification" --input-path <file>`.
- The helper reads `~/Library/Shortcuts/Shortcuts.sqlite` only to validate that the shortcut exists and is wired to `Shortcut Input`; it must not patch the notification body with the message text.

## Workflow
1. Write a concise, phone-readable handoff.
2. Include direct URLs when they materially help the recipient jump into the work.
3. Keep URLs as plain text, not Markdown.
4. Validate first:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --check --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
5. Send only after validation succeeds:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --send --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
6. If delivery fails with a readonly database, Operation not permitted, or Shortcuts access error in a sandboxed session, retry the same validated message with the session's approved local-automation escalation mechanism when policy permits.
7. If delivery still fails, stop and report a concise redacted blocker instead of probing Shortcuts databases, processes, clipboard state, or app internals unless the user explicitly asked to debug the relay.
8. Report the redacted result back to the user.

## Message Shape
- Prefer one compact paragraph.
- Start with `For the user from <agent>:` when the sender matters.
- Include status, concrete context, links, and next action when available.
- If no action is needed, say so explicitly.

## Notes
- Do not rewrite the installed shortcut with the outgoing notification text.
- If the helper reports that the ActionBuddy body is literal text, repair the shortcut so the body uses `Shortcut Input`, then rerun validation.
- Readonly database and Shortcuts helper errors usually mean the notification was not delivered; treat them as delivery blockers unless a permitted retry succeeds.
- Do not include secrets in notification text; the message is briefly written to a local temporary file while being sent.
