---
name: architecture-scout
description: Proactively inspect a codebase area and propose architecture improvements, module-boundary fixes, decomposition opportunities, or small PR stacks. Use when asked to improve architecture, find cleanup candidates, decompose modules, or scout backend/frontend/system design work.
---

# Architecture Scout

Map before judging; propose scoped, reversible improvements instead of rewrites. Separate behavior-preserving refactors from behavior-changing redesign, and do not impose a generic style where the repo has a working local pattern. Use `code-review` for reviewing a specific diff.

## Smells to hunt

- Product policy hidden inside transport, persistence, provider, UI, or glue layers.
- Modules that know sibling internals; dependency direction that makes core code depend on adapters.
- Shallow modules that only rename parameters or forward calls; broad one-implementation interfaces with no real seam value.
- Duplicated business rules across call sites; long types with multiple reasons to change.
- Unclear ownership of validation, authorization, retries, errors, or observability.
- Hard-to-test code because effects are mixed with decisions; dead abstractions and unnecessary compatibility layers.

## Classify each candidate

**Delete** dead code / **Move responsibility** to the owning boundary / **Deepen module** behind a smaller public API / **Split module** with independent responsibilities / **Inline shallow abstraction** / **Add seam** to isolate external effects or hard-to-test policy / **Behavior change** — needs a product, API, or data-contract decision before refactoring.

## Shape PR slices

Behavior-preserving cleanup first when it reduces risk; characterization coverage before risky moves; one responsibility boundary per PR; behavior changes after structure is clear; deletion last, once compatibility risk is understood. For each slice: goal, files or modules touched, behavior impact, validation plan, dependency on earlier slices, rollback risk.

## Confidence

Report **High** (code evidence and validation path are clear), **Medium** (likely improvement, needs implementation proof or tests), or **Low** (smell observed; needs investigation or a product decision). Never present speculative redesign as confirmed architecture debt.

## Hard rules

- No interfaces without a real boundary, test seam, or multiple-implementation need.
- No extractions that only reduce line count.
- No mixing unrelated cleanup with a behavior change unless separation is impractical.
- Every claimed improvement must reduce caller knowledge, isolate volatility, improve tests, remove duplication, or enable a concrete next feature.
