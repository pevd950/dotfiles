# UI extensions and acceptance

Use this reference when commissioning or upgrading a plugin with a visual interface. UI is optional; select it for a concrete user workflow and keep the existing tool contract authoritative.

## Choose the surface

Compare a focused view inside the conversation with a persistent browsing or editing workspace. Prefer the smaller interface when it completes the task; choose a workspace when navigation or sustained interaction needs more room.

| Surface | Choose when |
| --- | --- |
| Inline MCP App | A result needs a compact preview, comparison, or selection |
| Sidebar app | Users need to enter a browsing or editing workspace independently of a conversation |
| Conversation panel | Users need to consult or manipulate data while continuing the same conversation |
| File viewer/editor | Opening a supported file is the workflow's natural starting point |
| Composer content mentions | Users need to find and attach a particular plugin item to a request |
| Rich form | A tool needs structured choices or input that is easier to collect visually |

Record the selected surface, entry action, expected result, and intended clients. Avoid adding a dashboard solely because the extension exists. New UI does not create provider operations: display only supported actions and describe cache age and incomplete results truthfully.

## Implement against current documentation

Read the relevant official guide before choosing SDK versions or copying metadata:

- [Plugin Extensions](https://developers.openai.com/plugins/build/extensions): sidebar and conversation entrypoints, file handlers, content mentions, forms, and links to SDKs and the protocol specification.
- [Add UI to your MCP server](https://developers.openai.com/plugins/build/chatgpt-ui): MCP Apps resources, bridge, presentation, and state ownership.
- [UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines): layout, interactions, and accessibility.
- [Build plugins](https://developers.openai.com/plugins/build/plugins): package and distribution requirements.

Start with the standard MCP Apps UI resource and bridge. Add OpenAI extensions for the chosen surfaces; use capability detection and a useful fallback where possible. A registered UI resource connects a rendering tool to its interface. OpenAI entrypoint metadata selects `global` for the sidebar, `thread` for a conversation panel, or a supported `file` handler. Verify the current full registration contract rather than treating a logo or directory listing as app registration.

Keep business data and authorization on the server; keep temporary selection and layout state in the UI. Send relevant selections or staged edits to model-visible context without exposing credentials or unrelated private data. Return authoritative state after actions and preserve compatible UI state. Reuse data tools for UI actions; separate rendering where it prevents unnecessary remounts. Existing write approval, stale-preview, and uncertain-dispatch protections still apply.

Use the available ChatGPT/MCP app-building skill for implementation mechanics when relevant. Follow the linked documentation if that skill is absent or predates the required extension.

## Prove the installed interface

For each selected surface and intended client:

1. Verify the installed package/source and registration. Open the interface from its intended entry action in a fresh session.
2. Check that it renders a bounded authenticated result with the correct item identity, data shape, and freshness/completeness information.
3. Exercise the relevant selection, navigation, or form interaction. Verify conversation context updates where the workflow depends on them. For edits, use an authorized scenario and read back the server state.
4. Check loading, empty, and error states, usable layout, and keyboard access for the chosen controls. Verify that reopening or rerendering preserves appropriate state and does not repeat a mutation.
5. Test the tool workflow without UI and report unsupported client/surface combinations explicitly.

Capture the smallest sanitized visual evidence beside acceptance claims, bound to the tested version and client. Source tests and accepted metadata cannot prove the interface appeared or worked in a live client.

Documentation checked 2026-10-02. At that time, composer content mentions were desktop-only and web extensions for Free and Go were listed as coming soon. Refresh availability for the intended account/client before promising support; general plugin availability does not establish every UI surface.
