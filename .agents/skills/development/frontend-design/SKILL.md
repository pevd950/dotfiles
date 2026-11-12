---
name: frontend-design
description: Design and build distinctive, production-grade web interfaces. Use for a new page, component, or app with no established design system, or when the user asks for visual design or a restyle. In an existing product, its design system wins.
---

# Frontend Design

Build working interfaces that look designed for their product, audience, and workflow. In a codebase with an established design system, tokens, or component library, follow it and spend the craft on hierarchy, interaction states, and detail; the aesthetic choices below are for new surfaces and explicit design requests.

## Choose a point of view before coding

- **Purpose**: What job does this interface do, and who is using it?
- **Tone**: Commit to a deliberate aesthetic such as austere utility, expressive editorial, playful toy-like, refined luxury, industrial dashboard, organic/natural, retro-futurist, geometric art deco, raw brutalist, or another direction that fits the product.
- **Constraints**: Respect the project's framework, component system, performance budget, responsive behavior, and accessibility needs.
- **Differentiation**: Decide what users will remember: a layout move, a tactile interaction, a typographic voice, an unusual palette, a dense-but-readable workflow, or a focused visual motif.

Bold maximalism and restrained minimalism both work when every visual choice supports the concept and the user's task.

## Aesthetics

- **Typography**: Pick type with character that fits the domain. Reach past the default stacks (Arial, Inter, Roboto, system fonts) unless the design system uses them. Pair an expressive display face with readable body text, and tune weight, measure, and hierarchy.
- **Color and theme**: Use CSS variables or the project's token system. Prefer a coherent palette with decisive dominant colors and sharp accents over evenly distributed color.
- **Motion**: Animate where it improves comprehension or delight, with CSS transitions/keyframes for simple work and the project's motion library when one exists. A few well-orchestrated moments beat scattered decoration.
- **Composition**: Consider asymmetry, overlap, editorial rhythm, dense work surfaces, strong negative space, or controlled visual tension when the product supports it.
- **Backgrounds and detail**: Create atmosphere through texture, pattern, layering, light, borders, and depth that reinforce the chosen aesthetic.

Steer away from the generic AI-coded look: purple-blue gradients on white, interchangeable SaaS cards, predictable centered heroes, decorative blobs. Vary theme, type, density, and composition between projects.

Match implementation effort to the direction: maximalist concepts need layered visuals and richer animation; minimal ones need precise spacing, restraint, and edge-case polish. Build the usable interface first, and let the design show through craft rather than in-app explanations of it.
