---
name: ios-debugger-agent
description: Use XcodeBuildMCP to build, run, launch, and debug the current iOS project on the repo-selected simulator. Trigger when asked to run an iOS app, interact with simulator UI, inspect on-screen state, capture logs, or diagnose runtime behavior with XcodeBuildMCP.
---

# iOS Debugger Agent

Use this skill for iOS simulator build/run/debug work driven by XcodeBuildMCP.

## Goal

Bind XcodeBuildMCP to the right project, scheme, DerivedData path, and simulator before build/run work. Do not guess from whichever simulator happens to be booted.

## Core Workflow

1. Check session state first.
- `XcodeBuildMCP/session_show_defaults`
- If defaults are already correct for the current repo + simulator, reuse them.

2. Prefer repo-provided simulator/setup guidance when available.
- Check local repo guidance first (`AGENTS.md`, `README.md`, Makefile targets, helper scripts) for any documented XcodeBuildMCP setup flow, simulator lease workflow, or required scheme/configuration pairing.
- If the repo publishes a specific simulator lease, recommended device, derived-data path, or setup/export command, use that instead of inferring from Simulator.app state.
- Do not bind to an arbitrary booted simulator when the repo already documents a preferred target-selection workflow.

3. Set explicit XcodeBuildMCP defaults.
- Use `XcodeBuildMCP/session_set_defaults` with the resolved:
  - `projectPath` or `workspacePath`
  - `scheme`
  - `configuration`
  - `derivedDataPath`
  - `simulatorId`
  - `platform: "iOS Simulator"`
- After setting defaults, re-run `XcodeBuildMCP/session_show_defaults` once to confirm them.

4. Build or launch with the narrowest tool that matches the request.
- Build + launch: `XcodeBuildMCP/build_run_sim`
- Build only: `XcodeBuildMCP/build_sim`
- Launch existing app: `XcodeBuildMCP/launch_app_sim`
- Launch with logs: `XcodeBuildMCP/launch_app_logs_sim`
- If bundle ID is unknown:
  1. `XcodeBuildMCP/get_sim_app_path`
  2. `XcodeBuildMCP/get_app_bundle_id`

5. Interact with the running app using current tools.
- Inspect hierarchy: `XcodeBuildMCP/snapshot_ui`
- Tap: `XcodeBuildMCP/tap`
- Type: `XcodeBuildMCP/type_text`
- Swipe/gesture: `XcodeBuildMCP/swipe` or `XcodeBuildMCP/gesture`
- Screenshot: `XcodeBuildMCP/screenshot`

6. Capture logs when debugging runtime behavior.
- Start capture: `XcodeBuildMCP/start_sim_log_cap`
- Stop capture: `XcodeBuildMCP/stop_sim_log_cap`
- Prefer `launch_app_logs_sim` when a relaunch is acceptable.

## Troubleshooting

- If a build or launch call times out, switch to `xcodebuildmcp-timeout-recovery`.
- If the wrong app or wrong simulator is active, re-check repo guidance and reset defaults instead of continuing.
- If the repo has no explicit simulator-selection guidance, then use `XcodeBuildMCP/list_sims` and choose a simulator deliberately; do not assume "Booted" means "correct".
- If `XcodeBuildMCP/snapshot_ui` fails to return a hierarchy, assume the UI may be covered by a dialog, not fully rendered yet, or in a transient simulator state. Retry inspection once after the app settles, and use `XcodeBuildMCP/screenshot` as the next fallback.
- If `XcodeBuildMCP/screenshot` also stalls or times out during that fallback, stop the loop and switch to `xcodebuildmcp-timeout-recovery`.

## Guardrails

- Never assume a currently booted simulator is the correct target.
- Never use generic `Debug` if the repo/workflow requires a scheme-specific configuration.
- Prefer explicit session defaults over one-off tool arguments when multiple XcodeBuildMCP calls will follow.
