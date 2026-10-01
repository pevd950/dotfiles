# AI Prompting Best Practices

> Historical guidance captured on the Updated date below. Model names, availability, capabilities, and linked pages may have changed; verify current provider documentation before using model-specific claims.


Updated: 2026-07-10

Purpose: general source guidance for a ChatGPT project that turns rough ideas into paste-ready prompts for chat UI workflows. Default to ChatGPT/Codex-style use unless the user explicitly asks for API, SDK, endpoint, JSON, or parameter output.

## Default Assumptions

- The user usually wants a prompt they can paste into a chat UI.
- Do not include API parameters, model IDs, JSON payloads, endpoint names, seed, steps, CFG, or SDK fields unless explicitly requested.
- Prefer a strong final prompt over a long explanation.
- Ask clarifying questions only when missing context would materially change the result.
- If the user gives a rough idea, make reasonable assumptions and produce a polished prompt.

## Universal Prompt Shape

Use this structure for most text, research, writing, coding, or agent prompts:

```text
Goal:
[What the model should accomplish]

Context:
[Relevant background, audience, source material, constraints]

Instructions:
[Specific behavior, priorities, and boundaries]

Output:
[Format, length, tone, sections, examples if useful]

Success criteria:
[What a good answer must satisfy]
```

For quick user-facing prompts, collapse the sections into one clean paste-ready block.

## Current OpenAI / ChatGPT Guidance

For GPT-5.6 and modern ChatGPT/Codex workflows:

- Use outcome-first prompts: define the goal, success criteria, allowed side effects, evidence rules, and output shape.
- Simplify first. Remove repeated rules, examples, tools, and process instructions that do not change measured behavior.
- Avoid unnecessary step-by-step process instructions. Let the model choose the path unless the path itself matters.
- Be explicit about constraints that matter: audience, tone, length, source priority, tools, file safety, validation, and stopping conditions.
- Define autonomy and approval boundaries for agentic tasks. GPT-5.6 is more proactive and persistent, so distinguish read/review/diagnose work from authorized changes and from external, destructive, costly, or scope-expanding actions.
- GPT-5.6 is concise by default. Keep brevity instructions only when they produce a required output shape; specify what a short answer must retain.
- Use concise, direct wording. GPT-5.6 follows prompt contracts closely, so contradictory or overloaded prompts can be less stable than a shorter prompt.
- For coding agents, include repository conventions, validation expectations, file safety, and when to continue versus ask.
- For multi-step workflows, specify what evidence should be gathered and what final status should include.

Model-family selection:

- Sol: frontier capability for difficult professional, coding, research, design, and agentic work.
- Terra: strong capability with a better cost/performance balance.
- Luna: efficient, latency- or volume-sensitive work.

Do not insert API model IDs, reasoning settings, Pro mode, or multi-agent parameters into a chat-UI prompt unless the user explicitly asks for API or model configuration. See `gpt-5-6-prompt-guide.md` for the full distinction.

## Prompt Quality Checklist

Before returning a prompt, check:

- Clear goal
- Relevant context
- Non-conflicting constraints
- Output format
- Target model/app fit
- Reasonable length
- No generic filler
- No API-specific details unless requested

## Examples

Weak:

```text
Make this better and more professional.
```

Better:

```text
Rewrite the following message for a concise, professional Slack reply. Keep it friendly but direct, preserve all concrete facts, remove filler, and return only the final message.
```

Weak:

```text
Help me code this feature.
```

Better:

```text
You are working in an existing codebase. Inspect the relevant files first, identify the smallest safe implementation path, make the change, and verify it with focused tests or the closest available validation. Preserve unrelated local changes. In the final response, summarize changed files, validation run, and any remaining risk.
```

## Anti-Patterns

- Keyword stuffing
- Persona stacking
- Long generic rules that do not affect the result
- Asking for hidden chain-of-thought
- Conflicting tone or format instructions
- API payloads for chat UI use
- Overly broad "always" and "never" rules
- Excessive explanations when the user asked for a prompt

## Refresh Sources

- OpenAI prompt guidance: https://developers.openai.com/api/docs/guides/prompt-guidance
- OpenAI GPT-5.6 prompt guidance: https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6
- OpenAI GPT-5.6 model guidance: https://developers.openai.com/api/docs/guides/latest-model
- OpenAI GPT-5.6 System Card: https://deploymentsafety.openai.com/gpt-5-6
