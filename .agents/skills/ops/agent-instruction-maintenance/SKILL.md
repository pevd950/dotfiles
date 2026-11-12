---
name: agent-instruction-maintenance
description: Review or refactor agent instructions, skills, and prompt configuration for clarity, conflicts, and cross-tool consistency. Use for instruction maintenance, not ordinary subagent work.
---

# Agent Instruction Maintenance

Audit agent instructions for clarity, correctness, and cross-tool consistency; validate frontmatter; keep tool-specific variants aligned.

## Workflow

1. Discover which ecosystems exist in the repo or user config, and resolve instruction file locations from the current source of truth: the session's skill inventory first, then `$HOME/.agents/skills`, provider compatibility folders such as `$HOME/.claude/skills`, or the relevant plugin cache. Confirm a remembered path before relying on it.
2. Load local guidance (AGENTS.md, CLAUDE.md, copilot-instructions) when present. Read the global instructions file in full first: skills must agree with it.
3. When mining session logs for instruction or skill friction, follow the structural JSONL-parsing rule in `workflow-packaging-audit`, and keep the current maintenance run separate from the sessions being analyzed.
4. Review each file with the lens below, and check activation, authority, and stopping conditions against the [behavior cases](references/behavior-cases.md). Keep common steps in the entrypoint and specialized detail in references.
5. Validate metadata and local links with `scripts/check_instructions.py` in the dotfiles repository (`~/scripts/check_instructions.py` on a live host). It checks structure, not activation.
6. For review-only requests, propose concrete changes. When edits are authorized, implement them, verify the diff, and report validation plus remaining runtime uncertainty.

## Review lens

1. **Conflicts with the global file** or another skill: quote both sides with file and line.
2. **Stale facts**: dates, versions, tool and command names, paths, "verified on" claims. Check cheaply whether the named script, path or flag still exists, and say what was verified and what is only suspected.
3. **Prohibitions that can be positive**: state the wanted behavior once. Keep a prohibition only where it guards something irreversible, costly, or a known failure specific to that tool.
4. **Duplication**: text that restates the global file or another skill becomes a pointer or goes.
5. **Provider-neutral wording**: backticked skill names, "the agent's own local memory", no single provider's invocation syntax. A skill that works with one provider only says so in its description.
6. **Rules that cause known complaints**: stopping to ask when work is already authorized, handing over manual steps the agent could do, process sized for a team, slow validation loops, staying silent when blocked.

## Prioritization

Codex-first unless the user asks for tool-specific changes. Prefer SKILL.md and AGENTS.md for portable shared behavior; use tool-specific files only for features unique to that tool.

## References

- Codex: `references/codex.md`
- Claude Code: `references/claude-code.md`
- VS Code/Copilot: `references/copilot-vscode.md`
- Commands vs skills vs agents: `references/tool-selection.md`

## Output

Findings and risk areas; required schema/format fixes separated from recommended clarity improvements; proposed edits with rationale; updated files when approved.
