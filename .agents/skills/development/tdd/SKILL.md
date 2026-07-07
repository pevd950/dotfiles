---
name: tdd
description: Use test-driven development for new behavior, bug fixes, API contracts, and safe refactors. Trigger when the user asks for TDD, test-first work, regression tests, characterization tests, or red-green-refactor.
---

# Test-Driven Development

## What this skill does
- Drives implementation with a small failing test before production code when practical.
- Uses regression tests to prove bug fixes.
- Uses characterization tests to protect behavior before risky refactors.
- Keeps the validation loop fast while still finishing with relevant broader checks.

## When to use it
- Trigger phrases: "TDD", "test first", "write the failing test", "red green refactor", "regression test", "characterization test".
- Use when behavior can be exercised through a stable seam: public API, service boundary, UI interaction, command, integration point, or observable output.
- Do not force TDD for pure docs, trivial generated-code sync, mechanical renames, or exploratory spikes where the correct seam is not yet known.

## Default stance
- Test behavior, not private implementation details.
- Prefer the smallest test that proves the requirement or reproduces the bug.
- Keep tests readable enough to serve as executable documentation.
- Run focused tests during the loop; run broader relevant validation before handoff.
- Refactor only after tests are green.

## Workflow

### 1. Pick the test seam
Choose the highest-value seam:
- API contract or HTTP handler
- service or domain boundary
- repository or persistence behavior
- command-line behavior
- UI flow or view model behavior
- provider/client adapter
- integration workflow

Avoid testing private helpers directly unless no public seam exists and the helper is the real stable contract.

### 2. Write the failing test
For new behavior:
- encode one acceptance criterion
- assert observable output, state, side effect, or error shape
- keep setup minimal but realistic

For bugs:
- reproduce the reported failure as a regression test
- include the smallest input that still represents the real bug
- name the test after the behavior, not the implementation mistake

For refactors:
- add characterization coverage before moving code when existing tests are weak
- capture current intended behavior, not accidental quirks unless compatibility requires them

### 3. Verify red
- Run the narrowest relevant test command.
- Confirm it fails for the expected reason.
- If it passes unexpectedly, the test is not proving the intended behavior; adjust the seam or assertion.
- If it fails for setup noise, fix the test harness before production code.

### 4. Make it green
- Write the smallest production change that satisfies the test.
- Do not broaden scope while red.
- Keep error messages and edge cases explicit when they are part of the contract.
- Re-run the focused test until green.

### 5. Refactor
- Clean up duplicated setup, awkward APIs, or misplaced responsibility only after green.
- Keep tests green after each structural step.
- Avoid unrelated refactors unless they directly support the tested change.

### 6. Expand coverage only where useful
Add more tests when they cover real risk:
- invalid input
- permissions or authorization
- missing dependencies
- concurrency or cancellation
- serialization/schema compatibility
- boundary sizes and limits
- provider/network failure
- migration/rollback behavior

Do not add broad snapshot or brittle implementation tests just to increase count.

### 7. Final validation
- Run the focused test command used during the loop.
- Run the broader relevant suite for the touched surface.
- Report any tests not run and why.

## Expected outputs
- Test seam chosen and why.
- Failing test added and expected failure.
- Production change summary.
- Refactor summary, if any.
- Focused and broader validation commands with results.
- Remaining risks or missing seams.

## Coordination with other skills
- For API endpoint work, combine with `api-contract-testing`.
- For bug fixing, combine with `debug-triage` after a repro path is identified.
- For refactors, combine with `architecture-scout` when the boundary move needs planning.
- For code review, use `code-review` to evaluate whether tests cover behavior rather than implementation.

## Do not
- Do not claim TDD if no failing test was observed.
- Do not write production code first unless the user explicitly accepts test-after or the seam must be discovered through a spike.
- Do not mock the system under test so heavily that the test only proves the mock.
- Do not test private implementation details when a public behavior seam exists.
- Do not leave characterization tests that encode known-bad behavior unless the issue explicitly requires compatibility.
