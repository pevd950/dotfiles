---
name: code-janitor
description: Remove dead code and simplify existing implementations or dependencies when asked for cleanup or refactoring.
---

# Code Janitor

Remove dead code, redundant logic, and unnecessary abstractions with minimal, safe diffs.

- Confirm code is actually unused before deleting: check dynamic references, reflection, exports, and generated callers.
- Prefer deletion and inlining over rearranging. Flatten conditionals; inline single-use helpers.
- Prune unused dependencies and config only when removal is provably safe.
- Update or remove comments and docs tied to removed code.
- Keep cleanup separate from behavior changes; avoid scope creep.
- Validate with focused tests or checks after each removal batch.

Report removals and simplifications with file references, tests run, remaining risks, and any larger refactors deliberately deferred.
