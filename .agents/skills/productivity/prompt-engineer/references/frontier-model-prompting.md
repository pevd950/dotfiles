# Frontier-model prompting

Reviewed: 2026-10-01

## Evidence and model identity

OpenAI's current [Using GPT-6 guide](https://developers.openai.com/api/docs/guides/latest-model) explicitly lists GPT-6.1 Sol. Its [prompting section](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices) offers starting points across the GPT-6 family, based on behavior observed with GPT-6 Astra. Treat those observations as hypotheses to evaluate on the requested model and workload, not Sol-specific guarantees.

Honor the exact model the user names. A model label exposed by a local Codex picker establishes local availability only; verify public capabilities, API identifiers and parameter support separately in official documentation. Do not infer a dedicated model prompting page or API alias from a UI label. Recheck these live sources before introducing new model-specific claims.

## Prompt contract

Lead with the requested outcome, relevant source material, constraints, observable success criteria, and output format. Include only instructions that change behavior. Keep chat prompts free of API parameters unless API configuration is requested.

For agent work, distinguish analysis from implementation, define authorized side effects, and preserve earlier approval within its scope. Ask when missing input materially changes the result or authority; continue independent authorized work and prepare a concrete result before requesting a consequential approval. Audit loaded skills and instruction files for conflicting guidance; make precedence explicit.

Specify writing behavior concretely: audience, required evidence, length, prose or list structure, and what to retain when compressing. Avoid relying on a model's assumed default concision or copying every style rule into every prompt.

Calibrate testing to the change. Complete relevant checks, then broaden only for a new failure or unresolved concern. For consequential work require direct evidence of completion and a clear account of unavailable validation.

When delegation is authorized and available, define independent subtasks, ownership, integration and verification. Do not add subagents merely because the model supports them or let a generic template grant delegation authority.

## Migration and evaluation

Preserve a working baseline and representative tasks before changing the prompt. Test the named model with the same contract first. Then remove obsolete or conflicting instructions and make one targeted revision at a time. Compare task quality, tool behavior, permission boundaries, completion evidence, latency and cost where applicable. A prompt revision does not itself prove improved model performance.

Keep general task guidance separate from provider and model claims. For API requests, verify current reasoning, endpoint, tool and parameter compatibility in the official guide; do not copy historical settings or infer support from local Codex configuration. Prefer measured settings for the actual workload rather than a universal effort level.

## Other providers

Use the named provider's current official prompting documentation and evaluate the same outcome contract. Keep source material distinct from instructions, provide examples when format or judgment needs them, and avoid transferring unverified OpenAI capabilities or model names to another provider.
