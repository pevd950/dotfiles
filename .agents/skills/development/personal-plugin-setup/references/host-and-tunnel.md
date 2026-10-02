# Private host and Secure MCP Tunnel

Use this route for a server that needs private APIs, local data, native dependencies, or an established private runtime. Discover ownership from private configuration; when host routing matters, use [cross-host-context](../../../ops/cross-host-context/SKILL.md) if available. Verify paths, tools, credentials, and supervision on the owning host. Keep actual routes and identities out of reusable instructions.

## Separate the boundaries

- **Provider:** the connector's API key or dedicated OAuth grant, independent of unrelated apps/CLIs.
- **Server:** bounded MCP tools and private credential/state storage.
- **Tunnel supervisor:** its OpenAI runtime key, supplied only to `tunnel-client`; exclude it from the provider process's environment and logs.
- **Account plugin:** the intended Platform organization, ChatGPT workspace, audience, and client connection.

Secure MCP Tunnel uses outbound HTTPS to OpenAI and reaches a private stdio or HTTP server. It does not require public inbound exposure. Organization tunnel access and workspace/plugin access are separate. Creation/edit requires Tunnels Read + Manage; runtime use/selection requires Read + Use. A missing picker entry warrants checking workspace association and existing permissions, not automatically expanding them. See [current tunnel documentation](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

## Configure and verify

Use the supported `tunnel-client` release and live help. Generate the appropriate stdio profile or HTTP configuration, then validate it with the documented commands. Save the tunnel identity, runtime key reference, scope, and expiry privately in 1Password.

Supply secrets through supported injection or a private file. If human entry is needed, show the actual masked prompt and identify the target runtime before asking for entry. Keep keys out of chat, command arguments, screenshots, and tracked configuration.

Use the owning project's installer/supervisor. Keep configuration, rotating credentials, and write-state stores independent of immutable release directories. Verify the active service definition to find the current config; a retained root-level file may be historical. Avoid competing pollers for one tunnel, including diagnostic daemons.

Check `/healthz`, `/readyz`, and bounded connection status, then perform a useful authenticated tool call through the account plugin. Configuration validation such as `doctor` does not prove key authentication or provider access. Test denial using a controlled invalid/missing-credential probe that cannot dispatch provider work. Preserve private logs and keep the admin listener local unless a separately authorized design requires otherwise.

Discover tools and execute them in each requested client. Desktop and account/cloud surfaces can expose different configurations. Record owner-reported mobile acceptance with its release/scenario rather than turning it into an automatically observed device test.

## Bounded diagnostics

Compare transport status, runtime errors, provider status, and host resource pressure. A healthy loopback listener can coexist with failed real reads. Use a small request/time budget; avoid raw request logging, extra pollers, and changes to unrelated workloads.

OAuth discovery may travel through the tunnel, but the provider authorization server is not automatically tunneled. Validate its browser/runtime reachability separately. Keep audience changes and public distribution outside a private-host fix unless requested.
