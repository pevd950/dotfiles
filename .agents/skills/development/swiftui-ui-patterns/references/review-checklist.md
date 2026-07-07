# Review checklist

Use this as a quick final pass after structure, API, accessibility, and navigation checks.

## Performance sanity checks

- Avoid `AnyView` unless type erasure is truly required.
- Avoid expensive work in `body`, view initializers, and list builders.
- Avoid inline sorting/filtering/transforms in `ForEach` and `List` when they will repeat often.
- Prefer `LazyVStack` and `LazyHStack` for large scrollable collections.
- Prefer `task()` over `onAppear()` for async work.
- Use stable identities in lists and collections.

If performance is the main problem, switch to the `swiftui-performance-audit` skill.

## Hygiene checks

- Keep secrets and credentials out of the repository.
- Add comments only where logic is not self-evident.
- Ensure core application logic is testable and covered where appropriate.
- If the project uses `Localizable.xcstrings`, prefer the local string-catalog conventions already present in the repo.
- Prefer repo-local examples and conventions over generic sample-code structure when they differ.
