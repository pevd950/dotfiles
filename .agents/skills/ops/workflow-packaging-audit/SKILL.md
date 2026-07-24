---
name: workflow-packaging-audit
description: Identify repeated manual workflows from recent Codex sessions, memories, Chronicle discovery, and existing skills or automations; use when asked what should become a skill, subagent, automation, or extension.
---

# Workflow Packaging Audit

Turn recent work history into a small set of practical reusable assets.

## Evidence

Order: recent Codex sessions and task summaries → Codex memories and rollout summaries → Chronicle, if enabled, as a discovery/routing signal only (confirm details in logs, repos, trackers, or files before acting) → existing skills, custom agents, and automations.

Scan window: last 30 days by default, or all available history (say so). Scan both `~/.codex/sessions` and `~/.codex/archived_sessions`; prefer structural JSONL reads over broad raw text search, pairing tool calls with tool outputs.

## Candidate rules

Package only when the workflow occurred at least twice (or clearly recurs and is costly to repeat), has stable inputs, a repeatable procedure, a clear output or stopping condition, materially improves speed, quality, consistency, or reliability, and is not already adequately covered.

Choose the smallest documented form:

- `Skill` — the default for repeatable instructions, references, and helper scripts.
- `Custom subagent` — a bounded specialist role worth delegating; the value is the role, not a checklist. Check the current `~/.codex/config.toml` or project `.codex/config.toml` shape first.
- `Automation` — scheduled or recurring check, report, monitor, or heartbeat; prefer automations that invoke skills. Requires a clear prompt, cadence, permissions, output destination, and stop condition before creation.
- `Plugin` — a coherent installable bundle or external tool surface only; never for one skill.
- `Hook` — lightweight, event-driven, safe to run frequently; never a full workflow.
- `Config` — stable Codex configuration or project-local behavior.
- `Extend existing` — improve an existing asset instead of duplicating it.
- `Skip` — one-off, ambiguous, sensitive, poorly evidenced, or already covered.

## Sources before creating

Load `$skill-creator` for new or updated skills, `$plugin-creator` for plugin bundles, and `$plugin-eval` after meaningful changes. Use official Codex docs under `https://developers.openai.com/codex/` (skills, plugins, app/automations, hooks, config-advanced), preferring the OpenAI docs MCP or `$openai-docs` over memory when available.

## Process

Inventory existing assets — `~/.agents/skills`, `${CODEX_HOME:-$HOME/.codex}/skills` and `.../automations`, and any agent roots — then build a compact evidence table, group repeated work by procedure (not repo), decide the form per group, and create or extend only high-confidence, narrow, validatable items. Validate frontmatter and exact-path yadm state after edits.

## Output

First a shortlist: repeated workflow, supporting evidence with dates, frequency and confidence, recommended form, and why it is or is not worth creating. Then: what was created or extended, what was deliberately skipped, and what needs more evidence.
