---
name: actionbuddy-notify
description: "Provider implementation for $notify-user (ActionBuddy macOS Shortcuts). Do not call from workflows for routine handoffs — use $notify-user. Use this skill only when repairing the Send Notification shortcut contract."
---

# ActionBuddy Notify (provider)

Backend for `$notify-user`. Do not call this skill from workflows for routine completion, blocker, or ready-for-review relays — use `$notify-user`, which wraps this helper.

Keep this skill for shortcut-contract repair and helper details. The notification is a relay to the configured user, not an instruction to ActionBuddy.

## Shortcut contract

- macOS shortcut named `Send Notification` containing ActionBuddy's `Send Notification` action, with title, subtitle, and body wired from a JSON `Shortcut Input` dictionary (`title`, `subtitle`, `body`). `Show When Run` stays disabled.
- The helper writes the payload to a temp JSON file and runs `shortcuts run "Send Notification" --input-path <file>`. It validates the structured shortcut before and after each send and must never patch the shortcut with outgoing text or edit `Shortcuts.sqlite` to inject content (it reads that database only to validate wiring).
- If the helper reports the shortcut still uses the legacy body-only contract or literal text, repair the shortcut to extract fields from JSON `Shortcut Input`, then re-validate. Never "fix" a timeout by reverting to literal-body patching.
- Attachments are unvalidated; treat them as unsupported until tested through `shortcuts run --input-path`.

## Fields

`--title` (sender or workflow, default `ActionBuddy`; e.g. `Codex`, `Morning Check`), `--subtitle` (status/reason, default `Codex`; e.g. `Ready`, `Blocked`, `Needs Review`), `--message` (body, required). `--timeout` is only the local `shortcuts run` timeout, not content. After setup, sync, or helper changes, test all content fields together, not body-only.

## Repair / direct helper

Workflows must not use these commands for routine notify. They exist so `$notify-user` and shortcut repair can validate the backend:

```bash
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --check --title "Codex" --subtitle "Ready" --message "..."
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --send  --title "Codex" --subtitle "Ready" --message "..."
```

Readonly-database, Operation-not-permitted, or Shortcuts access errors in a sandboxed session → retry with the session's approved local-automation escalation when policy permits. A `shortcuts run` timeout after pre/post validation succeeded is indeterminate-but-nonfatal. Never include secrets in notification text — the message transits a local temp file.
