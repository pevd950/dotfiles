# Navigation and presentation review

Run this pass when a change touches navigation, sheets, alerts, dialogs, or tab structure.

- Prefer `NavigationStack` or `NavigationSplitView`; flag deprecated `NavigationView`.
- Prefer `navigationDestination(for:)` over old `NavigationLink(destination:)` patterns in modern stacks.
- Do not mix `navigationDestination(for:)` and destination-based `NavigationLink` in the same hierarchy.
- Register each `navigationDestination(for:)` once per data type in a given hierarchy.
- Use enum-backed tab selection instead of integers or strings when `TabView(selection:)` is used.
- Prefer `sheet(item:)` when presenting optional data.
- When the sheet view accepts the item directly, prefer concise initializers such as `sheet(item: $selection, content: DetailView.init)`.
- Attach `confirmationDialog()` close to the control that triggers it.
- If an alert only dismisses with a single default action, omit the redundant button block.
- Keep modal and presentation state explicit and localized to the owner view or router.
