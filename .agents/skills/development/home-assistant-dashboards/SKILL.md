---
name: home-assistant-dashboards
description: Design, audit, or refine Home Assistant dashboards and device pages so they feel like one cohesive app, with color and icons carrying state, purpose-built tiles, and depth one tap away. Use for Lovelace cards, badges, navigation, Sections layouts, issue summaries, and activity/editor UX; not unrelated device or automation changes.
---

# Home Assistant Dashboards

Build a household app for the job at hand, not an entity inventory, an engineering
console, or a column of default cards. Current user requests override these defaults.

## Design direction

The model is the Plants dashboard: photo tiles with one status chip, header counts
that open their own list, rooms in the order the user walks them, one tabbed care
sheet per plant, and a health board. Aim for that level of cohesion on every page.

- **Start from the job.** Name what someone opens the page to see and to do. Lead
  with identity and status at a glance, put everyday actions next, and keep depth
  one tap away in a sheet or a detail page.
- **One visual system per dashboard.** Choose a small palette and give each color
  one meaning everywhere: red needs action now, amber soon, blue for the measured
  quantity, green only for verified healthy, grey for unknown or stale. Any accent
  beyond those gets a stated meaning. Pair color with a value or label.
- **Icons carry meaning.** One MDI icon per concept, reused in headings, chips,
  badges and tiles. Every section heading has an icon.
- **Tiles are objects, not metrics.** One tile per real thing (a plant, a device,
  a room) with its photo or icon, its name, one status chip and the one reading
  that matters. Compact and balanced, with useful secondary state.
- **Header badges are the summary and the navigation.** Counts by state, colored
  and icon-led, left-aligned, hidden at zero, each opening the list it counts.
- **Depth in one place.** One sheet or detail page per object, with tabs when it
  has several jobs (overview, actions or care, history, settings). It opens once at
  full size. Frequent actions come first; rare ones live under Settings. Link the
  object's device page from wherever the object appears.
- **Charts earn their space.** One compact chart that answers the page's question,
  with a larger view on tap. Keep charts the user asked for visible.
- **Stable layout.** Cards keep their size as state changes.
- **Group the way the house is used.** Rooms in the user's own order (a walking or
  care route when given, otherwise floor then room), related outdoor areas together.
  Priority content goes in the main column; complementary context sits at the top
  right on wide screens and after the main content on phones.
- **Running processes stay controllable.** While something multi-stage runs, its
  stop and continue controls stay visible at every stage.

The results to avoid: a card per metric, an entities or Markdown list standing in
for interactive cards, many conditional copies of one card, several squeezed graphs,
tall square tiles, and a page with no color or icon system.

## Components

Choose the component that produces that result, and say what it costs to maintain.

- Native Sections, headings, badges and tiles with features are the frame.
- Installed custom cards such as Mushroom and Bubble Card provide chips, template
  cards and pop-up sheets. Read their official docs for the installed version.
- When one kind of object would need many conditional copies of a native card,
  build or reuse one purpose-built card for it. The Plants tile replaced a dozen
  conditional variants and cut the stored dashboard from 4.8 MB to 577 KB.
- Explain the gap and the maintenance cost before adding a new dependency. CSS
  placement hacks, DOM patches and frontend forks are last resorts.
- Device pages lead with identity and status, daily actions and useful schedule,
  media or history previews. Disclose occasional settings, care, connectivity and
  diagnostics without removing them. Associate previews with their device; verify
  camera orientation and playback separately.
- Summary counts open actionable filtered items, not count-history graphs. Avoid
  repeated device sections, duplicate destinations and unexplained icon actions.
- Keep agent commentary, verification notes and filler descriptions out of the app.

House-specific patterns: when the homelab repository is checked out, read its
`docs/dashboard-design.md` and the doc for the dashboard you are changing. Otherwise
read [patterns and exceptions](references/patterns.md) for page priorities, host
display thresholds, pet history and editor contracts, and capability checks.

## Before changing a dashboard

1. Read fresh configuration, owning builders and stable entity identities. Identify
   managed/generated versus editable views and the installed HA Core, frontend and
   relevant custom-card versions. Preserve useful controls, history, disclosure
   state and publication order; an old builder must not undo newer work.
2. Consult current official HA documentation and release notes when using a card or
   feature the dashboard does not already use, and before declaring a native limitation. Start with the
   [official reference map](references/patterns.md#current-official-documentation).
   Verify relevant layouts, cards, features and schema; compare latest documented
   capabilities with support in the installed versions and their release notes.
   When docs leave a gap, inspect official frontend source matching the installed
   version or validate safely against that version. Do not upgrade HA implicitly.
3. If online docs or installed-version evidence are unavailable, state the precise
   verification gap; do not silently treat memory, these examples or latest docs
   as confirmed installed behavior. Avoid unsupported YAML/capability claims.
   Keep source links, check dates and implementation evidence in PR/chat, not UI.

## Truthful State

- Deduplicate physical devices and fixtures; prefer intended group controls. Reuse
  verified room averages/composite occupancy for display, not control changes.
  Counts and issue lists share a definition: show each device's most actionable issue once,
  with remaining detail in its drilldown, not a second missing-battery warning.
- Unknown, unavailable, stale or unsupported is not healthy zero/green. Distinguish
  stale from unchanged; label stored last reports. Pair free storage with the same
  filesystem's used percentage; verify units, denominators and domain-appropriate thresholds.
- Activity shows meaningful events, not running/idle plumbing. State time window,
  identity, units and completeness; no invented backfill, visits inferred from
  cleaning cycles or confirmed labels for inferred identity.
- Hide empty alerts/zero warnings; the one standing exception is in the patterns reference.

## Safe Delivery and Acceptance

- Make body/icon/hold actions explicit:
  status opens details/navigation, never hidden device power. Confirm consequential
  snacks, cleaning and maintenance; keep ordinary safe toggles/navigation ergonomic.
- Keep templates bounded to named dependencies. Preserve measured curated light
  counters; avoid recursive discovery, all-state/domain scans and unnecessary
  `now()` in frequent updates. Do not add polling, helpers, timers, camera preloading,
  recorder load or dashboard-writing automations merely to arrange UI.
- Before authorized publication: scoped private backup, concurrent-edit check,
  supported APIs rather than direct `.storage` writes, and exact persisted readback.
  Update owning builders/passes and verify idempotence; retire comparison views only
  when requested and backed up. Preserve unrelated work and additive tasks/gaps.
- Check phone, tablet portrait/landscape and desktop: borders, wrapping, clipping,
  links, disclosure, empty/unknown states and responsive order. Report untested
  tooling/physical touches; mockups and successful reloads are not installed acceptance.
- Test authorized editing at the API boundary, including completion/errors,
  concurrency, persisted readback and restoration after live CRUD. Never dispense,
  clean, power-cycle, unlock, notify or change vehicle settings as a smoke test.
  Distinguish source changes, publication, reload/restart, rendering and natural updates.

## Starters

[Overview](assets/overview.yaml) and [device detail](assets/device-detail.yaml) are
native-only structural examples, not the visual target and not fixed house-wide layouts or deployments. Map placeholders
to verified sources/units/routes and installed capabilities; merge intended views
into fresh configuration rather than overwriting a dashboard with an example.
