---
name: agent-instruction-maintenance
description: "Review, update, and synchronize agent instructions and configs across Codex and Claude (and optionally VS Code/Copilot); use when creating or refactoring agent prompts, skills, or chatmodes (trigger keywords: agent instructions, prompt review, skill update, chatmode, subagent)."
---

# Agent Instruction Maintenance

## What this skill does
- Audits agent instructions for clarity, correctness, and consistency.
- Validates frontmatter and minimal schemas for detected ecosystems.
- Aligns tool-specific variants while keeping behavior consistent.

## When to use it
- Trigger phrases: "agent instructions", "prompt review", "skill update", "chatmode", "subagent".
- Use after creating or editing instructions, or when standards change.

## Step-by-step workflow
1) Discover which ecosystems exist in the repo or user config.
2) Resolve instruction file locations from the current source of truth before opening them.
- For named skills, prefer the path supplied by the current session's skill inventory.
- If a remembered path is missing, re-resolve under `${CODEX_HOME:-$HOME/.codex}/skills`, `~/.config/agent-skills/skills`, or the relevant plugin cache instead of assuming the old location is still canonical.
3) Load local guidance (AGENTS.md, CLAUDE.md, copilot-instructions) when present.
4) When auditing Codex session logs for instruction or skill friction, parse JSONL records structurally and focus on actual tool outputs such as `function_call_output`. Avoid raw `rg` over whole session files as a primary signal because prompts, embedded AGENTS.md text, and prior command outputs create false positives. If possible, separate the current maintenance run from the historical sessions being analyzed.
5) Validate minimal frontmatter for each file type (see references).
6) Review content for clarity, scope, and actionability; remove ambiguity.
7) Ensure intent parity across tools while avoiding contradictions.
8) Keep instructions lean; move deep details into references.
9) Propose updates with before/after snippets and rationale.

## Default prioritization
- Prefer Codex-first guidance unless the user asks for tool-specific changes.
- Prefer Skills (SKILL.md) and AGENTS.md for portable, shared behavior.
- Apply tool-specific files only when a feature is unique to that tool.

## Tool-specific references
- Codex: `references/codex.md`
- Claude Opus: `references/claude-code.md`
- VS Code/Copilot (optional): `references/copilot-vscode.md`
- Tool choice (commands vs skills vs agents): `references/tool-selection.md`

## Expected outputs / formatting
- Summary of findings and risk areas.
- Required fixes (schema/format) vs recommended improvements (clarity/consistency).
- Proposed edits with brief rationale.
- Updated files when approved.

## Example prompts
- "Review our skills and normalize naming/trigger phrases."
- "Validate agent frontmatter across Claude and Copilot files."
- "Update Codex skills to match new project standards."
