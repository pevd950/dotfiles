---
name: notify-user
description: "Fan out a structured handoff to the configured user's enabled notification providers; use for completion, blocker, ready-for-review, or other routine relays. Call $notify-user instead of ActionBuddy, Poke, or Buddy MCP."
---

# Notify User

Single caller-facing notification skill (`$notify-user`). Workflows load only this skill and run the fan-out script. Do not name ActionBuddy, Poke, or Buddy MCP for routine handoffs.

`actionbuddy-notify` and `poke-notify` are provider implementations (repair docs + helpers). Codex Buddy custom notify remains Host/MCP-owned and still requires **explicit user approval** — this skill does not invent a bypass.

## Fields

Pass the rich shape once. Adapters degrade:

| Field | CLI | Notes |
| --- | --- | --- |
| title | `--title` (default `Codex`) | ActionBuddy + Buddy; Poke folds into the paragraph |
| subtitle | `--subtitle` (default `Codex`) | ActionBuddy + optional Buddy (≤160 bytes); Poke folds |
| message / body | `--message` (required) | Phone-readable handoff; Buddy ≤560 bytes |
| destination | `--destination` | Optional HTTPS or portable `codexbuddy:` URL (Buddy only) |
| callerNamespaceID | `--caller-namespace-id` (default `notify-user`) | Buddy idempotency; keep stable per task/assistant |
| notificationID | `--notification-id` | Buddy idempotency; reuse only for retries/corrections |

Write a concise handoff: status, concrete context, plain-text URLs (not Markdown), and the next action — or say none is needed. Never put secrets in notification text.

## Workflow

1. Compose the structured fields above.
2. Validate, then send:

```bash
python3 "$HOME/.agents/skills/productivity/notify-user/scripts/send_notification.py" \
  --check --title "Codex" --subtitle "Ready" --message "..."
python3 "$HOME/.agents/skills/productivity/notify-user/scripts/send_notification.py" \
  --send  --title "Codex" --subtitle "Ready" --message "..."
```

Optional: `--config PATH`, `--json`, `--destination`, `--caller-namespace-id`, `--notification-id`.

3. Report `notification_status` using the automation-run-hygiene vocabulary: `sent` · `indeterminate` · `failed` · `fallback sent` (plus `checked` for `--check`). Continue the main task if notify fails; do not block durable writes on delivery.

## Provider config

Ordered list + enable flags, not hard-coded caller prose. Bundled default:

`~/.agents/skills/productivity/notify-user/config/providers.example.toml`

- ActionBuddy: enabled
- CodexBuddy: enabled (soft-skips when Host/MCP is unavailable)
- Poke: **off** (incident / explicit-ask only; never a silent fallback)

Override with `$XDG_CONFIG_HOME/notify-user/providers.toml` or `NOTIFY_USER_CONFIG`. Adding a provider is an adapter plus a config row. See the [example provider config](config/providers.example.toml).

## Provider behavior

**ActionBuddy** — wraps `actionbuddy-notify` (`shortcuts run` + structured Shortcut Input). Missing Shortcuts DB / non-macOS → `skipped`. `shortcuts run` timeout after a successful wiring check → `indeterminate`. Repair the shortcut via the provider skill; do not call that skill from workflows.

**CodexBuddy** — probe-only until a dedicated Host/MCP send path is stable. Soft-skip when `codex-buddy-mcp` / Host config is absent. **Approval gate:** `buddy_send_custom_notification` may run only after the user explicitly asks for or approves an externally visible Buddy handoff in this session. This adapter never invokes that MCP tool and never talks to the Host over an invented HTTP/CLI send path. Do not set an env var or flag to bypass the gate. Product notification routing policy stays in pevd950/codex-buddy (related: #27).

**Poke** — wraps `poke-notify` after folding title/subtitle into one `message`. Default-disabled. Enable in config only when the user asks for Poke or confirms the webhook incident is resolved. `POKE_API_KEY` stays in the environment; never print it.

Fan-out tries every **enabled** provider. Soft-skips do not enable Poke. `fallback sent` means the first enabled provider **failed** and a later **enabled** provider succeeded — not an implicit Poke retry.

## Failure handling

- Sandboxed Shortcuts / network errors: retry the same validated payload with the session's approved escalation when policy permits; still failing → report a redacted blocker and continue.
- Do not claim a Codex Buddy handoff was sent unless Buddy MCP actually sent after explicit approval (outside this script).
- Per-provider lines plus one `notification_status` are enough; do not dump helper stderr that might contain secrets.
