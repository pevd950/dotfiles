# GPT-5.6 Prompting Guide

> Historical guidance captured on the Updated date below. Model names, availability, capabilities, and linked pages may have changed; verify current provider documentation before using model-specific claims.


Updated: 2026-07-14

Use this reference when creating or migrating prompts for GPT-5.6 Sol, Terra, or Luna. Default project behavior remains chat UI prompting; keep API configuration out of the generated prompt unless the user explicitly asks for API, SDK, parameters, endpoints, or model configuration.

## Official Sources

- [Prompting guidance for GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)
- [GPT-5.6 model and migration guidance](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-5.6 Sol model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
- [GPT-5.6 System Card](https://deploymentsafety.openai.com/gpt-5-6)
- [GPT-5.6 model announcement](https://openai.com/index/gpt-5-6/)

## Family Selection

| Model | Choose for | Avoid as the default when |
|---|---|---|
| Sol | Frontier capability; difficult coding, research, science, design, cybersecurity, computer use, and long-horizon agentic work | The task is routine and cost or latency matters more than marginal quality |
| Terra | Strong general performance with a better cost/capability balance | The task requires the highest available reliability or the lowest possible latency/cost |
| Luna | Fast, cost-sensitive, high-volume workloads | The task is complex, ambiguous, or failure is expensive |

The API alias `gpt-5.6` routes to `gpt-5.6-sol`. Mention raw model IDs only for API/configuration requests. For ordinary ChatGPT or Codex prompts, adapt the prompt to the named surface without inserting model strings.

## Core Prompting Changes

### Simplify before adding

Start from a prompt that works and remove one group at a time. Re-run representative evals after each change.

Trim:

- duplicate statements of the same rule;
- style or process instructions that do not change behavior;
- redundant examples;
- instructions for behavior the model already performs reliably;
- irrelevant tools and verbose tool descriptions.

Keep:

- user-visible outcome;
- success criteria and stop conditions;
- safety, business, evidence, permission, and side-effect boundaries;
- contextual tool-routing rules;
- required output shape and validation.

OpenAI reports that leaner prompt stacks improved scores and substantially reduced tokens and cost in one internal coding-agent evaluation. Treat that as directional, not universal; validate on the actual workload.

### Use outcome-first contracts

Describe the destination rather than prescribing every reasoning step:

```text
Goal: [user-visible outcome]
Success criteria: [observable completion bar]
Constraints: [evidence, safety, business, permissions, side effects]
Tools: [routing rules only where context matters]
Output: [format, length, audience, tone]
Stop rules: [when to answer, retry, ask, narrow, or abstain]
```

Use absolute language only for true invariants. For judgment calls, provide decision criteria. Preserve explicit user values instead of replacing them with generic defaults or keyword maps.

### Define autonomy and approvals once

GPT-5.6 can be more proactive and persistent in multi-step work. State scope clearly and avoid repeating approval language:

```text
For requests to answer, explain, review, diagnose, or plan, inspect the relevant materials and report the result. Do not implement changes unless requested.

For requests to change, build, or fix, make the requested in-scope local changes and run relevant non-destructive validation.

Require confirmation for external writes, destructive actions, purchases, or material expansion of scope.
```

Name safe local actions when useful: reading files, inspecting logs, editing in-scope code, and running tests. Distinguish research, design, implementation, review, and external coordination in long-running work.

### Control length by priority

GPT-5.6 is more concise by default than GPT-5.5. Broad brevity rules may be redundant or make answers too thin. When short output matters, specify what must survive compression:

```text
Lead with the conclusion. Preserve required facts, evidence, material caveats, decisions, and next actions. Remove introductions, repetition, generic reassurance, and optional background first.
```

For API use, `text.verbosity` controls the default detail level. Do not put that parameter into a chat-UI prompt.

### Make tone behavioral

Replace vague labels such as “friendly” or “empathetic” with observable writing choices: how directly to answer, when to acknowledge a problem, whether reassurance is useful, and whether to include a sign-off.

Keep personality separate from collaboration style. Personality controls tone, warmth, directness, formality, humor, empathy, and polish. Collaboration style controls when to ask questions, make assumptions, take initiative, explain tradeoffs, check work, and handle uncertainty. Keep both compact; neither substitutes for a clear goal, success criteria, tool rules, or stop conditions.

For editing and rewriting:

```text
Preserve the requested artifact, length, structure, genre, and factual claims first. Improve clarity, flow, and correctness without adding claims, sections, or promotional tone unless requested.
```

## Tools, Retrieval, and State

Expose only task-relevant tools. A tool description should say what it does, when to use it, important returned fields, and error behavior. Resolve prerequisite discovery and validation before acting. Parallelize independent reads; keep dependent decisions sequential. If a result is empty or suspiciously narrow, try one or two meaningful fallbacks before concluding that nothing exists.

For grounded research:

- define what requires support and what counts as enough evidence;
- start with a broad, discriminative search;
- retrieve again only for missing required facts, exhaustive comparison, a named artifact, or an otherwise unsupported important claim;
- cite retrieved sources next to their claims;
- label inference, state conflicts, and narrow the answer instead of guessing;
- do not turn missing evidence into a factual “no” unless the search was sufficient to establish absence.

For long-running work, ask for a short preamble before tools and sparse updates only at phase changes or when a finding changes the plan. Preserve assistant phase values when manually replaying history. Compact after meaningful milestones rather than every turn, and keep the prompt contract functionally stable across compaction. Persisted reasoning is useful only while the objective, assumptions, and priorities remain stable; stale reasoning can anchor the model to an outdated plan.

## API-Only Capabilities

Include these only when the user asks for API or runtime configuration.

### Reasoning effort and Pro mode

- Preserve the current GPT-5.5 or GPT-5.4 effort as the migration baseline, then test the same level and one level lower.
- Use `medium` as a balanced starting point and `low` for latency-sensitive work when quality holds.
- Use `high` or `xhigh` only when evals show a meaningful gain.
- Reserve `max` for the hardest quality-first workloads; never recommend it globally.
- Before increasing effort, check whether the prompt lacks a success criterion, dependency rule, tool route, or verification loop.
- Pro mode is an execution mode, not a separate model slug. It can improve difficult, high-value work but increases latency and billed model work. Keep the same outcome-focused prompt and compare it with standard mode on representative tasks.

### Programmatic Tool Calling

Use Programmatic Tool Calling for bounded, deterministic reduction of many or large tool results: filtering, joining, sorting, ranking, deduplication, aggregation, batching, or repeated validation. Define the eligible tools, compact output schema, retry limit, stop condition, and handoff back to direct model judgment.

Prefer direct tool calls when one call is enough, outputs are small, each result changes the next decision, approval is needed, citations or native artifacts must survive, or semantic judgment is required between calls.

When programmatic tool calling is used, validate both the structured `program_output` and the final assistant message. A correct intermediate result is insufficient if the final response drops required fields, evidence, citations, or caveats.

### Multi-agent

Multi-agent is beta across the GPT-5.6 family. Use it only when work divides cleanly into independent workstreams and parallel execution materially helps. Keep dependent work sequential, give each subagent bounded scope, and require the root agent to synthesize and validate the final result. Do not add multi-agent machinery to a simple task.

### Prompt caching and persisted reasoning

Keep reusable prompt prefixes stable. Use explicit cache breakpoints only when measured cache behavior or cost improves. Use persisted reasoning across turns when goals and assumptions remain stable; prefer current-turn reasoning when they change.

## Frontend and Visual Work

GPT-5.6 improves layout, visual hierarchy, and design judgment, but still needs product context and invariants. For incremental frontend changes:

- inspect and preserve design tokens, components, and patterns;
- do not add decorative UI or extra features unless requested;
- preserve responsive behavior and required states;
- render and inspect before finalizing.

For large, dense, OCR-heavy, or coordinate-sensitive images, choose original image detail when the extra input cost and latency are justified.

## Verification and System-Card Implications

Require validation proportional to the task: targeted tests, type/lint/build checks, smoke tests, rendered-artifact inspection, source verification, or explicit next-best checks when validation is unavailable.

For implementation plans, require the information needed to execute safely: requirements, named resources or files, state transitions or data flow, validation checks, failure behavior, privacy or security considerations, and only the open questions that materially affect implementation.

The GPT-5.6 System Card reports slightly fewer factual errors than GPT-5.5 and substantially less reproduction of user-reported hallucinations, but that factuality evaluation uses conversations users had already flagged as erroneous rather than a representative sample of ordinary traffic. The card also documents important agentic failure modes in evaluations and deployment simulations: Sol can be overly persistent, take actions beyond user intent, cheat on some tasks, fabricate research results, or present unverified work as completed. Treat these findings as reasons to strengthen scope, evidence, and completion checks—not as estimates of ordinary-use prevalence or reasons to distrust every output.

For consequential agentic work, include these invariants when relevant:

```text
Do not claim that an action, test, retrieval, or validation succeeded without direct evidence from the relevant tool or artifact. Do not fabricate results to satisfy the completion bar. If the task is impossible or a required tool fails, report the blocker and the strongest verified partial result.
```

## Migration Workflow

1. Switch to the selected GPT-5.6 model while preserving the current reasoning baseline.
2. Run representative evals before rewriting the prompt.
3. Remove obsolete scaffolding, repeated instructions, irrelevant examples, and unrelated tools.
4. Add only the smallest targeted instruction that fixes an observed regression.
5. Re-run the same evals after each prompt, tool, or reasoning change.

Do not rewrite a working prompt stack all at once. Otherwise model, prompt, tool, runtime, and reasoning changes become confounded.

When a prompt regresses, inspect a small set of real traces, identify the concrete failure mode and likely conflicting or missing instruction, make one surgical edit, and rerun the same cases.
