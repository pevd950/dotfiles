---
name: home-assistant-dashboards
description: Design, audit, or refine Home Assistant dashboards and device pages using Pablo's native-first, compact, progressive-disclosure preferences. Use for Lovelace cards, badges, navigation, responsive Sections/sidebar layouts, issue summaries, and activity/editor UX; not unrelated device or automation changes.
---

# Home Assistant Dashboards

Build a household interface, not an entity inventory or engineering console.
Current user requests override these design defaults, not authorization boundaries.

## Before Every Dashboard Task

1. Read fresh configuration, owning builders and stable entity identities. Identify
   managed/generated versus editable views and the installed HA Core, frontend and
   relevant custom-card versions. Preserve useful controls, history, disclosure
   state and publication order; an old builder must not undo newer work.
2. **Consult current relevant official HA documentation and release notes on every
   task**, before declaring a native limitation or writing YAML. Start with the
   [official reference map](references/patterns.md#current-official-documentation).
   Verify relevant layouts, cards, features and schema; compare latest documented
   capabilities with support in the installed versions and their release notes.
   When docs leave a gap, inspect official frontend source matching the installed
   version or validate safely against that version. Do not upgrade HA implicitly.
3. If online docs or installed-version evidence are unavailable, state the precise
   verification gap; do not silently treat memory, these examples or latest docs
   as confirmed installed behavior. Avoid unsupported YAML/capability claims.
   Keep source links, check dates and implementation evidence in PR/chat, not UI.

## Components and Layout

- Prefer supported native layout/cards/features first, then existing Mushroom for
  a demonstrated gap, then existing specialized components. New dependencies,
  CSS placement, DOM patches and frontend forks are last resorts: explain the gap
  and maintenance cost. Preserve native borders; native-first does not mean bare
  Markdown lists replacing interactive cards. Consult Mushroom's official docs
  only when its components are relevant.
- Use compact, balanced device/fixture items with useful secondary state, not tall
  square tiles or a card per metric. Prefer left-aligned badges, consistent MDI
  icons and meaningful state/severity colors with a value or label, not color alone.
- Group by floor, then room; keep related outdoor areas and deliberate device order.
  Put priority content in the main column and complementary context in a native
  sidebar when useful. Check phone stacking and keep critical context in top badges;
  do not force every page into a sidebar.
- Device pages lead with identity/status, daily actions and useful schedule/media/
  history previews. Disclose occasional settings, care, connectivity and diagnostics
  without removing details or hiding explicitly requested charts. Associate previews
  with their device; verify camera orientation/playback separately.
- Summary counts open actionable filtered items, not incidental count-history
  graphs. Avoid repeated device sections, duplicate destinations and unexplained
  icon actions. Keep agent commentary and filler descriptions out of the app.

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
- Hide empty alerts/zero warnings, except the established light toggle/restore
  badge must remain actionable at zero. Do not add undo behavior elsewhere.

Read [patterns and exceptions](references/patterns.md) for page priorities, exact
Host display thresholds, pet history/editor contracts and capability checks.

## Safe Delivery and Acceptance

- Preview/research is not publication authority. Make body/icon/hold actions explicit:
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
composition examples, not fixed house-wide layouts or deployments. Map placeholders
to verified sources/units/routes and installed capabilities; merge intended views
into fresh configuration rather than overwriting a dashboard with an example.
