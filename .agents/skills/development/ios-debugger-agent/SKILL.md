---
name: ios-debugger-agent
description: Use XcodeBuildMCP to build, run, launch, and debug the current iOS project on the repo-selected simulator. Trigger when asked to run an iOS app, interact with simulator UI, inspect on-screen state, capture logs, or diagnose runtime behavior with XcodeBuildMCP.
---

# iOS Debugger Agent

Bind XcodeBuildMCP to the right project, scheme, DerivedData path, and simulator before build/run work. Never assume the currently booted simulator is the correct target.

## Workflow

1. `XcodeBuildMCP/session_show_defaults` — reuse defaults if they already match the current repo and simulator.
2. Prefer repo guidance (`AGENTS.md`, README, Makefile targets, helper scripts) for simulator lease workflows, recommended devices, derived-data paths, and scheme/configuration pairing. Only if the repo documents nothing, choose deliberately from `XcodeBuildMCP/list_sims`.
3. Set explicit defaults with `session_set_defaults` (`projectPath`/`workspacePath`, `scheme`, `configuration`, `derivedDataPath`, `simulatorId`, `platform: "iOS Simulator"`), then confirm with `session_show_defaults`. Never use generic `Debug` when the workflow requires a scheme-specific configuration. Prefer session defaults over one-off tool arguments when multiple calls will follow.
4. Use the narrowest tool: `build_run_sim`, `build_sim`, `launch_app_sim`, or `launch_app_logs_sim`. Unknown bundle ID: `get_sim_app_path` → `get_app_bundle_id`.
5. Interact with `snapshot_ui`, `tap`, `type_text`, `swipe`/`gesture`, and `screenshot`; capture logs with `start_sim_log_cap`/`stop_sim_log_cap`, or prefer `launch_app_logs_sim` when a relaunch is acceptable.

## Failure handling

- Build/launch timeout: one deliberate retry after checking whether package resolution, DerivedData warmup, or a long-running repo wrapper is still in flight. A second timeout means XcodeBuildMCP is blocked for this turn — fall back to the repo's documented host-side wrappers when they exist, and carry the MCP blocker forward explicitly instead of claiming validation is complete.
- Simulator lease owned by another worktree: wait for the lease or continue with repo-approved non-MCP validation. Do not steal it with a guessed booted simulator; re-run the repo's resolver helpers rather than improvising replacement defaults.
- `snapshot_ui` returns no hierarchy: the UI may be covered by a dialog, not yet rendered, or in a transient state — retry once after the app settles, then fall back to `screenshot`. If that also stalls, stop the loop, report the tooling blocker, and switch to the repo's non-MCP fallback path if one exists.
- Wrong app or simulator active: re-check repo guidance and reset defaults instead of continuing.
