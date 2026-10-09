# UI and capability parity

Use [UI extensions and acceptance](ui-extensions.md) for surface selection, registration, and installed-client acceptance. This reference adds consolidation, provider capability, and recovery checks.

## Verify the supported surface

Read the current [MCP Apps UI guide](https://developers.openai.com/plugins/build/chatgpt-ui), [plugin extensions](https://developers.openai.com/plugins/build/extensions), and [packaging schema](https://developers.openai.com/plugins/build/plugins). Use inline UI for focused results, and sidebar or conversation entrypoints when the requested workflow needs a persistent workspace. Implement the complete selected contract; entrypoints must accept empty arguments and should have meaningful titles and icons. Do not infer support across clients from one successful web test.

Keep provider access, MCP transport, UI rendering, and installation identity separate. Hosting does not dictate whether users open a separate website. An upstream server can supply useful tools while lacking image blocks or UI resources; bundling a skill cannot intercept those responses. Compare extending maintained server code, a bounded adapter, and a unified backend before creating a companion integration. Reuse provisioned identities where supported and retain recovery until replacement acceptance.

## Images and previews

Return actual MCP image content for model-visible images, with appropriate UI-only metadata for an embedded gallery. Base64 inside a text JSON field is not proof of a user-visible image. Verify actual rendering in the requested client and record owner confirmation precisely.

Distinguish a fresh layout render, a stored rendered screen, the provider's reported current screen, and physical-device delivery. Record dimensions, freshness and provenance. Do not substitute one for another. Respect render budgets and pending/completed/expired job semantics; do not fetch completed jobs again merely because the model-visible text omits the image.

If the official dashboard supports a preview that an API call denies, inspect the authorized dashboard and documented alternatives. A denial is specific to that endpoint and credential class. It neither proves the feature impossible nor authorizes bypassing access controls with session credentials. Browser-assisted inspection is not proof that cloud or mobile tools can perform the same operation unattended.

## Capability coverage

For dashboard parity, keep a compact matrix of the requested operation, provider contract, credential availability, exposed tool, UI control and installed-client evidence. A documented endpoint, discovered schema or operation count does not establish working access. Mark confirmed restrictions separately from untested operations. Test bounded representative reads and authorized reversible writes; keep unsupported account-connection and credential steps explicit.

When deriving operations from OpenAPI, merge path-level and operation-level parameters, preserve required fields and pagination, validate schemas and resource IDs, and handle binary/multipart operations deliberately. Restrict calls to registered routes. Generic operation forms can extend advanced coverage but do not replace usable controls for the primary workflows. Never ship a dead-end primary control backed only by a known-denied endpoint.

## Acceptance

After changing server tools, refresh the installed app catalog where the client requires it, then test in a fresh conversation. A successfully uploaded skill/package does not refresh server schemas automatically. Recheck package version, skill and artwork after app metadata edits or tool refresh: some client paths regenerate the package metadata. Restore the intended package after those steps when needed. Record backend, connected-app metadata and package versions separately; rename both package and connection metadata when consolidating.

Test the complete chain: registered tool schema, resource metadata and bridge, provider data, visible result, installed identity/artwork, and requested client. For consolidation, verify the replacement contains both management and UI before removing a redundant installation. Record exact package and runtime versions separately, remaining provider gaps, and recovery. Keep private identifiers, device names, signed image URLs and credentials out of portable skills and public source.

If a browser redacts a credential after the owner approves its use, respect that boundary. Have the owner store it in the existing vault item, then retrieve only the specified fields through the approved secret-store interface. Do not ask for the secret in chat or extract protected browser state.

For restricted edge runtimes, compile schema validators at build time. Node tests can pass while lazy `new Function` compilation fails during deployed requests. Run validation tests with dynamic code generation disabled and exercise a deployed read plus prepared write before claiming management acceptance.

## Mobile result and workspace presentation

Use a focused UI resource for image/result tools and a separate workspace resource for the sidebar entrypoint within the same integration. Avoid automatically loading a dashboard or opening a modal behind an inline result: hosts may capture that entire layout as the conversation card. Keep the requested resource identity in refresh actions, and make the initial result useful even when the host presents a noninteractive snapshot. Do not claim a card is live merely because the full app is interactive on another client.

Apply `hostContext.safeAreaInsets` from MCP Apps at initialization and on context changes. ChatGPT's `window.openai.safeArea.insets` and `openai:set_globals` can supply the platform fallback. CSS `env(safe-area-inset-*)` alone does not describe host header/composer overlays inside an iframe. Respect these insets for the page and dialogs; test controls at the top and bottom of the actual mobile app. Verify sidebar entrypoint icons separately from package/composer artwork.

Desktop sidebar hosts may render entrypoint artwork as an alpha mask while mobile displays the full-color image. Use a transparent glyph for the entrypoint and keep full-color package/composer artwork separate; an opaque square background can become a solid monochrome tile. Verify both surfaces rather than treating one client as authoritative for all.

Owner testing can reveal that reported safe-area values still leave controls covered. Preserve the larger standard/platform inset rather than allowing a zero from one source to override the other. If necessary, add a bounded, documented mobile fullscreen/workspace clearance fallback while keeping inline results compact. Treat the fallback as pending native-client acceptance; a layout unit test is not iPhone evidence.

If mobile spacing remains wrong after host-inset handling, stop treating deployment as acceptance. Test an app-owned inner content container under a synthetic host overlay and body-style reset, apply narrow-layout CSS independently of host device classification, and temporarily expose version/geometry diagnostics to distinguish stale resources from ineffective CSS. Do not assume the synthetic reproduction proves the native client is fixed.

For dashboard editors, test the editing workflow as well as the initial card: long labels, narrow layouts, scrolling dialogs, keyboard focus and reachable footer actions. Keep structural diagrams explicitly labeled as layout guides; they are not provider-rendered previews. Preserve unsaved choices when users switch layouts, and keep visual cleanup separate from live provider mutations. A read-only harness can use real account reads while blocking prepare/commit actions.

Choose mutation snapshots by semantic ownership, not simply a matching GET URL. A provider may expose writes and reads at the same path for different resource types. If a read mixes stored user data with generated render context, persist an explicit snapshot projection and reuse it for preparation, drift checks, readback and reconciliation. Exclude volatile context only when it is outside the state being changed; fail closed when authoritative data is missing. Preserve the comparison semantics of older saved drafts.

When browser-captured originals fill a provider image-access gap, keep bytes in owner-private storage and metadata keyed by the displayed resource identity. Preserve capture time separately from an unknown render time. Validate membership at import and readback; label stale captures and retain missing placeholders. Import/readback must be tested through the installed integration. Viewing cached images from cloud/mobile does not establish unattended browser refresh. Do not store signed image URLs or browser sessions in the integration.
