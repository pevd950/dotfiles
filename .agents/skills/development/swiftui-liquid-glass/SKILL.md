---
name: swiftui-liquid-glass
description: Implement, review, or improve SwiftUI features using the iOS 26+ Liquid Glass API. Use when asked to adopt Liquid Glass in new SwiftUI UI, refactor an existing feature to Liquid Glass, or review Liquid Glass usage for correctness, performance, and design alignment.
---

# SwiftUI Liquid Glass

Prefer native Liquid Glass APIs (`glassEffect`, `GlassEffectContainer`, glass button styles) over custom blurs. `references/liquid-glass.md` has the full API guide; prefer Apple docs for current signatures.

## Rules

- Wrap multiple coexisting glass elements in `GlassEffectContainer` and tune spacing.
- Apply `.glassEffect(...)` after layout and appearance modifiers.
- Use `.interactive()` only on elements that respond to touch or pointer.
- Use `.buttonStyle(.glass)` / `.buttonStyle(.glassProminent)` for actions.
- Add morphing transitions with `glassEffectID` + `@Namespace` only when the hierarchy changes with animation.
- Keep shapes, tinting, and spacing consistent across related elements.
- Gate with `#available(iOS 26, *)` and provide a non-glass fallback.

## Patterns

```swift
if #available(iOS 26, *) {
    Text("Hello")
        .padding()
        .glassEffect(.regular.interactive(), in: .rect(cornerRadius: 16))
} else {
    Text("Hello")
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
}
```

```swift
GlassEffectContainer(spacing: 24) {
    HStack(spacing: 24) {
        Image(systemName: "scribble.variable")
            .frame(width: 72, height: 72)
            .font(.system(size: 32))
            .glassEffect()
        Image(systemName: "eraser.fill")
            .frame(width: 72, height: 72)
            .font(.system(size: 32))
            .glassEffect()
    }
}
```
