# Credentials, branding, and runtime acceptance

## 1Password custody and references

Prefer the established project 1Password Environment or vault item. Use the 1Password Environments skill when installed for supported authentication, variable discovery, and mounts. Inspect current tool schemas rather than copying calls from an older session. An item UUID, secret reference, or consent page proves a setup step; verify that the intended runtime can use the intended credential with a bounded authenticated call.

Keep a small private inventory:

| Responsibility | Record privately |
| --- | --- |
| Provider authorization | Registration, API/OAuth endpoints, redirect, scopes, credential reference, token policy |
| Transport | Tunnel/Site identity, workspace association, runtime key reference, permissions, expiry |
| Account package | App/plugin identity, connection reference, version, asset references |
| Runtime | Owning runtime/config references, active source SHA or immutable version, state format |
| Recovery | Backup reference, compatible release, migration/reconnect limits, renewal action |

A vault reference has the symbolic shape `op://<vault>/<item>/<field>`; replace placeholders only in ignored private configuration. Environment mounts are a separate mechanism and should use the supported 1Password tooling. Never put real reference paths, identifiers, secret values, or connection URLs in shared examples. Inject secrets at runtime through the supported mechanism rather than expanding them into shell arguments, tool inputs, or build output. Exclude sensitive files from source control and package archives.

Verify mount metadata or credential presence privately; do not read a mounted environment just to prove it exists. If interactive unlock/consent is required, identify that boundary and preserve prepared setup. When credential reuse is authorized, establish a match with the intended provider/account without logging values; a working CLI credential is not automatically the connector's credential.

For variable updates, inspect current replacement/append semantics, preserve unrelated names, and avoid duplicate canonical fields. Read back names/non-secret metadata to verify the save. Keep active release metadata separate from historical installed/pinned values.

For providers with rotating single-use refresh tokens, dedicate and coordinate the grant. The active runtime token store becomes authoritative after rotation; the initial secret-manager snapshot is historical. Preserve durable refresh intent before a possibly consuming call. Unknown outcomes need scoped reconnect/recovery, not restoration of the bootstrap token or a blind second refresh.

## Package and visible branding

Inspect the current [plugin format](https://developers.openai.com/plugins/build/plugins) and [icon requirements](https://developers.openai.com/plugins/deploy/submission#icons-and-screenshots). Include logo and composer artwork in the first intended package, using official or appropriately licensed assets. Follow current format/dimension/size requirements and plugin-root-relative paths; inspect the final archive to ensure every referenced asset is present and private configuration is absent.

Use square artwork with padding that survives circular cropping. Check small-size legibility and applicable light/dark variants. A branding update should retain existing connection references and capability scope.

Verify three things separately: archive asset references, metadata accepted for the intended package version, and visible artwork in the relevant picker/listing/composer. Inspect saved package/version metadata and a fresh client session before attributing a fallback to caching. A saved logo does not establish a visible fix; keep any fallback unresolved until observed or explicitly accepted by the owner. Runtime restart or access changes are not implied by an artwork update.

## Installed source and compatible upgrades

Use the owning project's installer and release/runbook within the user's scope. Record immutable source/package identity, dependency/runtime requirements, and configuration. Staging should preserve the active inputs; verify the actual running service/config/version after authorized activation. Build checks, source merge, and deployment are separate evidence.

For an upgrade that changes persisted write or OAuth state, determine compatibility before activation. Use the store's supported consistent backup procedure; for an offline cutover, stop all affected consumers, including read-only clients that can refresh tokens. Rehearse migration on the backup when warranted, preserve original evidence, and inspect ambiguous/quarantined records. Observed desired state alone cannot establish what happened to an uncertain request.

Recover with compatible source and authoritative current state. An old binary may remain incompatible even in read-only mode after a format fence. Never restore consumed tokens or delete dispatch evidence to make rollback work. Follow the project's activation recovery procedure and establish the candidate's state before retrying a failed installer.

## End-to-end acceptance and maintenance

Check active version/configuration, readiness, controlled credential denial, and fresh authenticated execution. Use restart/recovery probes only where required for the release and authorized. Verify changed tool schemas in fresh sessions; retain separate observations for each requested client.

For supported writes, test the exact approved effect with before/after readback and agreed cleanup. Check returned IDs and values rather than trusting an accepted HTTP status. Preserve result lookup for lost responses; prior outcomes can validate migration preservation without claiming a new live write. Record any missing write/device acceptance explicitly.

Classify rate failures by layer: transport, connector budget, or upstream response. Honor provider reset/Retry-After guidance within a bounded diagnostic budget. Account for failures that consume quota, shared callers, and budget persistence across restarts. Report cache source/age/completeness and whether a read triggers upstream refresh. Do not reset counters or restart a service to evade limits; reconcile uncertain writes before any new attempt.

Maintain private active-release, expiry/renewal, state, recovery, and client-acceptance metadata. Keep operational transcripts and personal account data outside the reusable skill. Use existing maintenance arrangements; this guidance does not create a schedule or require a particular PR/review/merge workflow.
