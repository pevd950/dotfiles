# Private host and Secure MCP Tunnel

Use this route when the server needs the selected host's local APIs, data or established service environment. Choose the host based on those dependencies.

## Resolve ownership first

Use `cross-host-context`: resolve the current host through the private routing directory, then read the relevant destination subject. Verify tools, credentials and paths on the owning host. Use its restricted `-codex` identity for unattended code work and its user-owned identity for the owner's files, apps, Keychain or administration. Never silently switch identities after a failure.

Check available disk, load and service health. Verify actual tool calls as well as loopback health under host pressure. Keep diagnostics bounded and preserve unrelated workloads.

## Keep four boundaries separate

1. **Provider:** dedicated app/key/OAuth grant for the connector, independent of existing CLIs and apps.
2. **Server:** bounded tools; credentials supplied through a private store, not tool arguments or caller-selected URLs.
3. **Tunnel supervisor:** a dedicated OpenAI runtime key. Pass it only to `tunnel-client`, never to the provider MCP process. Refuse leaked supervisor secrets before third-party module loading where the project implements that contract.
4. **Account plugin:** correct Platform organization and ChatGPT workspace association, intended private audience and supported client access.

The tunnel is outbound HTTPS and supports stdio or private HTTP targets. It does not require opening a public inbound port. Organization tunnel permissions and ChatGPT workspace/plugin permissions are different. Creation/edit needs Tunnels Read + Manage; runtime use needs Read + Use. Do not expand permissions merely because the tunnel is absent from a picker.

## Set up transport

- Discover the current official `tunnel-client` release and inspect its live help. Use the supported named stdio sample or HTTP configuration. Check generated YAML against the supported format before use.
- Create/reuse the exact authorized tunnel and associate the intended workspace. Save identifiers, key scope and approved expiry in the existing 1Password Environment.
- Supply the key through a masked prompt, private file or supported secret injection. Ensure a human-facing prompt is actually open before directing the user to it. Never put the key in chat, shell arguments, screenshots or tracked YAML.
- Start a dedicated supervised service with an explicit release SHA, separate credential/change stores, private logs and loopback health listener. Use a minimal child environment. Preserve the safe permissions of shared LaunchAgents directories.
- Keep one active poller for the tunnel. A second validation client must not become a competing daemon.
- Check `/healthz` and `/readyz`, then an actual account-plugin call. `doctor` checks configuration and does not prove authentication of a syntactically valid key. Validate denial with a controlled missing-key startup/configuration check and a safe invalid-key HTTP request; do not dispatch provider work during the probe.
- Register/reuse the private tunnel-backed app, install its account plugin and connect it. Discovery, connection, tool availability and successful execution are separate observations.

## Packaging and verification

Use the pinned installer/runbook in the owning repository. Runtime roots and identifiers come from private routing/1Password, never hardcoded into the skill. Stage immutable candidates with independent launchers/config/profile. Activation alone updates the active service definition. Determine the current runtime config from that definition: a historical root-level config can remain as retained evidence and is not necessarily active.

Fresh-client checks should include one account read, a bounded list/read that proves the intended data shape, and any newly introduced targeted tool. Check native Codex and cloud/account surfaces separately. Owner-reported mobile success is valid acceptance with its stated scope, not an automatically observed device test.

Keep the tunnel's private audience explicit. Public plugin distribution has its own endpoint and authentication requirements; changing the audience requires separate authorization.

Primary reference: [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels). These operational checks also reflect a verified private-host deployment on 2026-10-01. Recheck current commands and project policy when using them.
