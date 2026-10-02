---
name: personal-plugin-setup
description: Set up or maintain a private MCP account plugin, choosing hosting, configuring credentials, packaging branding, and verifying its tools and optional UI in the intended clients. Use for connector commissioning, plugin upgrades, and runtime acceptance.
---

# Personal plugin setup

Make the requested plugin capabilities work in the intended clients. Follow the user's delivery scope and the owning project's procedures; this skill supplies plugin setup and acceptance checks.

## Establish the capability boundary

Identify the requested reads, writes, clients, UI needs, and private audience. Inspect current provider documentation and existing maintained MCP implementations. Reusable server code and an already hosted service are different options. Check licensing, supported operations, authentication, and persistence before selecting either.

Keep provider capability, configured server tools, and installed client access distinct. If the user wants existing-record edits but the API supports only reads and creation, explain that limitation and the supported alternative. A read-only first implementation does not satisfy requested writes. Setup approval does not authorize a new provider mutation.

## Choose hosting

| Route | Choose when | Acceptance surface |
| --- | --- | --- |
| Existing trusted remote MCP | Supported tools, authentication, and data boundary fit | Inspect actual tools and execute a bounded account read |
| Private host + Secure MCP Tunnel | Local APIs/data or private runtime dependencies matter | Verify the owning runtime and transport, then an account-plugin call |
| ChatGPT Sites MCP | HTTP execution and cloud storage fit the connector | Verify published hosting, plugin connection, and actual tools |
| Local desktop MCP | Local-only access meets the request | Execute through the intended local client |

Choose for the actual dependencies and audience; local success does not establish web/mobile access. Read [host and tunnel setup](references/host-and-tunnel.md) or [Sites setup](references/sites-mcp.md) for the selected route. A local stdio/filesystem server needs an adapted HTTP/storage design for Sites.

## Define the tool contract

- Expose task-shaped tools over documented provider operations. Use stable IDs, validate response identity, and keep arbitrary URLs, shell commands, and provider credentials out of tool arguments.
- Return enough context to use results: parent identity for child records, truthful pagination totals/completeness, and targeted checks instead of full account crawls. Missing counts and incomplete traversal remain unknown; they cannot prove zero or absence.
- Match advertised access, annotations, and guidance to the tools enabled by the active configuration. Exercise initialization, discovery, schemas, and calls through a real MCP client. Implement any declared extension's complete contract, including cache, size, and digest fields where required; otherwise omit that declaration.
- Bound bytes, pages, fan-out, concurrency, timeouts, and pending work. Distinguish local budgets from upstream limits; disclose cached data and freshness rather than describing every successful read as fresh.
- For consequential writes, resolve the exact effect and before/after state, bind approval to that effect, and reject stale previews. Retain result lookup after uncertain dispatch. Use provider idempotency when available; a possibly sent request must not be blindly replayed. Local dispatch protection alone cannot promise exactly-once provider execution.
- Where independent processes share write or token state, use coordination that makes authority and outcomes durable. Keep provider HTTP outside mutation-state transactions. Choose storage for the concurrency/recovery needs rather than requiring a database for every plugin.

## Choose optional UI surfaces

Add UI when inspecting, comparing, selecting, editing, or navigating data materially improves the requested workflow. Choose a focused inline view, a sidebar app, or a conversation panel for the task; consider file handlers, composer content mentions, or rich forms only when relevant. Keep MCP tools usable without UI.

For UI work, read [UI extensions and acceptance](references/ui-extensions.md) and the current [OpenAI Plugin Extensions documentation](https://developers.openai.com/plugins/build/extensions). Distinguish plugin-directory discovery and branding from registered app entrypoints. Record supported clients and selected surfaces; a sidebar entry does not prove a working interface.

## Configure and package

Read [credentials, branding, and runtime acceptance](references/credentials-and-release.md) for 1Password custody and reference patterns, rotating tokens, package assets, and state compatibility. Keep credentials and private deployment metadata outside portable source.

Package the intended connection, capabilities, version, logo, and composer artwork using the current schema. Reuse the existing app/plugin identity on updates. Verify package contents, accepted metadata, and visible artwork separately.

## Prove acceptance and maintain it

Record the exact installed source/package/configuration, not only a tested checkout or source merge. Use the selected hosting procedure and project installer for authorized activation; verify state compatibility when an upgrade requires migration.

Start with a small authenticated account read, then a bounded operation that proves the requested data shape. Test requested clients in fresh sessions. For writes, use an authorized reversible scenario with before/after readback and agreed cleanup; keep synthetic tests, prior accepted writes, and new live write acceptance distinct. If a write or client check is unavailable, state the gap rather than claiming full management.

For selected UI surfaces, verify discovery, opening, rendered data, interaction, and conversation context through the installed client using the [UI acceptance checks](references/ui-extensions.md#prove-the-installed-interface). Keep source validation, accepted registration, and observed interface behavior separate.

For failures, use [connector-readiness-triage](../../ops/connector-readiness-triage/SKILL.md) when available. Trace the failing layer before changing anything: client exposure/authentication, transport, runtime, local quota, or provider response. Inspect bounded private logs and status; honor retry/reset guidance and stop at the diagnostic budget. Do not consume scarce reads in retry loops or replay uncertain writes. Loopback health alone cannot exclude host pressure or provider failure.

Keep a private operational record of active version/source, configuration and secret references, expiry/renewal, persistence ownership, compatible recovery, tested clients/scenarios, and remaining gaps. Refresh it after verified upgrades. Use the owner's chosen knowledge/task systems and existing operational procedures; ongoing monitoring is optional and requires its own request.

Platform references checked 2026-10-02. Refresh current schemas, limits, and hosting instructions when applying this skill.
