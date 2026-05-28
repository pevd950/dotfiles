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
- ActionBuddy's notification title, subtitle, and body must be wired from a JSON
  `Shortcut Input` dictionary with `title`, `subtitle`, and `body` fields.
- `Show When Run` must stay disabled.
- The helper writes the notification payload to a temporary JSON file and runs
  the shortcut with `shortcuts run "Send Notification" --input-path <temp-json-file>`.
- The helper validates the structured shortcut before and after each send
  attempt. It must not patch the shortcut with the outgoing notification text or
  edit `Shortcuts.sqlite` to inject message content.
- The helper reads `~/Library/Shortcuts/Shortcuts.sqlite` only to validate that
  the shortcut exists and is wired to structured `Shortcut Input`.
- Attachments are not part of the helper contract yet. Treat them as unvalidated
  until a concrete file/image use case has been tested through `shortcuts run`
  with `--input-path`.

## Supported Fields
- Always prefer the structured helper fields when sending or validating:
  - `--title`: notification title. Defaults to `ActionBuddy`.
  - `--subtitle`: notification subtitle. Defaults to `Codex`.
  - `--message`: notification body. Required.
- `--timeout` is only the local `shortcuts run` timeout. It is not notification
  content.
- For validation after setup, sync, or helper changes, test all content fields
  together instead of testing body-only delivery.

## Workflow
1. Write a concise, phone-readable handoff.
2. Include direct URLs when they materially help the recipient jump into the work.
3. Keep URLs as plain text, not Markdown.
4. Validate first:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --check --title "Codex" --subtitle "Validation" --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
5. Send only after validation succeeds:
   - `python3 "$HOME/.config/agent-skills/skills/actionbuddy-notify/scripts/send_notification.py" --send --title "Codex" --subtitle "Ready" --message "For the user from Codex: test notification. Context: validating ActionBuddy relay. Next step: none."`
6. If delivery fails with a readonly database, Operation not permitted, or Shortcuts access error in a sandboxed session, retry the same validated message with the session's approved local-automation escalation mechanism when policy permits.
7. If delivery still fails, stop and report a concise redacted blocker instead of probing Shortcuts databases, processes, clipboard state, or app internals unless the user explicitly asked to debug the relay.
8. If `shortcuts run` times out after the pre/post Shortcut Input validation
   succeeds, treat it as an indeterminate-but-nonfatal local relay result and
   report the warning text.
9. Report the redacted result back to the user.

## Message Shape
- Prefer one compact paragraph.
- Use `--title` for the sender or workflow, such as `Codex` or `Morning Check`.
- Use `--subtitle` for the status or reason, such as `Ready`, `Blocked`, or
  `Needs Review`.
- Start the body with `For the user from <agent>:` only when the sender is not
  already clear from title/subtitle.
- Include status, concrete context, links, and next action when available.
- If no action is needed, say so explicitly.

## Notes
- Do not rewrite the installed shortcut with the outgoing notification text.
- If the helper reports that the ActionBuddy shortcut still uses the legacy
  body-only contract or literal text, repair the shortcut so title, subtitle,
  and body are extracted from JSON `Shortcut Input`, then rerun validation.
- If `shortcuts run` times out, report the warning or use the configured
  fallback. Do not "fix" a timeout by reverting to literal-body shortcut
  patching.
- Readonly database and Shortcuts helper errors usually mean validation could not
  run; treat them as delivery blockers unless a permitted retry succeeds.
- Do not include secrets in notification text; the message is briefly written to a local temporary file while being sent.
