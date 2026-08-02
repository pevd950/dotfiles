---
name: automation-run-hygiene
description: "Normalize recurring automation runs; use when a prompt includes Automation, Automation ID, Automation memory, Last run, recurring scan, checkpoint, notification status, source gaps, or final handoff directives."
---

# Automation Run Hygiene

Shared run contract for recurring automation threads and scheduled scout/router work, so each automation prompt can stay focused on its domain.

## Core workflow

1. Resolve paths from the live environment: `CODEX_HOME=${CODEX_HOME:-$HOME/.codex}`; automation memory from the prompt or `$CODEX_HOME/automations/<automation-id>/memory.md`; skills from the session inventory first, then `$HOME/.agents/skills`.
2. Read the automation memory before scanning or writing when it exists.
3. Scan window: the latest successful checkpoint from memory; otherwise the prompt's fallback window; otherwise ask for the smallest missing input instead of inventing history.
4. Exclude the current run from historical evidence. Parse JSONL sessions structurally; copied prompts, old memory excerpts, and replayed command output are context, not fresh friction.
5. Discover existing assets before proposing new ones.
6. Make the smallest allowed write, then read it back.
7. Append a concise local memory checkpoint before finishing.

## Durable writes

- Follow the automation prompt's write boundaries exactly. When a provider-specific durable record is required, load the owning domain skill and read the target or schema before writing.
- Keep dashboard/root pages compact; long run evidence goes in the run item body or the automation-specified archive.
- Update existing rows by stable slug when a recurring issue is reinforced; never duplicate a row because another host already saw the same friction.
- Record source gaps separately from conclusions.

## Notification status

Track independently from the durable record — never block the record or local checkpoint on notification failure:

`not needed` · `sent` (validation and send both succeeded) · `indeterminate` (send timed out or unconfirmed) · `failed` (after a reasonable fallback) · `fallback sent` (primary failed, fallback relay succeeded).

Provider-specific behavior lives in `actionbuddy-notify` / `poke-notify`.

## Final handoff

Emit exactly one final directive, and only when the host app requires one. Keep the final report to: scan window, sources, durable writes, top actions, source gaps, notification status, next checkpoint.

## Belongs elsewhere

Domain-specific classifiers → the domain skill or automation prompt. Connector failure classification → `connector-readiness-triage`. Project-specific workflow → the owning repo instructions. Host-specific secrets, paths, and repair notes → ignored local config or the owning domain's shared-memory protocol when another host needs them.
