---
name: swiftui-ui-patterns
description: Primary SwiftUI build, review, and refactor skill. Use when creating SwiftUI UI, refactoring SwiftUI files, reviewing SwiftUI code for modern APIs and structure, designing tab/navigation architecture, or needing component-specific patterns and examples.
---

# SwiftUI UI Patterns

Default SwiftUI skill for new feature work, reviews, and refactors.

## Stance

- iOS 26 is the default deployment target unless the task says otherwise. SwiftUI-first; UIKit only when the codebase or request requires it.
- SwiftUI-native MV: `@State`, `@Binding`, `@Observable`, `@Bindable`, `@Environment`, `.task`, `onChange`. Introduce a view model only when orchestration is substantial, reused across surfaces, or forced by legacy/integration constraints.
- Keep actions, side effects, and non-trivial logic out of `body`. Prefer async/await with `.task` and explicit loading/error states.
- One type per file; extract long or complex sections into dedicated `View` types rather than large computed properties. Keep stored state `private` unless external access is required.
- Prefer `NavigationStack`/`NavigationSplitView`, modern `Tab`, current toolbar and navigation placements, and modern replacements for deprecated modifiers.
- Accessibility is part of the default review pass, not an add-on.
- Check nearby repo examples first and follow local conventions; maintain legacy patterns only when editing legacy files.

## Tracks

- **Existing project:** identify the screen and interaction model (list, detail, editor, settings, tabbed), find the closest repo example, apply local conventions, then load only the matching references from `references/components-index.md`.
- **Review or refactor:** start with `references/structure-and-data-flow.md`, then run passes with `references/modern-api-review.md`, `references/accessibility-review.md`, `references/navigation-and-presentation-review.md`, and `references/review-checklist.md`. Load only what the task needs.
- **New project scaffolding:** start with `references/app-wiring.md` for TabView + NavigationStack + sheets, add a minimal `AppTab` and `RouterPath` from the skeletons, and expand route and sheet enums as screens are added.

## Refactor priorities

1. Normalize state ownership and dependency injection.
2. Remove logic and side effects from `body`.
3. Extract complex sections into dedicated `View` types.
4. Split multiple types into separate files.
5. Modernize deprecated API and presentation patterns.
6. Quick accessibility and performance sanity pass.

## Component references

`references/components-index.md` is the entry point. When adding a reference, keep it short and actionable, link concrete files in the current repo, and update the index.

## Specialized follow-ups

`swiftui-liquid-glass` for Liquid Glass adoption or review; `apple-ui-design` for visual direction and HIG quality; `swiftui-performance-audit` when performance is the primary problem; `swift-concurrency-expert` for Swift 6.2+ concurrency.
