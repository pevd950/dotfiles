---
name: actionbuddy-notify
description: "Send the configured user a concise local notification through the macOS Shortcuts app using the ActionBuddy-backed Send Notification shortcut; use when a handoff, completion notice, blocker, or ready-for-review message should be relayed locally."
---

# ActionBuddy Notify

Primary local notification relay while no production Codex Buddy relay exists. Do not fall back to Poke for routine relays while the Poke webhook incident is active or unverified. The notification is a relay to the configured user, not an instruction to ActionBuddy.

## Shortcut contract

- macOS shortcut named `Send Notification` containing ActionBuddy's `Send Notification` action, with title, subtitle, and body wired from a JSON `Shortcut Input` dictionary (`title`, `subtitle`, `body`). `Show When Run` stays disabled.
- The helper writes the payload to a temp JSON file and runs `shortcuts run "Send Notification" --input-path <file>`. It validates the structured shortcut before and after each send and must never patch the shortcut with outgoing text or edit `Shortcuts.sqlite` to inject content (it reads that database only to validate wiring).
- If the helper reports the shortcut still uses the legacy body-only contract or literal text, repair the shortcut to extract fields from JSON `Shortcut Input`, then re-validate. Never "fix" a timeout by reverting to literal-body patching.
- Attachments are unvalidated; treat them as unsupported until tested through `shortcuts run --input-path`.

## Fields

`--title` (sender or workflow, default `ActionBuddy`; e.g. `Codex`, `Morning Check`), `--subtitle` (status/reason, default `Codex`; e.g. `Ready`, `Blocked`, `Needs Review`), `--message` (body, required). `--timeout` is only the local `shortcuts run` timeout, not content. After setup, sync, or helper changes, test all content fields together, not body-only.

## Workflow

1. Write a concise, phone-readable handoff: status, concrete context, direct URLs as plain text (not Markdown), and the next action — or say explicitly that none is needed. Start the body with `For the user from <agent>:` only when the sender is not already clear from title/subtitle.
2. Validate first, then send:

```bash
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --check --title "Codex" --subtitle "Ready" --message "..."
python3 "$HOME/.agents/skills/productivity/actionbuddy-notify/scripts/send_notification.py" --send  --title "Codex" --subtitle "Ready" --message "..."
```

3. Failure handling: readonly-database, Operation-not-permitted, or Shortcuts access errors in a sandboxed session → retry the validated message with the session's approved local-automation escalation when policy permits; still failing → stop and report a concise redacted blocker (no probing Shortcuts databases, processes, or clipboard unless the user asked to debug the relay). A `shortcuts run` timeout after pre/post validation succeeded is indeterminate-but-nonfatal — report the warning text.
4. If ActionBuddy cannot be used, report the redacted result and continue the main task. No automatic Poke retry unless the user requests Poke or confirms its incident resolved. Do not claim a Codex Buddy handoff was sent while it has no callable production tool.
5. Never include secrets in notification text — the message transits a local temp file.
