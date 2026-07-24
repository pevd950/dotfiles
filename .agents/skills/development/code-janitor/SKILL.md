---
name: code-janitor
description: "Clean up codebases by removing dead code, simplifying logic, and reducing tech debt; use when asked to refactor for simplicity, delete unused code, or tidy dependencies (trigger keywords: cleanup, refactor, tech debt, simplify, remove unused)."
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
