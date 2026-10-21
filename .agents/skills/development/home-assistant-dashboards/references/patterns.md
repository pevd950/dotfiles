# Approved Patterns and Exceptions

These are durable preferences extracted from the October 16-21, 2026 dashboard
conversation, screenshots, saved memory and HomeLab notes. They are not a current
entity inventory or permanent specification of Home Assistant capabilities.
Reconcile fresh user requests and live configuration before applying them.

## Evidence to Decisions

| Feedback | Reusable decision |
| --- | --- |
| Oct 16: badges, native room averages, clear source/detail navigation | Use compact native badges, canonical display sources and purpose-specific drilldowns. |
| Oct 16: room/fixture groups, persistent inside/outside light badges | Do not duplicate grouped bulbs; an off/restore affordance must not disappear after use. |
| Oct 16: bridge connection did not need a whole row; maps needed previews and pan/zoom | Compress simple status, show useful previews, and verify actual interaction rather than a static image. |
| Oct 16-17: collapsible sections liked; empty watering/attention cards disliked | Hide empty alerts and disclose secondary content without removing it. |
| Oct 17: count-template redesign harmed light responsiveness | Preserve the measured curated counter rollback; do not copy expensive discovery from an older design note. |
| Oct 20: oversized pet cards, unclear power taps, noisy feed history and awkward forms | Use compact device items, explicit safe actions, normalized activity and an actual user workflow. |
| Oct 21: zero offline count despite offline device; duplicate battery issue | Derive counts and lists consistently and deduplicate by physical device/severity. |
| Oct 21: floors, consistent occupancy icons, left priority/right context on iPad | Use spatial grouping, common semantics, native responsive layout and narrow-screen checks. |
| Oct 21: native-first, border regressions, Markdown comparison rejected | Preserve platform styling; do not substitute bare lists or custom CSS for useful interactive cards. |
| Oct 21: combined Hosts selected; Tails charts and charge-limit control retained | Match layout to the job; compact overview metrics and detailed charts can coexist without duplicate navigation. |
| Oct 21: free GiB needed percentage context; high load should be colored | Pair quantities with their denominator/usage and use validated severity colors. |

## Layout Recipes

Choose a starting structure, not a compulsory template for every page.

| Page | Main focus | Complementary content |
| --- | --- | --- |
| Needs Attention | Real actionable issues, coherent counts, direct device/diagnostic links | Presence by floor; expandable environmental diagnostics |
| Admin Control Panel | Modes and common access/presence overrides | Infrequent critical-power and administrative controls |
| Device family overview | Compact comparable device items and intentional quick actions | Activity after the devices on phones, or in a wide-screen sidebar |
| Device detail | Identity/status, daily controls, schedule/camera/important charts | Settings, care, maintenance, connection and detailed history |
| Hosts overview | Approved Networking/Hubs plus one consolidated Hosts list | Combined connection/CPU/memory/free-space cards; no repeated host directory |
| Host detail | Performance, storage/I/O and separate network interfaces | Health and reporting state; expandable platform/private diagnostics |
| Plants | Water/sensor issues and room inventory, grouped by floor | Irrigation when space permits; room cards show useful counts |
| Car | State badges, accessible charging/climate and charge limit | Both battery/tire charts remain visible; secondary settings disclosed |

The approved Pets order is feeders, fountains, litter boxes, then separate feeder
and litter activity. Do not move a long log ahead of essential device sections.
The user wants eventual physical plant order within each room: preserve existing
order until that order is supplied, rather than inventing it.

Native Sections/sidebar and native visibility conditions own responsive placement.
Do not force a sidebar if a two-column main Sections layout better preserves chart
ordering. Prefer one rendered instance of expensive content. Complementary native
visibility conditions are acceptable when required for different wide/narrow
placement; prove that exactly one copy is visible, and keep configurations aligned.

## State, Icon and Action Semantics

- Presence uses one consistent motion/presence icon: clear gray, detected amber.
  Prefer verified composite room occupancy when there are multiple sources. A
  missing source is not evidence of a clear room.
- Temperature: if the icon is static, the user preferred red rather than blue;
  a deliberate temperature-dependent color is also acceptable. Do not impose a
  static palette over an existing meaningful dynamic one.
- Connection/status metadata can be badges, not full rows. Keep text/state meaning
  available in details and for accessibility. Match authoritative entity icons
  when metadata edits are separately authorized; dashboard styling is not blanket
  permission to rewrite registry metadata.
- Explicitly approved Host display thresholds: CPU amber at 75%, red at 90%;
  memory/filesystem usage amber at 80%, red at 90%. These are visual thresholds,
  not alert automations. Reject invalid ranges and gray disconnected/unknown data.
  Label stored last reports; never pretend a sleeping laptop's saved value is live.
- Pair free capacity and used percentage from the same filesystem, not a different
  mount or invented total. Respect units and attribute-backed snapshots.
- Device status is navigation/more-info, not an implicit power toggle. Preserve
  ordinary native switch behavior on intentional administrative control surfaces.
- Quick snacks are useful on both overview and feeder details, with a portion-specific
  confirmation and duplicate-feed protection. Keep minimum per-model units honest.
  Never assume a portion equals a universal gram amount.
- A camera preview belongs visually to the relevant device. A preview is not proof
  of live stream playback, orientation, recording or persistence. Preloading and
  recording affect resources/privacy and need their own explicit decision.

## Activity and Forms

Activity should answer what happened, when, on which device and, when reliably
available, the quantity or actor. Distinguish usage, cleaning, scheduled/manual
feeds, problems and recovery. Keep useful history accessible in separate logs or
time-range views without filling the overview with every idle/running transition.

Daily counters must specify the local calendar day, actual event definition,
coverage and historical limits. Do not count clean cycles as visits, polling
transitions as meals, or backfill a complete day from a partial observation window.
Inferred pet identity is not confirmed identity. Usage counts and food quantities
are different metrics and cannot substitute for one another.

Schedule editors should show the current plan as readable meal rows with day,
time and device-specific amount, then support focused editing in the same UI.
Keep one-off meals/exceptions separate from routine schedules. The earlier wish
for synchronized multi-feeder writes was superseded: a consistent per-feeder UI
is the durable requirement, not automatic synchronized routines.

Preserve other days/meal metadata on full-plan replacement. Show unambiguous
review/save/cancel/error states; do not leave Saving stuck after success or report
the editor's own successful write as an external conflict. Verify actual persisted
readback, concurrency behavior, create/read/update/delete and restoration when
authorized. Check LAN/mobile browser capability rather than assuming secure-context
Web Crypto exists. These workflow rules do not authorize schedule mutations.

## Native Limits to Verify, Not Hack Around

- Native Entity Filter filters configured entity rows; it does not turn an arbitrary
  `issues` attribute array into newly defined entity cards. Use the owning issue
  renderer or a justified existing adapter; do not invent a native capability.
- A native Tile can show state/attributes of its own entity, not arbitrarily join
  CPU, memory and disk entities. Existing Mushroom templates can fill that gap with
  fixed references. Avoid creating a backend aggregation helper solely for styling.
- Generated Overview supports its own native configuration. Do not assume an
  editable Shortcut card's description or actions are available in a managed
  shortcut. Check current installed behavior; do not patch vendor frontend code or
  periodically rewrite shortcut labels to imitate a missing feature.
- Disclosure does not require helpers or service calls. Reuse existing frontend-only
  disclosure wrappers around native cards; without one, use a native detail subview.
  Preserve original collapse keys when retaining an existing disclosure.

## Review Cases

Use these as behavioral acceptance cases when adapting the skill, not as claims
that a live system has been tested.

| Situation | Expected choice |
| --- | --- |
| Show an offline device plus its missing battery reading | One actionable issue, same count definition, remaining detail in drilldown. |
| Tap a normal light card versus a litter-box status card | Native light body/details and intentional icon toggle; litter status never powers off. |
| All lights turned off using a summary badge | Badge stays available for the established scoped restore action. |
| No plants need water | No empty warning section or yellow zero-warning badge. |
| A new feeder is added | Verify identity/model/capabilities; reuse the same presentation and history contract without copying stale IDs. |
| Native multi-entity metric card is requested | Try native support first; use existing Mushroom for a demonstrated gap, not new helpers/CSS. |
| Only 13 GiB is free | Look at real used percentage for that filesystem before calling it low. |
| User asks only for a design preview | Reversible preview, no publication or household side effects. |
| User changes direction while work is unfinished | Preserve additive tasks; retire superseded requirements explicitly rather than silently forgetting them. |
| Older builder recreates a rejected layout | Fix the owning builder/pass, preserve later edits, and test idempotence. |
