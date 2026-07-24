---
name: prd-writer
description: Turn fuzzy product ideas, notes, or feature concepts into lightweight product requirements documents before implementation planning. Use when asked for a PRD, product spec, requirements doc, feature brief, or product plan.
---

# PRD Writer

Keep the PRD as light as the decision requires. Prefer concrete user flows over abstract feature lists; separate facts, assumptions, decisions, and open questions; never turn unknown product choices into fake engineering requirements. Do not assume a docs folder or template unless the repo provides one, and do not file issues — use `backlog-planner` after the PRD is accepted or when the user asks.

## What to capture

- **Intent:** actors, problem, current pain, desired outcome, why now, and real constraints (platform, cost, policy, timing, technical, operational, legal, support).
- **Scope:** goals, non-goals, v1 scope, future work, explicit out-of-scope items, and assumptions needing validation.
- **Core flows**, each with trigger or entry point, user action, system behavior, success state, failure/empty state, permissions or limits, and observability or support needs when something goes wrong.
- **Requirements**, grouped as needed: product behavior; UX; data, API, or integration; admin, support, or operations; privacy, security, abuse, compliance; performance, reliability, cost; migration, rollout, rollback.
- **Acceptance and success:** v1 acceptance criteria, manual validation scenarios, success signals — propose candidate signals rather than inventing metrics no realistic signal supports — plus launch gates, risks, and mitigations.
- **Decomposition prep:** likely future issue areas (backend/API, client/UI, data model or migration, infra/ops, instrumentation, docs/support, polish), with blockers and human decisions flagged separately from implementation tasks.

## Outline

```markdown
# Title

## Overview
## Problem
## Users
## Goals
## Non-Goals
## V1 Scope
## Core Flows
## Requirements
## Acceptance Criteria
## Rollout / Migration
## Risks
## Success Signals
## Open Questions
## Future Work
```

Mark unknowns as open questions instead of hiding uncertainty, and keep implementation detail out until product behavior is clear.
