---
name: performance-triage
description: Diagnose and improve performance with evidence. Use for slow requests, high CPU or memory, database slowness, streaming/backpressure issues, startup latency, throughput limits, or performance-sensitive code changes.
---

# Performance Triage

Measure before optimizing; never claim improvement from code inspection alone. Treat the measurement loop as a product — fast, sharp, deterministic. Optimize one bottleneck at a time and re-measure the same scenario.

## Loop

1. **Define the symptom:** what is slow or expensive, who observes it, operation and input size, environment and build mode, expected threshold, and whether it is cold-start, steady-state, spike-driven, or data-size dependent.
2. **Baseline.** If no measurement exists, create the smallest reliable one before changing code: reproducible timing, benchmark, profile or trace, duration logs, query plan, or resource metrics. Pin time, seed, data, and build mode; raise sample count when noisy; keep before/after comparable. For intermittent regressions, a higher-rate flaky repro is enough to debug — a one-off anecdote is not.
3. **Localize** with evidence, not style judgments: repeated work, N+1 round trips, algorithm or data-structure cost, query/index problems, serialization overhead, lock contention or backpressure, allocation/GC pressure, render invalidation, startup loading, or resource throttling. When a regression window exists, bisect commits, data shape, dependencies, or configuration before speculative edits.
4. **Fix in preference order:** avoid the work → shrink the input → batch, dedupe, coalesce, or paginate → better algorithm, data structure, query, or index → move off the hot path or make incremental → bounded cache only when repeated work and invalidation rules are clear → new infrastructure last, and only when measurements show code and data-shape fixes are insufficient. For any cache, document key/value, invalidation/TTL, size bound, staleness risk, and expected hit-rate signal.
5. **One focused change,** preserving observable behavior unless a change is approved.
6. **Re-measure** the same scenario; compare with units and environment; call out noise and unmeasured claims. Run the relevant functional tests.

## Handoff

Symptom and impact, baseline evidence, bottleneck hypothesis and evidence, change made, before/after numbers, correctness tests run, tradeoffs, and follow-up monitoring worth adding.

## Do not

- Add Redis, queues, workers, or services just because a path is slow.
- Optimize cold paths without real user or cost impact.
- Benchmark debug builds when release behavior matters.
- Mix unrelated cleanup with performance work.
