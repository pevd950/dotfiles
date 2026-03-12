# Structure and data flow

Use this as the first pass when refactoring or reviewing an existing SwiftUI file.

## Default architecture

- Default to SwiftUI-native MV: views express state, while services/models own business logic.
- Prefer `@State`, `@Environment`, `@Observable`, `@Bindable`, `@Query`, `.task`, and `onChange` over introducing a view model.
- Inject services and shared models via `@Environment`.
- Test models/services and business logic; keep views declarative and thin.

## When a view model is justified

Introduce a view model only when one or more of these are true:

- The screen has substantial orchestration or derived state that would otherwise sprawl across multiple helpers.
- The same coordination logic is reused across multiple screens.
- Legacy architecture, framework integration, or team conventions require it.

If a view model exists:

- Make it non-optional when possible.
- Initialize it in `init` from explicit dependencies.
- Store root `@Observable` models in `@State`.
- Avoid bootstrap-style setup such as `bootstrapIfNeeded`.

## File and type structure

- One type per file by default.
- If a view body grows beyond a screenful or mixes multiple logical sections, extract subviews.
- Prefer dedicated `View` structs over large computed view properties or helper methods returning `some View`.
- Keep tiny local view fragments inline only when extraction would hurt readability more than it helps.
- If extracting a subview clarifies ownership or behavior, give it its own file.

## File ordering

Within a SwiftUI view type, prefer this order:

1. Environment
2. `let` properties
3. `@State` and other stored properties
4. non-view computed properties
5. `init`
6. `body`
7. computed subviews / view helpers
8. helper and async functions

## Body rules

- Do not place non-trivial logic inside `body`.
- Pull button actions into methods or small helpers.
- Move sorting, filtering, formatting, decoding, and other repeated work out of `body`.
- Prefer explicit view types over deeply nested conditionals or large blocks of inline layout code.
- Prefer `Button` over `onTapGesture()` for tappable UI unless tap count or tap location is required.

## Observation and state ownership

- `@State` should usually be `private` and owned by the view that creates it.
- Pass state downward using `@Binding`, `@Bindable`, simple values, and callbacks.
- Use stable identity for `ForEach` and lists.
- Avoid `Binding(get:set:)` in `body` when a direct binding plus `onChange` is sufficient.
- Prefer environment injection for shared services and global app state.

## Practical refactor sequence

1. Reorder the file.
2. Move logic out of `body`.
3. Normalize state ownership and dependency injection.
4. Extract subviews.
5. Split multiple types into separate files.
6. Run API, navigation, accessibility, and review checklist passes.
