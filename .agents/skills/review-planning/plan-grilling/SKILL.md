---
name: plan-grilling
description: Stress-test plans, designs, issue scopes, and architecture decisions before implementation. Use when the user asks to grill, challenge, sanity-check, shape, or decide a plan.
---

# Plan Grilling

Challenge plans against repo evidence, product goals, and implementation constraints. Be direct, not contrarian for sport. Stay read-only unless the user explicitly asks to update an issue, PR, doc, or code.

## Stance

- Resolve facts from code, docs, issues, or official references before asking the user; never ask what the repo can answer.
- Ask one high-leverage question at a time, and include your recommended answer so the user can accept, reject, or correct quickly.
- Separate facts, assumptions, recommendations, open questions, and risks.
- Do not turn a small implementation task into a strategy exercise unless the plan is genuinely ambiguous or risky, and do not interrogate low-impact details.

## Method

1. **Anchor:** proposed change or decision, user-facing goal, affected systems and workflows, explicit constraints and non-goals, and the current artifact to update (issue, PR, doc, ADR, spec, or none).
2. **Challenge terminology and scope:** call out overloaded or fuzzy terms, propose precise names for domain concepts and boundaries, distinguish product behavior from implementation detail, split mixed deliverables, and check whether the artifact is scoped for a human, an implementation agent, or a future planning discussion.
3. **Walk decisions in dependency order:** what must be decided first; which decisions change the API, data model, UX, cost, security, or operational behavior; which options are reversible vs expensive to undo; which match existing patterns; which assumptions can be verified cheaply. For each unresolved decision give the question, why it matters, the recommended answer, and what changes if the user chooses differently.
4. **Stress-test with concrete scenarios:** invalid input and misuse, boundary size/scale/timeouts, concurrency, retries, cancellation and partial failure, permission/ownership/privacy/billing edges, migration/rollout/rollback and compatibility, and observability when it fails later.

## Artifact updates

Recommend durable updates only where they earn their keep: issue body when scope, acceptance criteria, blockers, or validation changed; PR description or comment when implementation direction or tradeoffs changed during review; repo docs when behavior is user-facing or cross-cutting; ADR only for hard-to-reverse, surprising-without-context, real-tradeoff decisions. When a GitHub issue or PR is the active artifact, treat it as durable working memory — say exactly what to update so future agents do not need private chat context. Do not create docs just because none exist, and do not present assumptions as facts.
