# Patterns and Exceptions

Apply the relevant recipes, not a compulsory house-wide layout or frozen frontend
capability matrix. Current requests and verified installed behavior take precedence.

## Current Official Documentation

Use only the relevant pages; follow their current schema links rather than copying
a manual into this skill. The entrypoint requires fresh lookup on every task.

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

## Page Priorities

| Page | Main focus | Complementary content |
| --- | --- | --- |
| Needs Attention | Actionable issues and diagnostic links | Presence by floor; expandable air/windows |
| Admin Control Panel | Modes and common door-lock/presence overrides | Infrequent critical-power/admin controls |
| Devices | Comparable device items and intentional quick actions | Activity after devices on phones or in a wide-screen sidebar |
| Hosts overview | Networking/Hubs and one consolidated Hosts list | Combined connection/CPU/memory/free-space metrics, not duplicate navigation |
| Host detail | Performance, storage/I/O, separate network interfaces | Health/reporting and expandable diagnostics |
| Plants | Water/sensor issues; floor/room inventory | Irrigation when space permits |
| Car | State badges; charging/climate and accessible charge limit | Keep both battery/tire charts visible; disclose secondary settings |

Pets order: feeders, fountains, litter boxes, then separate feeder and litter logs.
Preserve existing plant order until the user's physical room order is supplied.
Prefer one rendered instance of expensive content. If complementary native visibility
conditions place it differently on wide/narrow screens, prove exactly one is visible
and keep both configurations aligned. Preserve existing disclosure keys.

## Display Exceptions

- Presence: consistent motion/presence icon; clear gray, detected amber. Missing
  sources are not clear rooms. Static temperature icons prefer red, not blue;
  retain an existing meaningful temperature-dependent color instead of overriding it.
- Host visual thresholds: CPU amber at 75%, red at 90%; memory/filesystem usage
  amber at 80%, red at 90%. These are display rules, not alert automations. Reject
  invalid ranges; gray disconnected/unknown data. A sleeping laptop's stored report
  is not live; do not pair free capacity with another mount or invent its total.
- A display change does not authorize entity/area/registry edits, HVAC participation,
  occupancy/group-control changes or metadata normalization. Preserve intentional
  native switch behavior on administrative control surfaces.
- Snack controls belong on overview and feeder detail, with portion-specific
  confirmation and duplicate-feed protection. Verify model minimums/units; portions
  do not equal a universal gram amount. New devices use the same UI contract only
  after identity, capabilities and units are verified.
- Camera preloading and recording require a separate resource/privacy decision;
  a snapshot does not prove stream playback, recording or persistence.

## Pet Activity and Editors

- Distinguish usage, cleaning, scheduled/manual feeding, errors and recovery.
  Daily counters mean the local calendar day and disclose event definition, coverage
  and history limits. Cleaning cycles are not visits; polling transitions are not
  meals; food quantity is not a use count. Inferred pet identity stays inferred.
- Show current meals as readable day/time/device-specific amount rows, with focused
  editing in a consistent per-feeder UI. No synchronized multi-feeder writes by default.
  Keep one-off meals/exceptions separate from routine schedules.
- Full-plan replacement preserves other days and meal metadata. Review/save/cancel/
  error states must complete; successful local writes are not external conflicts.
  Verify CRUD, concurrency and restoration only when authorized. Check LAN/mobile
  browser capabilities rather than assuming secure-context Web Crypto is available.

## Capability Questions to Recheck

Before choosing an adapter, check current official docs and installed behavior for:

- Entity Filter's configured rows versus rendering arbitrary issue arrays as cards.
- Tile state/attributes versus joining independent CPU, memory and disk entities.
- Managed-dashboard customization versus editable Shortcut descriptions/actions.
- Native disclosure or detail subviews before an existing frontend-only wrapper.

A demonstrated gap can justify existing Mushroom templates or a specialized renderer,
not new backend helpers solely for styling, vendor patches or periodic label rewrites.
