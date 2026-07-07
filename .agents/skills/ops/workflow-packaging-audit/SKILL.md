---
name: workflow-packaging-audit
description: Identify repeated manual workflows from recent Codex sessions, memories, Chronicle discovery, and existing skills or automations; use when asked what should become a skill, subagent, automation, or extension.
---

# Workflow Packaging Audit

Use this skill to turn recent work history into a small set of practical reusable assets.

## Evidence Order

1. Recent Codex sessions and task summaries.
2. Codex memories and rollout summaries.
3. Chronicle, if enabled, for discovery only.
4. Existing skills, custom agents, and automations.

Read Chronicle only as a routing signal. Confirm important details in Codex logs, memories, repositories, issue trackers, document systems, task managers, or local files before acting on them.

## Scan Window

- Default to the last 30 days.
- If less history exists, use all available history and say so.
- Scan both `~/.codex/sessions` and `~/.codex/archived_sessions`.
- Prefer structural JSONL reads over broad raw text search. Pair tool calls with tool outputs where possible.

## Candidate Rules

Only package a candidate when it:

- occurred at least twice, or is clearly likely to recur and costly to repeat;
- has stable inputs;
- has a repeatable procedure;
- has a clear output or stopping condition;
- materially improves speed, quality, consistency, or reliability;
- is not already adequately covered.

Choose the smallest documented form:

- `Skill`: reusable workflow, playbook, or domain procedure. Prefer this default for repeatable instructions, references, and helper scripts.
- `Custom subagent`: bounded specialist role or investigation task suitable for delegation. Use when the value is an independent role, not a workflow checklist.
- `Automation`: scheduled or recurring check, report, reminder, monitor, or heartbeat. Prefer automations that explicitly invoke skills for maintainability.
- `Plugin`: bundle of skills, app integrations, MCP servers, hooks, scripts, or assets that should install/update as a unit.
- `Hook`: lifecycle guardrail, lightweight context injection, policy check, or post-tool review. Do not use hooks for full workflows.
- `Config`: stable Codex configuration, subagent role definition, sandbox/rule setting, or project-local behavior.
- `Extend existing`: improve an existing asset instead of duplicating it.
- `Skip`: one-off, ambiguous, sensitive, poorly evidenced, or already covered work.

## Source References

Use local creator/evaluator skills and official Codex docs before creating or changing assets:

- For skills, use `$skill-creator` and the Codex skills docs: https://developers.openai.com/codex/skills
- For plugins, use `$plugin-creator` and the Codex plugins docs: https://developers.openai.com/codex/plugins
- For skill/plugin evaluation, use `$plugin-eval` when available.
- For automations, use the Codex automations docs: https://developers.openai.com/codex/app/automations
- For hooks, use the Codex hooks docs: https://developers.openai.com/codex/hooks
- For config, local state, project config, and subagent roles, use advanced configuration docs: https://developers.openai.com/codex/config-advanced

If the current session has an OpenAI docs MCP, use `$openai-docs` or the docs MCP before relying on memory. Otherwise restrict web research to official OpenAI docs for Codex behavior.

## Workflow

1. Load local guidance such as `AGENTS.md` and private local guidance when applicable.
2. Inventory current assets:
   - skills under `~/.agents/skills`;
   - Codex skills under `${CODEX_HOME:-$HOME/.codex}/skills` when relevant;
   - automations under `${CODEX_HOME:-$HOME/.codex}/automations`;
   - custom agents if the host has an agent root.
3. Build a compact evidence table from session history and memories.
4. Group repeated work by procedure, not by repo name.
5. For each group, decide `Skill`, `Custom subagent`, `Automation`, `Plugin`, `Hook`, `Config`, `Extend existing`, or `Skip`.
6. Before creating anything, check whether an existing asset already covers the work well enough.
7. When creation is justified, load the relevant creator skill first:
   - `$skill-creator` for new or updated skills;
   - `$plugin-creator` for plugin bundles or marketplace/package structure;
   - `$plugin-eval` after a meaningful skill/plugin change when evaluation would catch scope, token, trigger, or packaging problems.
8. Create or extend only high-confidence missing items. Keep them narrow and easy to validate.

## Output

First return a compact shortlist with:

- repeated workflow;
- supporting evidence and dates;
- frequency and confidence;
- recommended form;
- why it is or is not worth creating.

Then report:

- what was created or extended;
- what was deliberately skipped;
- what needs more evidence before packaging.

## Creation Rules

- For personal skills, prefer `~/.agents/skills`.
- Create only `SKILL.md` and `agents/openai.yaml` unless a script or reference file is genuinely needed.
- Do not create a plugin when one skill is enough. Use a plugin only when there is a coherent installable bundle or external tool surface.
- Do not create an automation until the prompt, cadence, permissions, output destination, and stop condition are clear.
- Do not create a hook unless the behavior is lightweight, event-driven, and safe to run frequently.
- Do not create subagent/config changes without checking the current `~/.codex/config.toml` or project `.codex/config.toml` shape.
- Use `apply_patch` for file edits.
- Validate frontmatter and exact-path yadm state after edits.
- Do not create speculative, overlapping, or broad assets.
