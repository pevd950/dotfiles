---
name: personal-plugin-setup
description: Choose hosting and set up a private account plugin across ChatGPT, mobile, Dot, Cloud Work and native Codex. Use for a new service connector, a plugin upgrade, or an authorized release cutover; covers hosted MCP reuse, private-host Secure MCP Tunnels, ChatGPT Sites, 1Password, branding and installed-source validation.
---

# Personal plugin setup

Deliver the requested capabilities from a reproducible release and verify them in the intended clients. Track connection, CI and source merge separately from installed-source and client acceptance. This procedure is a draft; installation and changes to shared configuration need the applicable authorization.

## Establish the target and authority

- Read the current request and earlier approvals. Reuse explicit authorization within the named project; ask when an action or change of scope needs new authority.
- Identify the requested reads, writes, clients and privacy boundary. Include the requested write capabilities. If the provider cannot support one, confirm that limitation in current documentation and explain the supported alternative.
- New provider terms, expanded account permissions, purchases and publication of private data need specific authorization. Prepare a concrete, reviewable proposal before requesting approval. If an action is blocked, identify the policy or automatic-review reason.
- Honor draft-only, review-only and explicit no-deploy scope. For authorized implementation and release work, continue after merge through deployment, any needed migration and verification. Limit the work to the active project.
- GitHub Issues own the technical plan, contracts and acceptance. Todoist is a concise progress surface linked to the Issue. Craft owns durable operational knowledge; private credential references and runtime routing stay private.

## Choose the simplest adequate hosting

Inspect existing account plugins, provider offerings and maintained upstream implementations before building. Confirm licensing, authentication, tool behavior and hosting. Distinguish reusable server code from a service that is already hosted.

| Choice | Prefer when | Evidence needed |
| --- | --- | --- |
| Existing trusted remote MCP | Its supported capabilities, authentication and data boundary fit | Current endpoint/tool inspection and one bounded account read |
| Private host + Secure MCP Tunnel | Local data, host APIs or established private runtime ownership matter | Owning-host runtime and tunnel checks, then an actual account-plugin call |
| ChatGPT Sites MCP | No host-specific dependency; an HTTP implementation and cloud persistence fit | Published Site, provisioned plugin connection and actual tools |
| Local desktop MCP | User explicitly wants local-only use | Actual local client call; do not imply web/mobile availability |

Use the [host and tunnel procedure](references/host-and-tunnel.md) or [Sites procedure](references/sites-mcp.md) after selection. A stdio service with Node filesystem dependencies needs an adapted design for Sites. For consequential authentication or mutation-state decisions, compare at least two materially different designs in the Issue, including interface complexity, coupling and recovery usability.

## Define a usable, bounded contract

- Use documented provider APIs, stable IDs and one account boundary. Keep provider-specific routes and normalization inside a cohesive adapter; avoid exposing arbitrary URLs, shell commands or a provider CLI to callers.
- Make output useful for the task. Episode rows need parent show identity; recommendations need targeted watched checks; pagination needs truthful totals and completeness. Represent unproven absence, missing counts and incomplete traversal as unknown.
- Bound raw input, bytes, pages, fan-out, concurrency, timeouts and durable pending state. Validate identifiers and contradictory metadata before exposure, cache insertion or write preparation.
- Keep advertised tools, account access and guidance consistent. Validate actual MCP schemas with a real client. If offering Skills resources, implement the declared extension's required result, cache, UTF-8 size and digest fields. Describe base-protocol support accurately.
- For writes, require confirmation of the exact returned preview of one resolved effect, with before/after state and a short expiry. Existing confirmation covers that preview while it remains valid; avoid asking again for the same preview. General setup approval does not confirm a new provider mutation.
- A possibly sent request is never replayed blindly. Retain permanent intent/claim/outcome evidence, distinguish known rejection from uncertainty, and expose result lookup and central recovery. Promise at-most-once local dispatch only unless the provider actually supplies stronger guarantees.
- When independent processes share consequential state, prefer atomic domain transactions to a custom multi-file protocol. Keep HTTP outside local transactions. Define process-death, lost-acknowledgment, publication-failure, stale-preview and operator-recovery behavior before implementation.

## Prepare credentials and branding before launch

Use the 1Password Environments skill and [credential/release procedure](references/credentials-and-release.md). Retrieve the actual secret while interactive access is available and verify the intended credential. An item UUID alone is insufficient. Reusing a CLI credential requires authorization and a verified match. Keep existing integrations' grants independent.

Include official or appropriately licensed logo and composer artwork in the first package. Use the current manifest format, plugin-root-relative asset paths, square artwork and padding that survives circular masks. Preserve connection references and capability scope on branding updates. Check accepted package metadata and visible client rendering separately. Record a remaining fallback icon as unresolved.

## Validate, review and deliver

1. Isolate the checkout and pin dependencies. Run repository-required checks and meaningful behavioral regressions. Reproduce a reported defect before making the smallest cohesive fix. Documentation edits do not need artificial regressions; report precisely which tests failed before a fix.
2. Stage a release from the exact committed source. Staging must preserve every active input. Verify the owning host's runtimes, locked install, checks and release contents before activation.
3. Start PRs as drafts. When the coherent change is ready, mark ready and use `babysit-pr` with `gh-pr-address-feedback`. Keep one monitor and record its actual saved target, current SHA and approval scope. Any exception to reviewer requirements must apply to this PR.
4. Read complete review bodies and inline findings for the current commit. Apply the agreed project review criteria and explicit merge authorization. Distinguish a no-findings COMMENTED review from formal approval; CI results, acknowledgments, resolved threads and capacity limits are separate evidence. Address validated findings. Review feedback does not authorize unrelated code changes or changes to provider or security settings.
5. If findings repeatedly affect the same persistence or recovery design, pause and reassess the architecture. Review invariants, alternatives and operational burden before continuing. Document the reasoning; a test count or review label alone cannot establish that the design is sound.
6. After authorized merge, verify merge SHA, main ancestry and reviewed-tree equivalence. Continue to authorized deployment and any applicable migration using the release procedure. An explicit source-only constraint still wins.
7. Prove the active source, service readiness, restart/recovery, credential denial and affected read paths. Refresh existing tool definitions when needed; reuse the account plugin instead of creating duplicates.
8. Test fresh sessions on requested clients. Record automated observations and owner-reported web/mobile acceptance separately. A reversible live write test needs confirmation of its exact preview and cleanup scope. State when that test has not been performed.
9. Update the canonical GitHub acceptance evidence with the smallest sanitized visual summary beside its claims. Preserve private handoffs and 1Password metadata. Complete Todoist only for the acceptance it actually represents.
10. Delete the completed PR monitor and verify record absence. Document key expiry and renewal action in the handoff. Create reminders or ongoing schedules only when requested.

## Handoff

Lead with what is installed and usable. Include the active commit, source/review evidence, tested clients, remaining unknowns, credential expiry and compatible recovery path. Save generated handoffs and this draft in the configured AI Inbox before attaching them to Craft. Keep account IDs, tunnel IDs, private links, host topology, credentials and viewing/library data outside tracked/shared files and GitHub. Use symbolic variables in reusable examples.

References checked 2026-10-01. Recheck provider and OpenAI documentation when using this procedure.
