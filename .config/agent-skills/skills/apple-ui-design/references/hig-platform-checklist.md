# HIG Platform Checklist

Use this checklist to adapt one design direction across Apple platforms without losing platform-native behavior.

## Universal HIG checks

- Keep content and primary actions immediately understandable.
- Keep visual hierarchy clear at first glance.
- Use native control metaphors unless product value requires deviation.
- Preserve continuity across light/dark appearance.
- Preserve readability under Dynamic Type and high contrast modes.
- Preserve coherent motion and honor accessibility motion settings.

## iOS

- Prefer bottom tab/navigation patterns that match app information architecture.
- Keep primary actions reachable with one-handed ergonomics.
- Validate behavior in portrait and landscape.
- Avoid dense desktop-style control clusters.

## iPadOS

- Support resizable windows and split-view multitasking.
- Use sidebars and multi-column layouts where information density benefits.
- Support keyboard shortcuts and pointer affordances where meaningful.
- Avoid phone-only layout assumptions.

## macOS (SwiftUI app or Catalyst)

- Respect menu bar, toolbar, sidebar, and inspector idioms.
- Support keyboard-first workflows and precise pointer interactions.
- Use larger information density only when scanability remains high.
- Avoid oversized touch-first spacing on desktop-focused surfaces.

## visionOS

- Favor comfort-first spatial layout and clear depth ordering.
- Avoid cluttered volumetric composition.
- Keep text legible and controls spatially stable.
- Use materials and motion to reinforce hierarchy, not spectacle.

## watchOS

- Keep tasks short, glanceable, and interruption-friendly.
- Favor concise copy and large, scannable controls.
- Minimize multi-step flows and heavy text input.

## tvOS

- Design for focus engine behavior first.
- Keep focused state highly visible and predictable.
- Optimize readability at distance.
- Avoid dense data-entry patterns.

## Final sign-off checks

- Verify navigation model consistency per platform.
- Verify accessibility labels, traits, and traversal order.
- Verify contrast and material readability on real backgrounds.
- Verify motion quality at normal and reduced motion settings.
- Verify no layout breakage at extreme text sizes and window sizes.
