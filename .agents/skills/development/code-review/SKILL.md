---
name: code-review
description: Review code or PR diffs for correctness, security, tests, and architecture. Report actionable findings; use feedback skills when asked to implement fixes.
---

# Code Review

Review diffs for bugs, security risks, missing tests, and architecture drift. Prioritize high-severity findings over style, and adapt to repository patterns and local guidance instead of imposing generic conventions.

## Architecture lens

- Layering: entrypoints and adapters stay thin; business rules live in the owning domain layer; persistence, transport, UI, and provider code should not absorb product policy by accident.
- Dependency direction: core logic should not depend on transport, storage, UI, or vendor details unless the repo explicitly chose that tradeoff.
- Boundary quality: an abstraction earns its place by reducing caller knowledge, isolating volatility, normalizing errors, enforcing policy, or creating a stable test seam.
- Prefer deep modules with small public APIs. Flag shallow modules that only rename calls or pass parameters through.
- Interfaces belong at real boundaries, test seams, or multiple implementations — not speculation.
- Errors should be actionable at the source; logs should aid diagnosis without leaking sensitive data.
- Testability: behavior should be testable at the right layer without excessive mocks or hidden global state.

## Output

- Findings ordered by severity with file paths, short rationale, and a concrete fix each.
- Security items may cite CWE/OWASP when useful.
- Missing tests called out explicitly.
- Performance flagged only with evidence.
- Brief change summary after the findings, not before.
