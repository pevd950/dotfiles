# Accessibility review

Run this pass for interactive or user-facing SwiftUI changes.

- Respect Dynamic Type, Reduce Motion, Reduce Transparency, contrast, and differentiation settings.
- Prefer semantic text styles such as `.body`, `.headline`, and `.title` over hard-coded font sizes.
- Ensure interactive targets meet the 44x44 minimum.
- Buttons with image labels must include a text label, even if the text is visually hidden.
- Prefer `Button` or `Menu` over gesture-only interactions.
- If `onTapGesture()` is required, add the appropriate accessibility traits.
- Mark decorative images as decorative or hide them from accessibility; add explicit labels for meaningful images.
- If color carries meaning, also differentiate with shape, iconography, text, or stroke so the UI works with `differentiateWithoutColor`.
- Check VoiceOver reading order for stacked overlays, floating controls, and custom rows.
- Prefer `Label` over manual icon+text stacks when it expresses the UI clearly.
- Ensure placeholders, empty states, and search results use accessible system components where appropriate, such as `ContentUnavailableView`.
