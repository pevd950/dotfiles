---
name: debug-triage
description: "Systematically reproduce, diagnose, and fix bugs; use when debugging failures, crashes, or test errors (trigger keywords: debug, bug, failure, crash, flaky test)."
---

# Debug Triage

Treat the feedback loop as the main debugging artifact: the faster and sharper the loop, the better the diagnosis.

## Workflow

1. Capture expected vs actual behavior, error output, environment, and recent changes.
2. Build the smallest useful feedback loop before fixing: failing test, HTTP script, CLI fixture, trace replay, or focused harness. A structured human-in-the-loop script is the last resort.
3. Minimize the repro without changing the reported failure mode — a nearby but different failure is the wrong bug.
4. For hard or ambiguous bugs, form 3-5 ranked falsifiable hypotheses before editing; each should predict the evidence that would confirm or disprove it.
5. Instrument only where it distinguishes hypotheses. Change one variable at a time, tag temporary debug logs with a unique prefix, and remove throwaway probes before handoff.
6. Apply a minimal fix aligned with project patterns; no unrelated refactors.
7. Add regression coverage at the seam that reproduces the real bug pattern. If no correct seam exists, document that as a testing or architecture gap instead of adding a shallow false-confidence test.
8. Rerun the original feedback loop and relevant tests.

## Non-deterministic bugs

Raise the reproduction rate enough to debug: repeat, parallelize, seed, freeze time, isolate filesystem/network state, or inject timing pressure matching the suspected failure mode. Bisect commits, data, dependencies, or configuration when a regression window exists. If no useful loop can be built, stop and report what was tried and the missing artifact or access.

## Report

Repro steps with expected vs actual output, feedback loop used (deterministic, flaky, or manual), root cause with file references, hypotheses tested, fix summary, tests run, and remaining risks.
