# Documentation and Capability Checks

General references for any Home Assistant dashboard. House-specific patterns (page
priorities, display exceptions, thresholds, pet activity and editor rules) live in
the homelab repository's `docs/dashboard-design.md`.

## Current Official Documentation

Use only the relevant pages; follow their current schema links rather than copying
a manual into this skill.

| Decision | Official references |
| --- | --- |
| Dashboard ownership/customization and version changes | [Dashboards](https://www.home-assistant.io/dashboards/), [managed/custom dashboards](https://www.home-assistant.io/dashboards/dashboards/), [latest release notes](https://www.home-assistant.io/latest-release-notes/) |
| Responsive layout | [Views](https://www.home-assistant.io/dashboards/views/), [Sections](https://www.home-assistant.io/dashboards/sections/), [Sidebar view](https://www.home-assistant.io/dashboards/sidebar/) |
| Compact state and controls | [Tiles](https://www.home-assistant.io/dashboards/tile/), [features](https://www.home-assistant.io/dashboards/features/), [badges](https://www.home-assistant.io/dashboards/badges/) |
| Interaction and conditional display | [Actions/confirmations](https://www.home-assistant.io/dashboards/actions/), [card visibility](https://www.home-assistant.io/dashboards/cards/#showing-or-hiding-a-card-or-badge-conditionally) |
| Navigation | [Shortcut](https://www.home-assistant.io/dashboards/shortcut/) |

When Mushroom is needed, use its [official project docs](https://github.com/piitaya/lovelace-mushroom)
for the installed card version. Official source at the installed tag can resolve
documentation gaps; a development-branch schema is not proof of installed support.

## Capability Questions to Recheck

Before choosing an adapter, check current official docs and installed behavior for:

- Entity Filter's configured rows versus rendering arbitrary issue arrays as cards.
- Tile state/attributes versus joining independent CPU, memory and disk entities.
- Managed-dashboard customization versus editable Shortcut descriptions/actions.
- Native disclosure or detail subviews before an existing frontend-only wrapper.

A demonstrated gap can justify existing Mushroom templates or a specialized renderer,
not new backend helpers solely for styling, vendor patches or periodic label rewrites.
