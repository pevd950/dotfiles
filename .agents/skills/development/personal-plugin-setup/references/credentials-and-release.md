# Credentials, branding and release completion

## 1Password custody

Use the 1Password Environments skill. Authenticate and inspect existing environments before creating one; prefer the established project Environment. List variable names without exposing values. Retrieve the secret through its supported private access mechanism and verify the intended credential before relying on unattended access. Treat an item reference or consent page as a setup step, then verify usable credentials.

Record, as applicable:

| Responsibility | Variables / records |
| --- | --- |
| Provider registration | App name/ID, client ID/secret, API and OAuth base URLs, exact redirect, scopes and token policy |
| Transport | Tunnel/Site identity, intended organization/workspace association, runtime key, approved permissions and expiry |
| Account package | Plugin/app identity, private connection URL, package version, logo/composer assets and verified metadata |
| Runtime | Private owning-host route, root/service/config reference, active source SHA, state format and cutover time |
| Recovery | Offline backup reference, compatible source fallback, migration/reconnect procedure and limits |

Conceal secret values. Keep private identifiers, account URLs, host topology and viewing/library contents out of GitHub and reusable tracked configuration. Do not print a broad environment or route private notes into a public system. Use a masked entry or protected secret transfer, then verify file identity/mode and secret presence without logging the value.

For OAuth, dedicate the grant to this connector. Serialize single-use refresh and retain durable intent before a possibly consuming request. The active runtime token store becomes authoritative after rotation; an initial concealed bootstrap snapshot is historical evidence, never a rollback token. Unknown refresh outcomes require scoped reconnect/recovery, not deletion of the marker or a second refresh. Preserve unrelated grants.

Update the active release variable after verification. Do not assume an `append_variables` tool replaces an existing name: use a supported update path, or a clearly named new canonical field plus explicit deprecation metadata. Avoid duplicate same-name variables. Verify saved metadata without rereading all secrets.

## Branding acceptance

Prepare square logo/composer assets up front; retain the original official/licensed source. Use transparent padding and verify circular cropping, legibility and optional light/dark variants. Inspect the current plugin schema before choosing `interface`/`extensions.com.openai` fields and include every referenced file under the plugin root, preferably `./assets/`.

Record the package version, accepted icon references and a fresh visible client check separately. Preserve the existing app identity and server permissions when updating artwork. If the UI still shows a fallback icon, record it as unresolved even when metadata saved successfully.

References: [Plugin packaging](https://developers.openai.com/plugins/build/plugins), [icon requirements](https://developers.openai.com/plugins/deploy/submission#icons-and-screenshots).

## Merge → deploy → migrate where applicable → verify

1. Verify the authorized merge's exact SHA/main ancestry and reviewed-tree equivalence. Build/package from that commit, not a dirty checkout or mutable branch name.
2. Stage on the owning runtime and run required release checks. Preserve active configuration, credential files, stores and unrelated services. Verify the runtime version floor on the actual host.
3. Determine whether migration is needed and what rollback is compatible. For consequential persisted state, compare the actual legacy shape with the approved contract; do not assume a test fixture proves the production store.
4. Stop every old consumer of the affected stores, including read-only consumers that can refresh OAuth. Verify absence, then make an offline private backup with a byte/digest manifest. Do not copy a live SQLite database, delete a journal, restore consumed tokens or sync the live store to cloud storage.
5. Rehearse on the offline copy when the state change warrants it. Run the authorized migration; preserve originals and archive digests. Inspect quarantine. A retained completed outcome plus documented request-completion evidence can support an operator assessment; observed desired state alone cannot resolve an ambiguous request. Never automatically clear unattributable/global blocks.
6. Activate the staged release using its supported installer. On failure, prove candidate job absence before retrying and preserve evidence. Restore only compatible source; a permanent database/OAuth format fence can intentionally make old read-only binaries incompatible.
7. Read back active service/config/release SHA, health and readiness. Perform a bounded restart and fresh authenticated read through the account plugin. Check changed tool behavior and preserved result lookup; never apply an old ID to demonstrate replay refusal in production.
8. Test missing/invalid credentials without registering another poller or performing provider work. Configuration validation, HTTP denial and successful authenticated execution establish different facts.
9. Update 1Password release metadata, private handoff and GitHub acceptance with sanitized evidence. Keep tested source, installed source, automated tests and owner/client acceptance distinct. If no new live write was performed, state that.
10. Complete usable delivery, or identify the exact remaining external boundary. Record source merge, CI, connection status and installed-client acceptance separately.

## Review discipline

Use `babysit-pr` to collect the full live review record, check repository rules and track the current commit and monitor. Use `gh-pr-address-feedback` for validated fixes. One root owns source changes and the sole monitor. Capacity-only skips require the user's applicable permission and are recorded separately from approval. Verify the reason for a paused review before treating it as a capacity limit.

Reassess the design when substantive findings repeatedly affect one subsystem. Document the guarantees and the limits of the available evidence. Do not claim power-loss certification or exactly-once remote execution from tests that cannot establish them.
