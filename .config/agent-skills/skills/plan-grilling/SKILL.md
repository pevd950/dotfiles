---
name: plan-grilling
description: Stress-test plans, designs, issue scopes, and architecture decisions before implementation. Use when the user asks to grill, challenge, sanity-check, shape, or decide a plan.
---

# Plan Grilling

## What this skill does
- Challenges plans against repo evidence, product goals, existing docs, and implementation constraints.
- Turns fuzzy ideas into explicit decisions, tradeoffs, assumptions, and failure modes.
- Asks only the questions that materially change the plan.

## When to use it
- Trigger phrases: "grill this", "grill me", "challenge this", "stress test", "sanity check", "shape this", "help decide", "what are we missing".
- Use for architecture decisions, feature plans, API contracts, issue shaping, PR direction, product behavior, or implementation strategy.
- Stay read-only unless the user explicitly asks to update an issue, PR, doc, or code.

## Default stance
- Be direct, not contrarian for sport.
- Resolve facts from code, docs, issues, or official references before asking the user.
- Ask one high-leverage question at a time when user input is genuinely needed.
- Include your recommended answer with each question so the user can accept, reject, or correct it quickly.
- Separate facts, assumptions, recommendations, open questions, and risks.

## Workflow

### 1. Anchor the plan
Capture:
- proposed change or decision
- user-facing goal
- affected systems, users, or workflows
- explicit constraints and non-goals
- current artifact to update, if any: issue, PR, doc, ADR, spec, or none

### 2. Read local evidence first
Before challenging details, inspect relevant local sources when available:
- local instructions such as `AGENTS.md`
- design docs, README files, runbooks, or product docs
- related issues, PRs, comments, and acceptance criteria
- existing code paths, tests, schemas, APIs, or UI surfaces
- official external docs only when repo evidence is insufficient or dependency behavior matters

Do not assume a repo has a glossary, ADR folder, or context map. If those artifacts exist and are relevant, use them. If they do not exist, proceed without ceremony.

### 3. Challenge terminology and scope
- Call out overloaded or fuzzy terms.
- Propose precise names for domain concepts, states, and boundaries.
- Distinguish product behavior from implementation detail.
- Identify where the plan mixes multiple deliverables that should be split.
- Check whether the artifact is scoped for a human, an implementation agent, or a future planning discussion.

### 4. Walk the decision tree
Resolve decisions in dependency order:
- What must be decided before anything else?
- Which decision changes the API, data model, UX, cost, security, or operational behavior?
- Which options are reversible vs expensive to undo?
- Which option best matches existing patterns?
- Which assumptions can be verified cheaply?

For each unresolved decision, provide:
- the question
- why it matters
- the recommended answer
- what changes if the user chooses differently

### 5. Stress-test with scenarios
Use concrete cases:
- happy path
- invalid input or misuse
- boundary size, scale, or timeout
- concurrency, retries, cancellation, or partial failure
- permission, ownership, privacy, or billing edge cases
- migration, rollout, rollback, and compatibility
- observability and debugging when it fails later

### 6. Decide artifact updates
Recommend updating durable artifacts only when useful:
- Issue body: when scope, AC, blockers, or validation changed.
- PR description/comment: when implementation direction or tradeoff changed during review.
- Repo docs/spec: when behavior is user-facing, cross-cutting, or needed by future agents.
- ADR: only when the decision is hard to reverse, surprising without context, and the result of a real tradeoff.

Do not create docs just because none exist.

When a GitHub issue or PR is already the active artifact, treat it as durable working memory. Recommend exactly what should be updated there so future agents do not need private chat context to continue.

## Expected outputs
- Concise summary of the plan as understood.
- Key facts discovered from local evidence.
- Recommended decision path.
- Blocking questions, one at a time when interaction is needed.
- Risks, failure modes, and missing validation.
- Suggested artifact updates, if any.

## Do not
- Do not endlessly interrogate low-impact details.
- Do not ask questions that code/docs can answer.
- Do not turn a small implementation task into a strategy exercise unless the plan is actually ambiguous or risky.
- Do not auto-create ADRs, glossaries, or docs unless asked.
- Do not present assumptions as facts.
