---
name: apple-ui-design
description: Create distinctive, production-grade interfaces for current Apple platforms using SwiftUI and UIKit with Liquid Glass and Apple Human Interface Guidelines. Use when asked to design, style, or refactor UI for iOS, iPadOS, macOS, watchOS, tvOS, or visionOS, or when reviewing Apple-platform UI quality and HIG alignment.
---

# Apple UI Design

Build memorable Apple-platform interfaces with clear visual intent, platform-native behavior, and production-ready code.

## Workflow

1. Define the product context.
2. Commit to one visual direction.
3. Select the primary UI framework path (SwiftUI first, UIKit when the feature or codebase requires it).
4. Implement with HIG and platform conventions as hard constraints.
5. Apply Liquid Glass intentionally, not decoratively.
6. Validate accessibility, adaptability, and performance before finalizing.

## 1) Define Product Context

- Identify audience, task criticality, and usage environment.
- Identify platform targets and minimum OS versions.
- Identify whether the feature is net-new or constrained by an existing design system.
- Capture the one memorable design idea for this surface.

## 2) Commit to One Visual Direction

Choose one clear direction and execute it consistently:

- Editorial precision
- Playful tactile
- Quiet luxury
- Technical instrument
- Organic and soft
- High-contrast utilitarian

Favor intentional restraint over random novelty. Keep hierarchy and interaction legible first, expressive second.

## 3) Respect Apple HIG Constraints

Treat these as non-negotiable:

- Preserve clarity of content and actions.
- Preserve deference: chrome supports content, not the reverse.
- Preserve depth using motion, layering, and material with purpose.
- Use platform-native navigation idioms and control metaphors.
- Follow dynamic type, contrast, and motion accessibility settings.

Load `references/hig-platform-checklist.md` for detailed platform adaptation and QA checks.

## 4) SwiftUI Implementation Rules

- Prefer SwiftUI for new feature work.
- Use composition-first views with clear state ownership.
- Use modern observation/state patterns already present in the project.
- Keep view code modular; extract repeated motifs to reusable components.
- Apply animation only where it communicates state or hierarchy changes.
- Use environment and size class adaptation for iPhone, iPad, Mac, and visionOS layouts.

Liquid Glass in SwiftUI:

- Use `glassEffect` and `GlassEffectContainer` for grouped glass surfaces.
- Use glass button styles for action emphasis where appropriate.
- Apply glass modifiers after layout and appearance modifiers.
- Use morphing transitions only for meaningful hierarchy transitions.
- Gate API usage with availability checks and provide non-glass fallback materials.

Load `references/liquid-glass-notes.md` for framework-specific usage notes.

## 5) UIKit Implementation Rules

- Follow existing UIKit architecture in mixed or legacy codebases.
- Keep controllers lean; isolate view configuration and state updates.
- Use modern list/navigation APIs where possible.
- Adapt layout with safe areas, trait collections, and split view behavior.
- Ensure pointer, keyboard, and focus behavior on iPadOS, macOS Catalyst, and tvOS contexts as needed.

Liquid Glass in UIKit:

- Use UIKit glass APIs on supported OS versions (for example `UIGlassEffect`, `UIGlassContainerEffect`) through `UIVisualEffectView` patterns.
- Verify exact API signatures against the currently installed SDK docs before coding.
- Group related glass regions and avoid stacking excessive translucent layers.
- Provide fallback material styles on unsupported versions.

## 6) Visual and Interaction Standards

- Use Apple typography and semantic text styles by default.
- Use color roles and semantic colors for dynamic system appearance.
- Build depth with spacing, material, and shadow systems that remain legible in light/dark modes.
- Prioritize tactile interaction feedback (press states, haptics where appropriate, focus feedback).
- Keep motion purposeful and physically coherent.

Avoid:

- Generic template-like UI.
- Decorative motion that obscures intent.
- Overuse of glass/material that harms readability.
- Custom controls that break platform expectations without product justification.

## 7) Accessibility and Quality Gates

Pass all gates before completion:

- Dynamic Type behavior remains usable at larger sizes.
- Contrast is acceptable across appearance modes and materials.
- VoiceOver labels, traits, and reading order are correct.
- Hit targets are comfortable and consistent.
- Reduced Motion and Reduced Transparency settings degrade gracefully.
- Layout is robust across iPhone portrait/landscape, iPad split view, and desktop-scale contexts.
- Performance remains stable during transitions and scrolling.

## 8) Output Contract

When producing deliverables:

- Provide real, runnable SwiftUI/UIKit code, not mockup-only prose.
- State assumptions about deployment targets and platform scope.
- Keep code aligned with local project conventions.
- Include fallback behavior for unavailable APIs.
- Include a short verification checklist for the implemented UI.

## Resources

- Platform adaptation and HIG checks: `references/hig-platform-checklist.md`
- Liquid Glass notes for SwiftUI and UIKit: `references/liquid-glass-notes.md`
