---
name: prd-writer
description: Turn fuzzy product ideas, notes, or feature concepts into lightweight product requirements documents before implementation planning. Use when asked for a PRD, product spec, requirements doc, feature brief, or product plan.
---

# PRD Writer

## What this skill does
- Converts rough product intent into a clear, lightweight product requirements document.
- Separates product decisions from implementation details.
- Identifies open questions, risks, rollout concerns, and later issue candidates.

## When to use it
- Trigger phrases: "PRD", "product requirements", "product spec", "feature brief", "requirements doc", "shape this product idea".
- Use before backlog decomposition when the user-facing behavior, goals, or non-goals are not stable yet.
- Do not create GitHub issues by default; use `backlog-planner` after the PRD is accepted or when the user asks to file issues.

## Default stance
- Keep the PRD as light as the decision requires.
- Prefer concrete user flows over abstract feature lists.
- Separate facts, assumptions, decisions, and open questions.
- Do not turn unknown product choices into fake engineering requirements.
- Do not assume a fixed docs folder or template unless the repo provides one.

## Workflow

### 1. Capture intent
Identify:
- target users or actors
- problem being solved
- current pain or opportunity
- desired user outcome
- why now
- known constraints: platform, cost, policy, timing, technical, operational, legal, or support

### 2. Define scope
Write:
- goals
- non-goals
- v1 scope
- future work
- explicit out-of-scope items
- assumptions that need validation

### 3. Describe core flows
For each important flow, capture:
- trigger or entry point
- user action
- system behavior
- success state
- failure or empty state
- permissions, limits, or eligibility
- observability or support needs when something goes wrong

### 4. Specify requirements
Group requirements as needed:
- Product behavior
- UX requirements
- Data, API, or integration needs
- Admin, support, or operations needs
- Privacy, security, abuse, or compliance considerations
- Performance, reliability, or cost constraints
- Migration, rollout, and rollback expectations

### 5. Define acceptance and success
Include:
- acceptance criteria for v1
- manual validation scenarios
- metrics or qualitative success signals
- launch or rollout gates
- known risks and mitigations

### 6. Prepare for decomposition
Identify likely future issues without filing them unless asked:
- backend/API
- client/UI
- data model or migration
- infra/ops
- instrumentation
- docs/support
- follow-up polish

Flag blockers and human decisions separately from implementation tasks.

## Suggested PRD outline
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

## Expected outputs
- A concise PRD or feature brief.
- Explicit goals, non-goals, and v1 scope.
- User flows and acceptance criteria.
- Open questions and human decisions.
- Suggested follow-up issue areas when decomposition is useful.

## Do not
- Do not over-specify implementation before product behavior is clear.
- Do not create broad epics or issues unless the user asks.
- Do not invent metrics when no realistic signal exists; propose candidate signals instead.
- Do not hide uncertainty. Mark unknowns as open questions.
