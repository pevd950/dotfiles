---
name: parcel-tracking
description: "Pablo's rules for Parcel package tracking through the Parcel connector: when to add a delivery without asking, the API's daily and hourly limits, and what to check before retrying. Use when adding a delivery from a tracking number, checking active or recent deliveries, or building a delivery automation."
---

# Parcel tracking

Reach Parcel through the session's Parcel connector (in Codex its tools sit under `mcp__codex_apps__parcel`): find carriers, list deliveries, preview an add and execute it.

## Adding a delivery

- A request to add a delivery, or an existing scoped authorization, is the permission for that delivery, including any postcode or email it supplies. Run the preview for your own check and execute; ask only when the tracking number, carrier, description, or a required postcode or email is missing or ambiguous.
- Resolve the carrier code first, and check active and recent deliveries for a duplicate.
- Use the carrier code `pholder` only for a placeholder delivery.
- A new delivery may show no data until Parcel's server updates.
- Report what was added, what failed, and any limit that was hit.

## Limits of the Parcel API

- 20 add requests a day, failures included, one delivery per request.
- 20 reads an hour. Results are cached upstream and a read does not refresh the carrier.
- No edit, delete, archive or forced refresh. After a timeout or a lost response, check recent deliveries before retrying, because every attempt counts against the daily limit.
- Reference: [Parcel API](https://parcelapp.net/help/api.html).
