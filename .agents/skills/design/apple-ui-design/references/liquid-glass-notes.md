# Liquid Glass Notes (SwiftUI + UIKit)

Use Liquid Glass to support hierarchy and interaction cues, not as decoration.

## Scope and availability

- Target current Apple SDKs that include Liquid Glass APIs.
- Gate all Liquid Glass usage with availability checks.
- Provide fallbacks (`Material`, blur, or standard backgrounds) for unsupported OS versions.

## SwiftUI notes

- Prefer `glassEffect` for custom glass surfaces.
- Use `GlassEffectContainer` when multiple glass elements coexist.
- Keep shape language consistent across related glass elements.
- Apply glass after layout and base appearance modifiers.
- Use interactive glass only on controls or directly interactive surfaces.
- Use glass morphing IDs/transitions only when view hierarchy changes meaningfully.

## UIKit notes

- In UIKit codebases, use platform glass APIs (for example `UIGlassEffect`, `UIGlassContainerEffect`) through native effect-view patterns.
- Verify exact initializer and configuration signatures in the installed SDK docs before implementation.
- Centralize effect configuration to keep a consistent glass language across screens.
- Avoid stacking multiple effect views that reduce legibility.

## Do / Do not

Do:

- Use glass to group related controls or elevate key actions.
- Keep foreground text/icons high contrast against dynamic backgrounds.
- Test glass readability on image-heavy and high-saturation content.

Do not:

- Put glass on every surface.
- Combine strong tint, strong blur, and heavy shadow simultaneously.
- Sacrifice readability for visual novelty.

## QA checklist

- Verify readability in light and dark appearance.
- Verify Reduced Transparency behavior.
- Verify smooth scrolling and transition performance.
- Verify no accidental occlusion of essential content.
