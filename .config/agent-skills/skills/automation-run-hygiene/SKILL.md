---
name: automation-run-hygiene
description: "Normalize recurring automation runs; use when a prompt includes Automation, Automation ID, Automation memory, Last run, recurring scan, checkpoint, notification status, source gaps, or final handoff directives."
---

# Automation Run Hygiene

Use this skill for recurring automation threads and scheduled scout/router work. It keeps the run mechanics consistent so each automation prompt can stay focused on its domain.

## When To Use It

- The prompt includes `Automation:`, `Automation ID:`, `Automation memory:`, or `Last run:`.
- The task asks for a recurring scan, durable checkpoint, Craft run record, notification status, or cross-host handoff.
- You are editing or reviewing an automation prompt and need to decide which mechanics belong in the shared run contract.

## Core Workflow

1. Resolve host identity:
   - Prefer `AGENT_HOST_ALIAS` when set.
   - Otherwise use `hostname -s`.
2. Resolve paths from the live environment:
   - `CODEX_HOME=${CODEX_HOME:-$HOME/.codex}`.
   - Resolve automation memory from the prompt or under `$CODEX_HOME/automations/<automation-id>/memory.md`.
   - Resolve skills from the current session inventory first, then `$CODEX_HOME/skills`, then `~/.config/agent-skills/skills`.
3. Read the automation memory before scanning or writing when it exists.
4. Choose the scan window:
   - Use the latest successful checkpoint from memory when available.
   - Otherwise use the prompt's fallback window.
   - If neither exists, ask for the smallest missing input instead of inventing history.
5. Exclude the current automation run from historical evidence.
6. Prefer structural evidence over prompt text:
   - Parse JSONL sessions structurally.
   - Treat copied prompts, old memory excerpts, and replayed command output as context, not fresh friction.
7. Discover existing assets before proposing new ones.
8. Make the smallest allowed write, then read it back.
9. Append a concise local memory checkpoint before finishing.

## Durable Writes

- Follow the automation prompt's write boundaries exactly.
- If a Craft run record is required, read the target document or collection schema before writing.
- Keep dashboard/root pages compact. Put long run evidence in the run item body or the automation-specified archive destination.
- Update existing rows by stable slug when a recurring issue is reinforced.
- Do not create duplicate rows because another host already saw the same friction.
- Record source gaps separately from conclusions.

## Notification Status

Track notification work independently from the durable record:

- `not needed`: no actionable recommendation, blocker, or handoff.
- `sent`: validation and send both succeeded.
- `indeterminate`: send timed out or could not be confirmed.
- `failed`: validation or send failed after a reasonable fallback.
- `fallback sent`: primary failed and fallback relay succeeded.

Do not block the durable record or local checkpoint on notification failure. Use the relevant notification skill for provider-specific behavior.

## Final Handoff

- End with the host app's required final directive only when the current environment requires one.
- Emit exactly one final directive if required.
- Keep the final report focused on scan window, sources, durable writes, top actions, source gaps, notification status, and next checkpoint.

## What Belongs Elsewhere

- Domain-specific classifiers belong in the domain skill or automation prompt.
- Connector failure classification belongs in `connector-readiness-triage`.
- Notification provider implementation belongs in `actionbuddy-notify` or `poke-notify`.
- Project-specific workflow belongs in the owning repo instructions or project docs.
- Host-specific secrets, paths, and repair notes belong in ignored local config or shared Craft memory when another host needs to know.
