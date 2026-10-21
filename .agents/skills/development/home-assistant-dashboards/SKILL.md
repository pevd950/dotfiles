---
name: home-assistant-dashboards
description: Design, audit, or refine Home Assistant dashboards and device pages using Pablo's native-first, compact, progressive-disclosure preferences. Use for Lovelace cards, badges, navigation, responsive Sections/sidebar layouts, issue summaries, and activity/editor UX; not unrelated device or automation changes.
---

# Home Assistant Dashboards

Build a useful household interface, not an entity inventory or engineering control
console. Preserve the user's information and working controls while making the
first screen easier to scan. Current explicit requests override these defaults.

## Start With the Existing Surface

- Read project guidance and the fresh dashboard configuration, relevant entity
  identities, and owning builders. Distinguish managed/generated dashboards from
  editable Lovelace views; use supported customization for each.
- Inventory the readings, actions, confirmations, navigation, history, and saved
  disclosure state that must survive. An older generator can overwrite a newer
  layout: identify the complete publication order before changing it.
- For research or preview-only requests, do not publish. A skill is not authority
  to change devices, entity metadata, integrations, credentials, or household state.

## Component Order

1. Use installed native features first: Sections, sidebar, headings, entity
   badges, Tiles and their features, visibility conditions, shortcuts, history,
   and more-info dialogs. Check the installed frontend before assuming a feature
   or visual editor option exists.
2. Use existing Mushroom cards or template badges for a demonstrated gap, such
   as combining independent readings or threshold colors in one compact item.
3. Reuse an existing specialized component, including a useful Bubble control
   or disclosure wrapper, when native/Mushroom does not cover the workflow.
4. New custom components, CSS placement, DOM patches, or frontend forks are last
   resorts. Explain the gap and ongoing cost before adding a dependency; do not
   strip native borders or recreate platform layout with CSS.

Native-first does not mean forcing a bare Markdown list onto an interactive page.

## Visual and Interaction Defaults

- Keep overviews compact and balanced: actual device/fixture items, short names,
  useful secondary state, and deliberate grid sizes, not tall square status tiles.
  Group small metadata into badges or heading badges rather than a card per fact.
- Default header badges to left alignment. Reuse consistent MDI iconography and
  native state conventions. Color should convey state or severity, not decoration;
  include a value, label, or familiar symbol so color is not the only information.
- Organize spatial content by floor, then room; keep related outdoor areas together.
  Preserve deliberate room/device order instead of sorting everything alphabetically.
- Give each page a coherent priority order. Use native sidebars for complementary
  context; confirm useful stacking on narrow screens. A sidebar is a tool, not a
  mandatory shape for every page. Keep critical small-screen context in top badges.
- Make card body, icon, and hold actions predictable. Native control tiles normally
  open more-info on the body and toggle on the icon only where safe and expected.
  A navigation tile can instead open its clearly identified detail page. A status
  tile for a litter box must never secretly become its power switch.
- Put deliberately consequential commands in clearly named actions with an
  appropriate confirmation, including snacks, cleaning and maintenance routines.
  Do not add confirmation to every harmless navigation or ordinary native toggle.
- Summary counts should open the corresponding actionable/filtered items, not an
  incidental count-history graph. Distinguish different destinations by purpose;
  avoid duplicate shortcuts, repeated device sections, and unexplained icon taps.
- A device page should feel like a device: identity/status, daily actions and a
  useful schedule/camera/history preview first; occasional settings, care,
  maintenance, connectivity and diagnostics behind disclosure or detail navigation.
- Keep explicitly requested charts visible. Progressive disclosure is not license
  to hide useful history or remove details. Media/map/camera previews must be
  associated with their device; verify orientation and actual playback separately.
- Exclude agent commentary, verification notes, implementation jargon and filler
  descriptions from the app. Explain engineering choices in chat/docs instead.

## Truthful Data and Activity

- Deduplicate physical devices and logical fixtures, not just entity IDs. Prefer
  intended fixture/group controls over separately listing their member bulbs.
  Reuse verified canonical room averages/composite occupancy for display without
  changing HVAC, lighting, occupancy or group-control behavior as a design task.
- A count and its issue list must share a definition. Show a device once with its
  most actionable issue, retaining other details in its drilldown. An offline
  device should not reappear as a second missing-battery problem.
- Never render unavailable/stale/unsupported data as a healthy zero or green.
  Distinguish stale from merely unchanged. Expose the actual issue and its source.
- Use meaningful activity events, not noisy running/idle plumbing. Explain the
  time window, units, identity and completeness; do not invent missing earlier
  events or infer visits from cleaning cycles. Label inferred identity as inferred.
- Contextualize quantities: pair free storage with the same filesystem's used
  percentage; verify units and source pairing. Set domain-appropriate severity
  thresholds, not one universal percentage rule for batteries, water and disks.
- Hide empty alert sections and zero warning badges when they add no action.
  Exception: keep an actionable light toggle/restore badge visible at zero so the
  user can reverse the action. This is not a reason to add undo behavior elsewhere.

Read [approved patterns and exceptions](references/patterns.md) for page-specific
recipes, form/history behavior, and the dated feedback behind these defaults.

## Performance and Acceptance

- Prefer a presentation-only change. Do not add polling, helpers, timers, camera
  preloading, recorder load, or dashboard-writing automations just to arrange UI.
- Keep templates dependency-bounded to named entities. Avoid recursive fixture
  discovery, whole-domain/all-state scans and unnecessary `now()` subscriptions
  in frequent updates. Preserve working curated counters; visual success does not
  establish acceptable control-path performance.
- Before authorized publication: make a scoped private backup, check concurrent
  edits, use supported dashboard APIs rather than writing `.storage`, and verify
  exact readback after persistence. Do not regenerate unrelated backend config.
- Validate real phone, tablet portrait/landscape and desktop layouts, borders,
  text wrapping, icon/badge clipping, empty/unknown states, links and disclosure.
  Use available browser tooling; report unavailable tooling and untested physical
  touches honestly. Screenshots of overlays or mockups are not installed acceptance.
- Test editing workflows at the real API boundary, not just form rendering. Check
  success/error completion and readback; live CRUD tests require authorization and
  restoration of the original plan. Never dispense, clean, power-cycle, unlock,
  notify or alter vehicle settings merely to smoke-test a dashboard.
- Separate source changes, publication, restart/reload, installed rendering and
  natural device updates. Preserve unrelated work; keep additive requests and
  validation gaps in the existing progress log rather than forgetting earlier work.
- Retire accepted comparison/placeholder views only when requested and backed up.
  Update owning builders or layout passes so regeneration cannot resurrect them.

## Starters

Use [overview.yaml](assets/overview.yaml) or
[device-detail.yaml](assets/device-detail.yaml) as composition examples, not fixed
house-wide layouts. They contain example entities/routes, no new dependencies,
and must be mapped to verified sources. Merge intended views into fresh config;
never overwrite an existing dashboard with a starter. No deployment is implied.
