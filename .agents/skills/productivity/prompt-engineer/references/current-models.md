# Prompting current models

Reviewed: 2026-11-12, against the vendor pages linked below. Guidance changes with each model release: honor the exact model the user names, and recheck the linked page before relying on a model-specific claim.

These notes are about prompt text. API settings (reasoning effort, verbosity, structured outputs, caching) go in a prompt only when the user asks for API configuration; take them from the vendor's current docs.

## What holds across current models

- **Say the outcome, what done looks like, and the scope.** Current models follow instructions literally and do not stretch an instruction past what it says.
- **Give the reason for a rule, in plain wording.** Models generalize from the reason. Capitals, "CRITICAL" and "MUST" make them over-apply the rule.
- **Keep absolutes for true invariants.** A "never" is read as absolute, so write the approval or exception form instead: "ask before deleting files".
- **Leave reasoning to the model.** "Think step by step", "be thorough", "double-check" and push-testing language now cause overwork. Depth is a setting, not prompt text.
- **Examples are copied closely.** Use them when format or tone needs them, vary them, and cut any that do not change the result.
- **Instructions must agree.** Conflicts between a prompt, skills and instruction files make current models stop early. Say which one wins.
- **Leaner is better.** State each instruction once and remove what the model does anyway.
- **A revised prompt is a hypothesis.** Only a run on real tasks shows whether it is better.

## Claude (Fable 5.2, Opus 5.5, Sonnet 5.5, Haiku 5.5)

- Put long documents first and the question last. Separate source material, instructions and examples with XML tags.
- Ask for the answer, not for written reasoning. A `<thinking>` section or a reasoning field in the output can be refused on the newest models.
- Prefilled assistant turns are not supported; describe the output format or use structured outputs.
- For agents: name the steps that need no approval, give specific approvals, and for coding say whether the agent owns the code and should fix what it finds.
- Sources: [prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) and the per-model guides beside it, such as [Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2).

## GPT-6 (Astra, Sol) and Codex

- These models weigh instructions in skills and `AGENTS.md` heavily. State that the user's instructions take precedence over a skill's.
- They default to lists, tables and Markdown. Ask for concise paragraphs when prose is wanted.
- They test thoroughly and ask for clarification readily. For small tasks say how much testing is enough, and say when implied authorization is enough to proceed.
- They may delegate less than wanted. Say when to use subagents.
- Source: [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model). Its observations come from Astra; treat them as starting points for Sol.

## Other targets

- **Gemini:** Google had no Gemini 4 prompting guide at review. Use its current prompting strategies page.
- **Video:** OpenAI shut down Sora 2 and its Videos API on 2026-09-24. Ask which video tool the prompt is for.
