---
name: swiftui-performance-audit
description: Audit and improve SwiftUI runtime performance from code review and architecture. Use for requests to diagnose slow rendering, janky scrolling, high CPU/memory usage, excessive view updates, or layout thrash in SwiftUI apps, and to provide guidance for user-run Instruments profiling when code review alone is insufficient.
---

# SwiftUI Performance Audit

Start with a code-first review when code is available; move to user-run profiling only when review is inconclusive.

## Likely culprits

- View invalidation storms from broad state changes; broad dependencies in observable models — prefer granular models or per-item state to cut update fan-out.
- Unstable identity in lists: `id` churn, `UUID()` per render, `id: \.self` on non-stable values.
- Heavy work in `body`: formatter allocation, inline sorting or filtering in `body` or `ForEach`, computed properties that recompute per evaluation, image decoding on the main thread.
- Layout thrash: deep stacks, `GeometryReader`, long preference chains.
- Large images without downsampling; implicit animations over large trees.

## Fixes

Narrow state scope toward leaf views; stabilize `ForEach` identity; precompute and cache outside `body` (cached formatters, sorted/filtered collections updated on change); `equatable()` or value wrappers for expensive subtrees; decode and downsample images off the main thread; reduce layout complexity or use fixed sizing where possible.

## Profiling handoff

When review is inconclusive, ask the user to capture Instruments data: SwiftUI template on a Release build, reproduce the exact interaction, then share the SwiftUI lanes and Time Profiler call tree (export or screenshots) plus device/OS/build configuration. Treat trace timestamps as evidence and findings as hypotheses to confirm in code. After fixes, re-run the same capture and compare CPU, frame drops, and memory peak against the baseline.

## Output

Top issues ordered by impact with code references, proposed fixes with estimated effort, and a before/after metrics summary when captures exist.

## References

- Optimizing SwiftUI performance with Instruments: `references/optimizing-swiftui-performance-instruments.md`
- Understanding and improving SwiftUI performance: `references/understanding-improving-swiftui-performance.md`
- Understanding hangs in your app: `references/understanding-hangs-in-your-app.md`
- Demystify SwiftUI performance (WWDC23): `references/demystify-swiftui-performance-wwdc23.md`
