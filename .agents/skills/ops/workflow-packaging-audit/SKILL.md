---
name: workflow-packaging-audit
description: Identify repeated manual workflows worth packaging, working from Codex session data (sessions, memories, Chronicle) plus existing skills and automations. Use when asked what should become a skill, subagent, automation, or extension.
---

# Workflow Packaging Audit

Turn recent work history into a small set of practical reusable assets. The evidence sources and collectors read Codex session data; another agent can run the audit, but only over Codex history.

## Evidence

Order: recent Codex sessions and task summaries → Codex memories and rollout summaries → Chronicle, if enabled, as a discovery signal only (confirm details in logs, repos, trackers, or files before acting) → existing skills, custom agents, and automations.

Scan window: for recurring reviews and ad hoc reviews without a requested interval, the preceding 30 complete calendar days in the configured local timezone, excluding the current day; use a requested interval for ad hoc reviews, or all available history when explicitly requested (say so). A checkpoint from an earlier run resumes work inside that window; it does not narrow it. Scan both `~/.codex/sessions` and `~/.codex/archived_sessions`.

Parse session JSONL structurally: pair each tool call with its output and judge friction from real tool outputs such as `function_call_output`. Raw text search over whole session files false-positives on prompts, embedded instruction text, and replayed command output; successful reads of automation memories or older excerpts are replayed context, not fresh friction. Exclude the current run from the evidence, and record source gaps separately from conclusions.

For an authorized full-window review across approved hosts, use [private transcript pull and review](references/transcript-review.md). It copies active and archived transcripts into a private source-separated cache over existing SSH and rsync, resumes local batches until traversal finishes, and retrieves surrounding user, tool and response context. Its session worklist records reviewed, no-change, and pending chats separately from indexing. Report unavailable sources, parse gaps, exclusions, and unknown archive history; coverage is separate from completed contextual review.

For an explicitly bounded point scan, use [the collector interface](references/collector.md). Its limits do not establish complete monthly or multi-host coverage.

## Candidate rules

Package only when the workflow occurred at least twice (or clearly recurs and is costly to repeat), has stable inputs, a repeatable procedure, a clear output or stopping condition, materially improves speed, quality, consistency, or reliability, and is not already adequately covered.

Choose the smallest documented form:

- `Skill` — the default for repeatable instructions, references, and helper scripts.
- `Custom subagent` — a bounded specialist role worth delegating; the value is the role, not a checklist. Check the current `~/.codex/config.toml` or project `.codex/config.toml` shape first.
- `Automation` — scheduled or recurring check, report, monitor, or heartbeat; prefer automations that invoke skills. Needs a clear prompt, cadence, permissions, output destination, and stop condition before creation.
- `Plugin` — a coherent installable bundle or external tool surface; one skill stays a skill.
- `Hook` — lightweight, event-driven, safe to run frequently; a full workflow belongs in a skill.
- `Config` — stable Codex configuration or project-local behavior.
- `Extend existing` — improve an existing asset instead of duplicating it.
- `Skip` — one-off, ambiguous, sensitive, poorly evidenced, or already covered.

## Sources before creating

Load the host's skill-authoring skill (`skill-creator`) for new or updated skills and, where the host provides them, its plugin-authoring and plugin-evaluation skills (`plugin-creator`, `plugin-eval` in Codex) for plugin bundles and after meaningful changes. For Codex assets, use the official docs under `https://developers.openai.com/codex/` (skills, plugins, app/automations, hooks, config-advanced), through the OpenAI docs MCP or the `openai-docs` skill when available.

## Process

Inventory existing assets — `~/.agents/skills`, `${CODEX_HOME:-$HOME/.codex}/skills` and `.../automations`, and any agent roots — then build a compact evidence table, group repeated work by procedure (not repo), decide the form per group, and create or extend only high-confidence, narrow, validatable items. Validate frontmatter and exact-path yadm state after edits.

## Output

First a shortlist: repeated workflow, supporting evidence with dates, frequency and confidence, recommended form, and why it is or is not worth creating. Then: what was created or extended, what was deliberately skipped, and what needs more evidence.
