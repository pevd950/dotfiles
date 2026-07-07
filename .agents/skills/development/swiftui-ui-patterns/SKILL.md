---
name: swiftui-ui-patterns
description: Primary SwiftUI build, review, and refactor skill. Use when creating SwiftUI UI, refactoring SwiftUI files, reviewing SwiftUI code for modern APIs and structure, designing tab/navigation architecture, or needing component-specific patterns and examples.
---

# SwiftUI UI Patterns

Use this as the default SwiftUI skill for new feature work, reviews, and refactors.

## Default stance

- iOS 26 is the default deployment target unless the task says otherwise.
- Prefer SwiftUI-first solutions and avoid UIKit unless the codebase or request requires it.
- Check nearby repo examples first, then apply the rules in this skill.
- Default to SwiftUI-native MV using `@State`, `@Observable`, `@Environment`, `.task`, and `onChange`.
- Keep actions, side effects, and non-trivial logic out of `body`.
- One type per file by default.
- Extract long or complex subviews into dedicated `View` types rather than large computed view properties.
- Introduce a view model only when orchestration is substantial, reused across surfaces, or forced by legacy/integration constraints.

## Quick start

Choose a track based on your goal:

### Existing project

- Identify the feature or screen and the primary interaction model (list, detail, editor, settings, tabbed).
- Find a nearby example in the repo with `rg "TabView\("` or similar, then read the closest SwiftUI view.
- Apply local conventions first, then load the relevant review references from `references/components-index.md`.
- Build with small, focused views, SwiftUI-native data flow, and explicit ownership of state.

### Review or refactor

- Start with `references/structure-and-data-flow.md` to normalize file structure, state ownership, and extraction rules.
- Run quick review passes with `references/modern-api-review.md`, `references/accessibility-review.md`, `references/navigation-and-presentation-review.md`, and `references/review-checklist.md`.
- Only load the references that match the task to keep context small.

### New project scaffolding

- Start with `references/app-wiring.md` to wire TabView + NavigationStack + sheets.
- Add a minimal `AppTab` and `RouterPath` based on the provided skeletons.
- Choose the next component reference based on the UI you need first (TabView, NavigationStack, Sheets).
- Expand the route and sheet enums as new screens are added.

## General rules to follow

- Use modern SwiftUI state (`@State`, `@Binding`, `@Observable`, `@Bindable`, `@Environment`) and avoid unnecessary view models.
- Prefer composition; keep views small, focused, and split into dedicated types as they grow.
- Keep stored state `private` unless external access is required.
- Prefer async/await with `.task` and explicit loading/error states.
- Prefer `NavigationStack`/`NavigationSplitView`, modern `Tab`, and current toolbar/navigation placements.
- Prefer modern API replacements over deprecated modifiers and wrappers.
- Treat accessibility as part of the default review pass, not an optional add-on.
- Maintain existing legacy patterns only when editing legacy files.
- Follow the project's formatter and style guide.

## Workflow for a new SwiftUI change

1. Define the view's state and its ownership location.
2. Identify dependencies to inject via `@Environment`.
3. Choose the relevant component reference from `references/components-index.md`.
4. Sketch the view hierarchy and extract repeated or complex parts into dedicated subview types.
5. Implement async loading with `.task` and explicit state enum if needed.
6. Run the relevant review passes for API, accessibility, navigation, and structure.
7. Add accessibility labels or identifiers when the UI is interactive.
8. Validate with a build and update usage callsites if needed.

## Refactor priorities

When cleaning up an existing SwiftUI file, prefer this order:

1. Normalize state ownership and dependency injection.
2. Remove logic and side effects from `body`.
3. Extract complex sections into dedicated `View` types.
4. Split multiple types into separate files.
5. Modernize deprecated API and presentation patterns.
6. Run a quick accessibility and performance sanity pass.

## Component references

Use `references/components-index.md` as the entry point. Each component reference should include:
- Intent and best-fit scenarios.
- Minimal usage pattern with local conventions.
- Pitfalls and performance notes.
- Paths to existing examples in the current repo.

## Adding a new component reference

- Create `references/<component>.md`.
- Keep it short and actionable; link to concrete files in the current repo.
- Update `references/components-index.md` with the new entry.

## Specialized follow-ups

- Use `swiftui-liquid-glass` for Liquid Glass adoption or review.
- Use `apple-ui-design` for stronger visual direction and Apple-platform design quality.
- Use `swiftui-performance-audit` when performance is the primary problem.
- Use `swift-concurrency-expert` for Swift 6.2+ concurrency diagnostics or fixes.
