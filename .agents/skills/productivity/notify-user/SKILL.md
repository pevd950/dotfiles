---
name: notify-user
description: "Fan out a structured handoff to the configured user's enabled notification providers; use for completion, blocker, ready-for-review, or other routine relays. Every routine notification goes through this skill, which wraps ActionBuddy, Poke, and Buddy MCP."
---

# Notify User

The single caller-facing notification skill. Workflows load this skill and run its fan-out script; ActionBuddy, Poke, and Buddy MCP are reached through it.

This fan-out is separate from an agent's own native turn notifications (for example Codex Desktop/TUI/`notify`-hook notifications), which stay automatic.

`actionbuddy-notify` and `poke-notify` are provider implementations (repair docs + helpers). Codex Buddy custom notify remains Host/MCP-owned and still requires **explicit user approval** — this skill does not invent a bypass.

## Fields

Pass the rich shape once. Adapters degrade:

| Field | CLI | Notes |
| --- | --- | --- |
| title | `--title` | Your agent name and the title of the thread or session you are in, as `<agent> · <thread title>`, for example `Codex · Stuff holiday sharing` (script default `Codex`). Buddy allows 120 bytes, so shorten a long thread title; with no thread title, use the project and a few words on the task. ActionBuddy + Buddy; Poke folds into the paragraph |
| subtitle | `--subtitle` | Status or reason, for example `Ready` or `Blocked` (script default `Codex`). ActionBuddy + optional Buddy (≤160 bytes); Poke folds |
| message / body | `--message` (required) | Phone-readable handoff; Buddy ≤560 bytes |
| destination | `--destination` | Optional HTTPS or portable `codexbuddy:` URL (Buddy only) |
| callerNamespaceID | `--caller-namespace-id` (default `notify-user`) | Buddy idempotency; keep stable per task/assistant |
| notificationID | `--notification-id` | Buddy idempotency; reuse only for retries/corrections |

Write a concise handoff: status, concrete context, plain-text URLs (not Markdown), and the next action — or say none is needed. Keep secrets out of the text; it transits provider services and a local temp file.

## Workflow

1. Compose the structured fields above.
2. Validate, then send:

```bash
python3 "$HOME/.agents/skills/productivity/notify-user/scripts/send_notification.py" \
  --check --title="<agent> · <thread title>" --subtitle=Ready --message="..."
python3 "$HOME/.agents/skills/productivity/notify-user/scripts/send_notification.py" \
  --send --title="<agent> · <thread title>" --subtitle=Ready --message="..."
```

Prefer `--flag=value` for title, subtitle, and message so a body like `--blocked` is not parsed as a new option. Space-separated `--message "$value"` still works. If the value itself is a CLI switch (`--check`, `--json`, …), use the equals form (`--message=--check`).

Optional: `--config PATH`, `--json`, `--destination`, `--caller-namespace-id`, `--notification-id`.

3. Report `notification_status` as one of `sent` · `indeterminate` · `failed` · `fallback sent` (plus `checked` for `--check`). If notify fails, continue the main task and its durable writes.

## Provider config

Providers are an ordered list with enable flags. Bundled default:

`~/.agents/skills/productivity/notify-user/config/providers.example.toml`

- ActionBuddy: enabled
- CodexBuddy: enabled (soft-skips when Host/MCP is unavailable)
- Poke: enabled (soft-skips when `POKE_API_KEY` is unset)

Override with `$XDG_CONFIG_HOME/notify-user/providers.toml` or `NOTIFY_USER_CONFIG`. See the [example provider config](config/providers.example.toml).

## Provider behavior

**ActionBuddy** — wraps `actionbuddy-notify` (`shortcuts run` + structured Shortcut Input). Missing Shortcuts DB / non-macOS → `skipped`. Sqlite TCC / unreadable DB → warn and still `--check` via `shortcuts list` / `--send` via `shortcuts run` (`checked` / `indeterminate` / `sent`; sqlite access never fails the fan-out). `shortcuts run` timeout → `indeterminate`. Repair the shortcut with the `actionbuddy-notify` skill.

**CodexBuddy** — probe-only until a dedicated Host/MCP send path is stable. Soft-skip when `codex-buddy-mcp` / Host config is absent. Field-limit or ID/destination mismatches also skip (they must not fail `--check` while this adapter cannot send). **Approval gate:** `buddy_send_custom_notification` may run only after the user explicitly asks for or approves an externally visible Buddy handoff in this session. This adapter never invokes that MCP tool and never talks to the Host over an invented HTTP/CLI send path. Do not set an env var or flag to bypass the gate.

**Poke** — wraps `poke-notify` after folding title/subtitle into one `message`. Enabled by default. Soft-skip when `POKE_API_KEY` is unset; the key is read from the environment.

Fan-out tries every **enabled** provider and soft-skips unavailable ones. `fallback sent` means the first enabled provider **failed** and a later **enabled** provider succeeded.

## Failure handling

- Sandboxed Shortcuts / network errors: retry the same validated payload with the session's approved escalation when policy permits; still failing → report a redacted blocker and continue.
- Report a Codex Buddy handoff as sent only when Buddy MCP actually sent it after explicit approval (outside this script).
- Report per-provider lines plus one `notification_status`; leave helper stderr out, since it may contain secrets.
