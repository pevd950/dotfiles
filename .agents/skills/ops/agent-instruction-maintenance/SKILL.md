---
name: agent-instruction-maintenance
description: "Review, update, and synchronize agent instructions and configs across Codex and Claude (and optionally VS Code/Copilot); use when creating or refactoring agent prompts, skills, or chatmodes (trigger keywords: agent instructions, prompt review, skill update, chatmode, subagent)."
---

# Agent Instruction Maintenance

Audit agent instructions for clarity, correctness, and cross-tool consistency; validate frontmatter; keep tool-specific variants aligned without contradictions.

## Workflow

1. If the prompt carries automation metadata (`Automation:`, `Automation ID:`, `Automation memory:`, `Last run:`), follow `automation-run-hygiene` for checkpoint, scan-window, and handoff mechanics.
2. Discover which ecosystems exist in the repo or user config, and resolve instruction file locations from the current source of truth: the session's skill inventory first, then `$HOME/.agents/skills`, provider compatibility folders such as `$HOME/.claude/skills`, or the relevant plugin cache. Do not assume a remembered path is still canonical.
3. Load local guidance (AGENTS.md, CLAUDE.md, copilot-instructions) when present.
4. When mining Codex session logs for instruction or skill friction, parse JSONL structurally and focus on real tool outputs such as `function_call_output`. Raw `rg` over whole session files false-positives on prompts, embedded AGENTS text, and replayed command output; successful reads of automation memories or older excerpts are replayed context, not fresh friction. Separate the current maintenance run from the sessions being analyzed.
5. Validate minimal frontmatter per file type (see references), review content for clarity and scope, keep instructions lean with deep detail in references, and propose edits with before/after snippets and rationale.

## Prioritization

Codex-first unless the user asks for tool-specific changes. Prefer SKILL.md and AGENTS.md for portable shared behavior; use tool-specific files only for features unique to that tool.

## References

- Codex: `references/codex.md`
- Claude Code: `references/claude-code.md`
- VS Code/Copilot: `references/copilot-vscode.md`
- Commands vs skills vs agents: `references/tool-selection.md`

## Output

Findings and risk areas; required schema/format fixes separated from recommended clarity improvements; proposed edits with rationale; updated files when approved.
