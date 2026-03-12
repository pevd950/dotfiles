# Modern API review

Use this pass to replace outdated SwiftUI and Foundation usage with current APIs.

- Prefer `foregroundStyle()` over `foregroundColor()`.
- Prefer `clipShape(.rect(cornerRadius:))` over `cornerRadius()`.
- Prefer the modern `Tab` API over `tabItem()`.
- Do not use deprecated toolbar placements such as `.navigationBarLeading` and `.navigationBarTrailing`; use `.topBarLeading` and `.topBarTrailing`.
- Avoid the one-parameter `onChange()` form; use the current variants that match the platform SDK.
- Prefer `overlay(alignment:content:)` or the trailing-closure form over deprecated overlay overloads.
- Prefer `sensoryFeedback()` over older UIKit haptic generators in SwiftUI code.
- Prefer `@Entry` for custom environment-style keys when the project uses current Swift macros.
- Use `#Preview` instead of `PreviewProvider`.
- Prefer `ImageRenderer` over `UIGraphicsImageRenderer` when rendering SwiftUI views to images.
- Prefer generated asset symbols such as `Image(.avatar)` when the project is configured for them.
- Prefer `.scrollIndicators(.hidden)` over older `showsIndicators: false` initializers.
- Use text interpolation instead of concatenating `Text` with `+`.
- Prefer `Date.now` over `Date()`.
- Prefer modern Foundation APIs such as `URL.documentsDirectory`, `appending(path:)`, and `FormatStyle` over older formatter-heavy or C-style patterns.
- Prefer `Task.sleep(for:)` over `Task.sleep(nanoseconds:)`.
- Avoid `DispatchQueue.main.async` and other GCD calls when modern Swift concurrency is appropriate.
- Treat `GeometryReader` as a last resort; first consider `containerRelativeFrame()`, `visualEffect()`, or a custom `Layout`.
- Use SwiftUI's native `WebView` for iOS 26+ when embedded web content is needed, unless the project has a specific reason not to.
