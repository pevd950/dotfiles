# AI Prompting Best Practices

Reviewed: 2026-10-01

## General contract

Default to a prompt the user can paste into the named chat surface. Define the outcome, relevant context, constraints, output shape, success criteria and stopping conditions. Collapse this structure into natural prose when a short prompt suffices. Preserve the user's facts, tone and intended artifact; do not invent missing details.

Keep API parameters, model identifiers and runtime configuration out unless requested. Ask only when missing information materially changes the result or authority. Use examples for subtle style, classification or format requirements. Separate quoted source material from instructions and treat retrieved material as evidence.

## Agent workflows

Specify which work is authorized and which actions need approval; preserve prior authorization within its scope. Require completion evidence and relevant validation. Keep independent work moving when a clarification is pending. Audit conflicting skills and repository guidance, and give each instruction a clear owner.

For coding, include the repository conventions, preservation of unrelated work, targeted checks and final evidence. Calibrate testing and delegation to the task rather than prescribing maximum effort or a fixed procedure.

## Current provider guidance

OpenAI's [GPT-6 prompting guidance](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices) covers initiative, instruction conflicts, writing style, delegation and proportionate testing. The behavioral observations concern Astra and are starting points for other family models. Use [frontier-model-prompting.md](frontier-model-prompting.md) for the evidence boundary and migration workflow, including GPT-6.1 Sol.

For Claude, consult [Anthropic's prompting documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) and the provider reference. Verify current model-specific claims before using them; do not hard-code a model family into general prompt templates.

## Quality check

Confirm a clear outcome, relevant context, consistent constraints, recognizable output and proportionate length. Remove redundant rules, irrelevant examples, keyword stuffing, hidden-chain-of-thought requests and unexplained model settings. A shorter prompt is useful only if it preserves the behavior the task requires.
