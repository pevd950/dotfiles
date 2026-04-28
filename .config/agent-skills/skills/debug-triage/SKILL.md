---
name: debug-triage
description: "Systematically reproduce, diagnose, and fix bugs; use when debugging failures, crashes, or test errors (trigger keywords: debug, bug, failure, crash, flaky test)."
---

# Debug Triage

## What this skill does
- Reproduces issues, isolates root causes, and applies minimal fixes.
- Verifies fixes with targeted tests and documents findings.
- Produces a concise bug report when reproduction is possible.
- Treats the feedback loop as the main debugging artifact: the faster and sharper the loop, the better the diagnosis.

## When to use it
- Trigger phrases: "debug", "bug", "failure", "crash", "flaky test".
- Use for runtime errors, test failures, or unexpected behavior.

## Step-by-step workflow
1) Gather context: expected vs actual behavior, error output, logs, environment details, and recent changes.
2) Build the smallest useful feedback loop before fixing. Prefer a failing test, HTTP script, CLI fixture, trace replay, focused harness, or structured human-in-the-loop script over manual inspection.
3) Minimize the repro until it isolates the symptom without changing the user-reported failure mode. A nearby but different failure is the wrong bug.
4) For hard or ambiguous bugs, form 3-5 ranked falsifiable hypotheses before editing. Each hypothesis should predict what evidence would confirm or disprove it.
5) Trace the code path and validate hypotheses with evidence from code, logs, debugger state, or targeted tests; rule out alternatives.
6) Instrument only where it distinguishes hypotheses. Change one variable at a time, tag temporary debug logs with a unique prefix, and remove throwaway probes before handoff.
7) Apply a minimal fix aligned with project patterns; avoid unrelated refactors.
8) Add regression coverage at the seam that reproduces the real bug pattern. If no correct seam exists, document that as a testing or architecture gap instead of adding a shallow false-confidence test.
9) Verify: rerun the original feedback loop and relevant tests; note any regression risks.
10) Document root cause, fix, tests, and remaining risks or follow-ups.

## Feedback loop options
- Failing unit, integration, API, UI, or end-to-end test.
- Curl or HTTP script against a running service.
- CLI invocation with fixture input and expected output.
- Replay of captured request, trace, log event, or payload.
- Throwaway harness around the smallest real code path.
- Stress or repetition loop for flaky bugs to increase reproduction rate.
- Commit, data, dependency, or configuration bisection when a regression window exists.
- Structured human-in-the-loop script only when no automated path can exercise the failure.

## Non-deterministic bugs
- Aim to raise the reproduction rate enough to debug, not to prove perfect determinism.
- Repeat, parallelize, seed, freeze time, isolate filesystem/network state, or inject timing pressure when those actions match the suspected failure mode.
- If no useful loop can be built, stop and report what was tried plus the missing artifact or access needed.

## Expected outputs / formatting
- Repro steps with expected vs actual behavior and observed output.
- Environment details (OS/version/config) when relevant.
- Feedback loop used and whether it is deterministic, flaky, or manual.
- Root cause explanation with file references.
- Hypotheses tested (brief) and evidence used.
- Fix summary and tests run.
- Remaining risks or follow-ups.

## Example prompts
- "Debug this crash and propose a fix."
- "Investigate why this test is failing."
- "Triage this flaky test and suggest a minimal change."
