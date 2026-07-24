---
name: apple-ui-design
description: Create distinctive, production-grade interfaces for current Apple platforms using SwiftUI and UIKit with Liquid Glass and Apple Human Interface Guidelines. Use when asked to design, style, or refactor UI for iOS, iPadOS, macOS, watchOS, tvOS, or visionOS, or when reviewing Apple-platform UI quality and HIG alignment.
---

# Apple UI Design

Build memorable Apple-platform interfaces with one clear visual intent, platform-native behavior, and runnable code — SwiftUI first, UIKit when the feature or codebase requires it.

## Visual direction

Capture the one memorable design idea for the surface, then commit to a single direction and execute it consistently: editorial precision, playful tactile, quiet luxury, technical instrument, organic and soft, or high-contrast utilitarian. Intentional restraint beats random novelty; hierarchy and interaction stay legible first, expressive second.

## HIG as hard constraints

- Clarity of content and actions; deference — chrome supports content, never the reverse; depth through motion, layering, and material with purpose.
- Platform-native navigation idioms and control metaphors.
- Dynamic Type, contrast, and motion accessibility settings honored.
- Apple typography, semantic text styles, and semantic color roles by default; depth systems that stay legible in light and dark modes.
- Tactile interaction feedback: press states, haptics where appropriate, focus feedback.

Load `references/hig-platform-checklist.md` for detailed platform adaptation and QA checks.

## Liquid Glass

Apply intentionally, not decoratively. For SwiftUI implementation and review rules, use the `swiftui-liquid-glass` skill. For UIKit: use glass APIs (`UIGlassEffect`, `UIGlassContainerEffect`) through `UIVisualEffectView` patterns, verify exact signatures against the installed SDK docs before coding, group related glass regions, avoid stacking excessive translucent layers, and provide fallback materials on unsupported versions. `references/liquid-glass-notes.md` has framework-specific notes.

## Avoid

Generic template-like UI; decorative motion that obscures intent; glass/material overuse that harms readability; custom controls that break platform expectations without product justification.

## Quality gates — all must pass

- Dynamic Type remains usable at larger sizes; contrast holds across appearance modes and materials.
- VoiceOver labels, traits, and reading order are correct; hit targets are comfortable.
- Reduced Motion and Reduced Transparency degrade gracefully.
- Layout is robust across iPhone portrait/landscape, iPad split view, and desktop-scale contexts.
- Performance stays stable during transitions and scrolling.

## Deliverables

Runnable SwiftUI/UIKit code aligned with local project conventions, stated deployment-target and platform assumptions, fallback behavior for unavailable APIs, and a short verification checklist for the implemented UI.
