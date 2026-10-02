# ChatGPT Sites hosting

Consider Sites for tools over Site-owned data or an external HTTP API when its runtime, storage, and authorization fit. It can remove the need for a dedicated private host. An existing operational connector needs an independently validated port before switching hosting.

Check current availability and audience controls in [Site-hosted plugin documentation](https://help.openai.com/en/articles/20001547-hosting-a-plugin-with-chatgpt-sites). Publishing, plugin installation/connection, and useful execution are separate acceptance surfaces.

## Runtime fit

A Site runs HTTP code, not a local stdio process. Host-bound apps, native binaries, filesystem locks, and local SQLite files require redesign. Identify provider credentials, rotating tokens, durable write state, limits, and per-user access before moving source.

Use the current `sites-mcp`, `sites-building`, and `sites-hosting` skills when installed; otherwise use the platform's supported documentation and tools. Keep their changing schemas and deployment mechanics in those procedures.

- Reuse the intended Site and preserve its identity, audience, and existing capabilities. Add the MCP capability and a stateless HTTP `POST /mcp` supporting initialization, discovery, and calls.
- Enforce authorization with the trusted hosting identity described by Sites. Keep discovery free of private account data. Site/plugin connection OAuth and external provider authorization are separate lifecycles; one owner's provider grant must not become available to every viewer.
- Supply runtime secrets through native environment tooling, with setup/recovery references in 1Password. Exclude values from source archives and hosting manifests.
- Select platform storage for the actual requirements: structured durable state, blobs, and coordination have different needs. Memory or browser storage cannot own rotating tokens or authoritative write claims. Validate transaction/concurrency guarantees rather than assuming local SQLite semantics transfer to cloud storage.
- For schema changes, inspect generated migrations and the actual applied state. A failed upload can follow successful migration; ambiguous deployment must be inspected before retrying.

## Plugin and client acceptance

Build for the supported hosted runtime and use its publication procedure within the authorized scope. Reuse the app/private plugin provisioned by Sites instead of creating another app or substituting local MCP configuration.

For installation/reconnection, obtain current connection metadata from `get_site` with `include_mcp_connection: true`. Use its returned plugin identity with the supported installation UI; preserve existing connection references on updates. A published Site or displayed Connect button is not a successful tool call.

After connection, execute a bounded account read in a fresh intended client. Verify the exposed contract, provider-account boundary, data freshness, and requested writes separately. Capture the active Site version and client acceptance; do not claim a Sites port was tested merely because this route is documented.
