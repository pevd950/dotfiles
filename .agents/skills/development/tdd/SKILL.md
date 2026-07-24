---
name: tdd
description: Use test-driven development for new behavior, bug fixes, API contracts, and safe refactors. Trigger when the user asks for TDD, test-first work, regression tests, characterization tests, or red-green-refactor.
---

# Test-Driven Development

Drive implementation with a small failing test before production code. Do not force TDD for docs, mechanical renames, generated-code sync, or spikes where the right seam is not yet known.

## Loop

1. **Pick the seam.** Test behavior through a stable public boundary: API contract, service or domain boundary, persistence behavior, CLI, UI flow or view model, adapter, or integration workflow. Avoid testing private helpers unless no public seam exists and the helper is the real contract.
2. **Write the failing test.** One acceptance criterion; assert observable output, state, side effect, or error shape. For bugs, reproduce the reported failure as a regression test named after the behavior. For refactors, add characterization coverage first — capture intended behavior, not accidental quirks, unless compatibility requires them.
3. **Verify red.** Confirm it fails for the expected reason. Passing unexpectedly means the test proves nothing; failing on setup noise means fix the harness before production code.
4. **Make it green** with the smallest production change. Do not broaden scope while red.
5. **Refactor** only after green, keeping tests green after each structural step.
6. **Expand coverage only for real risk:** invalid input, authorization, missing dependencies, concurrency and cancellation, serialization compatibility, boundary sizes and limits, provider failure, migration/rollback. No brittle snapshot or implementation tests just to increase count.
7. **Final validation:** the focused command, then the broader suite for the touched surface. Report anything not run and why.

## Hard rules

- Do not claim TDD if no failing test was observed.
- Do not mock the system under test so heavily that the test only proves the mock.
- Do not leave characterization tests that encode known-bad behavior unless compatibility explicitly requires it.

Related: `api-contract-testing` for endpoints, `debug-triage` for repro paths, `architecture-scout` for boundary moves, `code-review` for evaluating test quality.
