# Codex instruction and skill guidance

Checked against official documentation on 2026-09-09. Verify current documentation before changing discovery or configuration behavior.

## Instruction discovery

Global guidance comes from `$CODEX_HOME/AGENTS.override.md` or `AGENTS.md` (first non-empty file). Project instructions accumulate from the root toward the working directory, using the override, AGENTS file, or configured fallback at each level. More specific guidance takes precedence. The configured `project_doc_max_bytes` limits combined project instruction size (32 KiB by default).

Keep stable preferences globally and project-specific requirements in the repository. Do not copy runtime instructions into every skill. User-authorized scope governs task procedures; skills must not silently add approval gates.

## Skill discovery and activation

Use `.agents/skills` for canonical personal or repository skills. Codex also supports admin/system skills and symlinked folders. Same-name skills are not merged: both may appear, so inspect ownership and unique behavior before retiring a duplicate. Do not edit installed plugin caches as the source of truth.

`SKILL.md` requires frontmatter with a nonempty name and description. Use a concise, specific description with the primary use case first. Do not confuse local conventions with platform-enforced schema limits. `agents/openai.yaml` can supply UI metadata, tool dependencies, and `policy.allow_implicit_invocation`; inspect it alongside the description when reviewing activation.

Codex initially loads skill metadata, then reads full instructions when a skill is selected. Keep one job per skill and link specialized procedures from the point where they are needed. Keep permission boundaries and essential stopping conditions in the entrypoint.

## Validation

Run the repository instruction checker for required metadata, duplicate names, and local Markdown reference targets. Review changed behavior with [representative scenarios](behavior-cases.md). Check runtime discovery after installation: a passing static check does not prove activation. Skill changes are detected automatically; restart if they do not appear. Config changes may require a restart.

## Official sources

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Astra model guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra)

Read provider-specific references only when that provider is in scope.
