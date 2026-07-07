---
name: performance-triage
description: Diagnose and improve performance with evidence. Use for slow requests, high CPU or memory, database slowness, streaming/backpressure issues, startup latency, throughput limits, or performance-sensitive code changes.
---

# Performance Triage

## What this skill does
- Turns performance work into an evidence-driven loop: baseline, localize, fix, re-measure.
- Helps avoid speculative optimizations and infrastructure-heavy fixes before proving the bottleneck.
- Applies across backend, frontend, UI, database, streaming, background jobs, and local tooling.

## When to use it
- Trigger phrases: "performance", "slow", "latency", "throughput", "CPU", "memory", "allocation", "profiling", "benchmark", "timeout", "streaming is sluggish", "database is slow".
- Use when the task is primarily about runtime cost, responsiveness, scaling, resource use, or a performance-sensitive change.

## Default stance
- Measure before optimizing. If no baseline exists, create the smallest reliable measurement before changing code.
- Treat the measurement loop as a product: make it faster, sharper, and more deterministic before relying on it.
- Optimize one bottleneck at a time, then re-measure the same scenario.
- Prefer simple code or data-shape fixes before caching, queues, or new infrastructure.
- Preserve correctness. Run relevant functional tests after performance changes.
- Adapt to the repository's documented workflow and preferred profiler/test tools.

## Workflow

### 1. Define the symptom
Capture:
- What is slow, expensive, or resource-heavy.
- Who observes it: user, API caller, worker, UI, CI, database, or operator.
- Operation, input size, environment, build mode, and expected threshold.
- Whether the issue is cold-start, steady-state, spike-driven, or data-size dependent.

Classify the problem:
- latency
- throughput
- CPU
- memory or allocations
- startup or initialization
- database/query
- streaming or long-lived connection
- rendering/layout
- background job or queue
- external dependency/provider
- infrastructure/resource limit

### 2. Establish a baseline
Collect at least one concrete signal:
- wall-clock timing from a reproducible command or request
- benchmark result
- profiler or trace
- logs with durations/request IDs
- database query plan or slow-query log
- resource metrics such as CPU, memory, goroutines/threads, file descriptors, or queue depth
- a focused reproduction script or fixture

If the task lacks measurements, pause implementation long enough to add or run the smallest useful measurement.

Then improve the loop when practical:
- make it faster by narrowing setup or input size while preserving the symptom
- make it sharper by asserting on the specific slow path or resource signal
- make it more deterministic by pinning time, seed, data, build mode, environment, or dependency versions
- increase sample count when the signal is noisy
- keep before/after measurements comparable

For intermittent regressions, the goal is enough reproduction rate or statistical confidence to debug. A higher-rate flaky loop is useful; a one-off anecdote is not.

### 3. Localize the bottleneck
Identify the primary suspect and evidence:
- unnecessary or repeated work
- N+1 calls or excessive round trips
- inefficient algorithm or data structure
- database query/indexing issue
- serialization/deserialization overhead
- network/provider latency
- lock contention, backpressure, cancellation, or concurrency leak
- allocation or GC pressure
- rendering/layout invalidation
- startup dependency loading
- infrastructure/resource throttling

Do not treat code style as root cause unless it explains the measured cost.

When a regression window exists, consider bisection across commits, data shape, dependency version, configuration, model/provider routing, or infrastructure changes before making speculative code edits.

For performance regressions, prefer timing, profiling, traces, query plans, or resource metrics over log-only diagnosis. Logs are useful when they provide durations, counts, IDs, or boundary timing that distinguish hypotheses.

### 4. Choose the fix strategy
Prefer fixes in this order:
1. Avoid unnecessary work.
2. Reduce input size or replayed context.
3. Batch, dedupe, coalesce, or paginate work.
4. Improve algorithm, data structure, query, or index.
5. Move work off the hot path or make it incremental.
6. Add a bounded cache only when repeated work and invalidation rules are clear.
7. Add infrastructure only when measurements show code/data-shape fixes are insufficient.

For caches, document:
- cached key and value
- invalidation/TTL
- maximum size or memory bound
- correctness risk if stale
- expected hit-rate signal

### 5. Implement one change
- Keep the diff focused on the chosen bottleneck.
- Avoid broad refactors during measurement unless the refactor directly removes the bottleneck.
- Preserve observable behavior unless the user explicitly approves a behavior change.
- Add benchmarks, regression tests, or logging only when they will keep the fix verifiable.

### 6. Re-measure
Run the same baseline scenario after the change.
Compare before/after with units and environment.
Call out measurement noise, confidence, and any unmeasured claims.

### 7. Final handoff
Include:
- symptom and user/operator impact
- baseline evidence
- bottleneck hypothesis and evidence
- change made
- before/after result
- correctness tests run
- tradeoffs and remaining risks
- follow-up measurements or monitoring to add if needed

## Tooling examples
- Go: `go test -bench`, `pprof`, `trace`, allocation profiles, goroutine dumps.
- Databases: `EXPLAIN ANALYZE`, slow-query logs, index inspection, query count logs.
- Web/API: request logs, load scripts, timing headers, OpenTelemetry traces.
- Apple platforms: Instruments, Time Profiler, SwiftUI template, hangs and memory instruments.
- General systems: CPU/memory graphs, flamegraphs, queue depth, file descriptor counts, thread counts.

## Do not
- Do not add Redis, queues, workers, or new services just because a path is slow.
- Do not optimize cold paths unless the user impact or cost is real.
- Do not claim improvement from code inspection alone.
- Do not mix unrelated cleanup with performance work.
- Do not benchmark debug builds when release or production behavior matters.
- Do not ignore correctness tests after changing a performance-sensitive path.
