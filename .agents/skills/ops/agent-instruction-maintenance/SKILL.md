---
name: agent-instruction-maintenance
description: Review or refactor agent instructions, skills, and prompt configuration for clarity, conflicts, and cross-tool consistency. Use for instruction maintenance, not ordinary subagent work.
---

# Agent Instruction Maintenance

Audit agent instructions for clarity, correctness, and cross-tool consistency; validate frontmatter; keep tool-specific variants aligned without contradictions.

## Workflow

1. If the prompt carries automation metadata (`Automation:`, `Automation ID:`, `Automation memory:`, `Last run:`), follow `automation-run-hygiene` for checkpoint, scan-window, and handoff mechanics.
2. Discover which ecosystems exist in the repo or user config, and resolve instruction file locations from the current source of truth: the session's skill inventory first, then `$HOME/.agents/skills`, provider compatibility folders such as `$HOME/.claude/skills`, or the relevant plugin cache. Do not assume a remembered path is still canonical.
3. Load local guidance (AGENTS.md, CLAUDE.md, copilot-instructions) when present.
4. When mining Codex session logs for instruction or skill friction, parse JSONL structurally and focus on real tool outputs such as `function_call_output`. Raw `rg` over whole session files false-positives on prompts, embedded AGENTS text, and replayed command output; successful reads of automation memories or older excerpts are replayed context, not fresh friction. Separate the current maintenance run from the sessions being analyzed.
5. Validate metadata and local links with the repository checker. Review activation, authority, and stopping conditions using [behavior cases](references/behavior-cases.md). Keep common steps in the entrypoint and specialized detail in references.
6. For review-only requests, propose concrete changes. When edits are authorized, implement them without another approval gate, verify the diff, and report validation plus remaining runtime uncertainty.

## Prioritization

Codex-first unless the user asks for tool-specific changes. Prefer SKILL.md and AGENTS.md for portable shared behavior; use tool-specific files only for features unique to that tool.

## References

- Codex: `references/codex.md`
- Claude Code: `references/claude-code.md`
- VS Code/Copilot: `references/copilot-vscode.md`
- Commands vs skills vs agents: `references/tool-selection.md`

## Output

Findings and risk areas; required schema/format fixes separated from recommended clarity improvements; proposed edits with rationale; updated files when approved.
