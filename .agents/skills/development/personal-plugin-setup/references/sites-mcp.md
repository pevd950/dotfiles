# ChatGPT Sites hosting alternative

Confirmed 2026-10-01: OpenAI documents hosting an MCP server in a new or existing Site and creating an associated plugin when its owner publishes. Install and connection remain separate steps. Feature rollout and workspace permissions can affect availability; recipients need access to both the plugin and Site. Personal accounts currently cannot share their Site-hosted plugin directly through invitations or a share link. [Official setup](https://help.openai.com/en/articles/20001547-hosting-a-plugin-with-chatgpt-sites)

## Fit test

Consider Sites for a cloud-native adapter to an external HTTP API or tools over Site-owned data. It can remove the need for a dedicated Mac and tunnel daemon. Move an operational connector when its requirements justify that change.

Check what the service needs: provider credentials, OAuth rotation, atomic state, rate limits, filesystem access, native binaries and user authorization. A server depending on local macOS apps, stdio processes, kernel-held directories or `node:sqlite` files needs a different runtime/storage design. Remote HTTP access to the provider does not by itself solve these dependencies.

## Implement using the installed Sites skills

Read the currently installed `sites-mcp`, `sites-building` and `sites-hosting` procedures when executing, rather than embedding their tool schemas here.

1. Inspect/reuse the intended Site and its source. Preserve its opaque project ID and audience; new Sites start private.
2. Preserve existing capabilities and add `"mcp"` in `.openai/hosting.json`. Expose a stateless HTTP `POST /mcp` with initialization, discovery and calls. Sites does not run a local stdio server.
3. Use the hosting-boundary identity headers documented by Sites. Keep discovery free of private data and enforce user-specific authorization on data calls, returning 401/403 when appropriate. Sites owns OAuth for the Site/plugin connection. Provider API authorization is a separate lifecycle; do not bypass it or share one owner's grant with all Site viewers.
4. Store runtime secrets through the native Sites environment tools, with their authoritative setup/recovery metadata in 1Password. Keep values outside source archives and hosting manifests.
5. Use platform persistence only where required: D1 for structured durable state, R2 for blobs. Memory/browser storage cannot carry authoritative claims or rotating tokens. Do not assume local SQLite locking/transaction semantics transfer unchanged to D1; review the supported coordination guarantees and recovery contract.
6. Generate and inspect schema migrations before build/publish. Sites may apply migrations before Worker upload, so a failed deployment can leave applied schema changes. Preserve applied migration history and inspect ambiguous state before retrying.
7. Build Workers-compatible output and publish with the native Site workflow. Reuse the provisioned app/private plugin; do not create an extra plugin or configure local MCP as a substitute.
8. Read `get_site(include_mcp_connection: true)`, use its actual returned plugin ID with `plugin_management.suggest_plugins`, and let the user install/connect. Then verify an actual read-only tool call. Publishing success alone is hosting proof.

These steps were checked against the installed Sites MCP, hosting and storage instructions. Refresh them when using this procedure. A new Site was not created, published or tested as part of this research.

## Recommendation for the next connector

Compare a minimal Sites HTTP adapter with a private-host adapter before writing source. Favor Sites when its runtime, durable storage and provider authorization fit without a custom recovery system. Preserve an existing deployment until a separately designed and validated port is ready.
