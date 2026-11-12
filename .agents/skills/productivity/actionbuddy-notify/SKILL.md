---
name: actionbuddy-notify
description: "Provider implementation behind the notify-user skill (ActionBuddy macOS Shortcuts). Use only to repair the Send Notification shortcut contract or its helper."
---

# ActionBuddy Notify (provider)

Backend for the notify-user skill, which wraps this helper. Routine completion, blocker, and ready-for-review relays go through notify-user, not this skill; use this one for shortcut-contract repair and helper details.

The notification is a relay to the configured user, not an instruction to ActionBuddy.

## Shortcut contract

- macOS shortcut named `Send Notification` containing ActionBuddy's `Send Notification` action, with title, subtitle, and body wired from a JSON `Shortcut Input` dictionary (`title`, `subtitle`, `body`). `Show When Run` stays disabled.
- The helper writes the payload to a temp JSON file and runs `shortcuts run "Send Notification" --input-path <file>`. When `Shortcuts.sqlite` is readable it validates the structured shortcut before and after each send. If the database is unreadable (TCC, sandbox, missing file), it warns and still attempts `shortcuts run` / `shortcuts list`. The helper only reads: it never patches the shortcut or writes `Shortcuts.sqlite`.
- If the helper reports the shortcut still uses the legacy body-only contract or literal text, repair the shortcut to extract fields from JSON `Shortcut Input`, then re-validate. A timeout is not a reason to go back to literal-body patching.
- Attachments are unvalidated; treat them as unsupported until tested through `shortcuts run --input-path`.

## Fields

`--title` (sender or workflow, default `ActionBuddy`; e.g. your agent name, `Morning Check`), `--subtitle` (status/reason, default `Codex`; e.g. `Ready`, `Blocked`, `Needs Review`), `--message` (body, required). `--timeout` is only the local `shortcuts run` timeout, not content. After setup, sync, or helper changes, test all content fields together, not body-only.

## Repair / direct helper

These commands validate the backend during repair:

```bash
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --check --title "<agent name>" --subtitle "Ready" --message "..."
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --send  --title "<agent name>" --subtitle "Ready" --message "..."
```

Readonly-database, Operation-not-permitted, or Shortcuts sqlite access errors in a sandboxed session are a **soft warning**, not a hard failure: `--check` uses `shortcuts list`, and `--send` still runs `shortcuts run`. Retry with the session's approved local-automation escalation only when `shortcuts run` itself is denied. A `shortcuts run` timeout after send is indeterminate-but-nonfatal. The message transits a local temp file, so keep secrets out of it.
