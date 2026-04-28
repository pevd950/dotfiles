---
name: architecture-scout
description: Proactively inspect a codebase area and propose architecture improvements, module-boundary fixes, decomposition opportunities, or small PR stacks. Use when asked to improve architecture, find cleanup candidates, decompose modules, or scout backend/frontend/system design work.
---

# Architecture Scout

## What this skill does
- Maps a codebase area before proposing architectural changes.
- Identifies misplaced responsibility, leaky boundaries, shallow modules, dependency-direction problems, and hard-to-test seams.
- Produces scoped improvement candidates and PR stacks instead of broad rewrites.

## When to use it
- Trigger phrases: "architecture", "improve codebase", "decompose", "module boundary", "clean architecture", "shallow module", "monolith", "scout", "find cleanup candidates".
- Use for proactive architecture planning, issue discovery, implementation slicing, and design-risk analysis.
- Do not use as a replacement for normal code review; use `code-review` when reviewing a specific diff.

## Default stance
- Understand the current design before judging it.
- Prefer small, reversible improvements that make the next feature easier.
- Separate behavior-preserving refactors from behavior-changing redesign.
- Reject cosmetic extractions that only rename or pass through behavior.
- Do not impose a generic architecture style when the repo has a working local pattern.

## Workflow

### 1. Anchor the target
Clarify:
- area, feature, module, or workflow being inspected
- user goal: speed, maintainability, testing, extensibility, reliability, deletion, or decomposition
- constraints: release risk, validation budget, parallel PRs, or no-code planning
- expected output: findings, issue plan, PR stack, or implementation

### 2. Map the current architecture
Inspect enough code to describe:
- entrypoints and external interfaces
- core domain objects or data flow
- dependencies and direction of calls
- persistence, network, UI, provider, or infrastructure boundaries
- ownership of business rules and product policy
- tests and validation seams
- generated code, framework constraints, and legacy compatibility paths

Prefer local repo docs and instructions first. Use official external docs only when framework or dependency behavior matters.

### 3. Identify architecture smells
Look for:
- product policy hidden inside transport, persistence, provider, UI, or glue layers
- modules that know too much about sibling internals
- dependency direction that makes core code depend on adapters
- shallow modules that only rename parameters or forward calls
- duplicated business rules across call sites
- long functions or types with multiple reasons to change
- unclear ownership of validation, authorization, retries, errors, or observability
- hard-to-test code because effects are mixed with decisions
- unnecessary compatibility layers or dead abstractions
- broad interfaces with one implementation and no real seam value

### 4. Classify candidates
For each candidate, classify:
- **Delete**: remove dead, unused, or obsolete code.
- **Move responsibility**: put behavior at the owning boundary.
- **Deepen module**: hide meaningful behavior behind a smaller public API.
- **Split module**: separate independent responsibilities.
- **Inline shallow abstraction**: remove indirection that does not pay for itself.
- **Add seam**: isolate external effects, slow dependencies, or hard-to-test policy.
- **Behavior change**: requires product/API/data contract decision before refactor.

### 5. Shape PR slices
Prefer small sequences:
- behavior-preserving cleanup first when it reduces risk
- tests or characterization coverage before risky moves
- one responsibility boundary per PR
- behavior changes after structure is clear
- deletion at the end when compatibility risk is understood

For each slice, include:
- goal
- files or modules likely touched
- behavior impact
- validation plan
- dependency on earlier slices
- rollback risk

### 6. Report confidence
Use confidence levels:
- **High confidence**: code evidence and validation path are clear.
- **Medium confidence**: likely improvement, but needs implementation proof or tests.
- **Low confidence**: smell observed, but more investigation or product decision needed.

Do not present speculative redesign as confirmed architecture debt.

## Expected outputs
- Current architecture map.
- Findings ordered by impact and confidence.
- Recommended issue/PR slices with validation plans.
- Explicit distinction between safe refactors and behavior changes.
- Open questions or human decisions required.

## Do not
- Do not propose broad rewrites without a staged migration path.
- Do not extract helpers just to reduce line count.
- Do not introduce interfaces unless there is a real boundary, multiple implementation need, testing seam, or external dependency isolation.
- Do not mix unrelated cleanup with a behavior change unless the coupling makes separation impractical.
- Do not claim improvements without explaining how they reduce caller knowledge, isolate volatility, improve tests, remove duplication, or enable a concrete next feature.
