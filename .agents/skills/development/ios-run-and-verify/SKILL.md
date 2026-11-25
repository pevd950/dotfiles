---
name: ios-run-and-verify
description: Pablo's rules for running and verifying an iOS app, covering which tool to use, binding to the repo's simulator and build settings, and cleanup. Load whenever building, running, or checking an iOS app on a simulator or device, or working with TestFlight and App Store Connect, alongside the tool's own debugger skill.
---

# iOS run and verify

These rules sit on top of the tool-specific skills (the iOS plugin's debugger skill,
Xcode's own skills), which carry the mechanics.

## Tools

- **XcodeBuildMCP (MobileBuildMCP upstream)** for builds, tests, simulator runs,
  logs, and LLDB. Discover installed tools first; names vary by version.
- **Device MCP** for interactive device and simulator checks: tap, type, and
  capture. Use screenshots when a simulator accessibility tree is unavailable.
  Device Hub is a GUI, not another MCP server.
- **Native Xcode MCP** for Xcode workspace, IDE, and preview tasks when available.
  **AXe** is a targeted fallback for simulator controls or capture, including
  fold posture. Use the same target; verify the observed posture and active
  screen or geometry, not just that the fold command succeeded.
- **`asc`** for App Store Connect build, TestFlight, version, and review status.

## Reserve and verify the target

1. **Use the repo's paved path.** Read its instructions, scripts, and test gates
   first. Bind the project or workspace, scheme, configuration, DerivedData,
   fixtures, runtime, and simulator UDID before building or running.
2. **Get exclusive use before touching a simulator.** Follow the repo's lease or
   queue and record the owner and target. A booted simulator is not a free slot.
   If busy, wait or use the documented fallback. If the repo allows a disposable
   simulator, name it for the project, agent, and worktree or thread. Do not
   restart, erase, or reprofile a shared target to get unstuck.
3. **Keep tools on the same target.** Check the actual destination again when
   changing tools; XCTest can run on a clone rather than the requested UDID.
   Record both when they differ. Diagnose the failed phase (lease, boot, build,
   launch, test discovery, test execution, UI check, or distribution). Try at
   most one bounded repo-supported recovery or fallback, only if safe and
   authorized for the target and failed phase. If ownership, the lease, access,
   or authorization blocks the action, report the blocker; don't retry through it.
4. **Prove the requested outcome.** For a run, check the expected app state after
   launch. For a test, report which tests actually ran and passed. For motion
   or input behavior, record motion or exercise the interaction; a still image
   proves only layout. Report simulator, physical-device, and TestFlight
   evidence separately. A build or install alone is not a successful run.
5. **Clean up only what you own.** Shut down simulators you booted, delete only
   disposable simulators your job created, remove temporary output you own, and
   release your lease. Leave pre-existing devices, data, and build output alone.

## Prefer slim when it meets the test's needs

- Prefer a repo-approved slim target for compatible UI smoke tests. Keep slim
  and full targets separate. Use full when required services, fixture fidelity,
  or the repo's gate are not validated in slim mode.
- When Device MCP starts the simulator, select integrated slim only if the repo
  permits it, the runtime supports it, and the workload's required services and
  fixture behavior are verified in that mode. Otherwise use the repo-approved
  full simulator; if that fallback is unavailable, report the blocker. Don't
  layer standalone SimSlim over integrated slim. Verify the live Slim/Full
  state after boot; the requested mode and actual boot can differ. If the repo
  permits standalone SimSlim, apply it only to a job-owned disposable simulator
  and verify its live profile.
- Check the exact mode against the workload. The two tools do not necessarily
  retain the same services (for example, push, StoreKit, universal links, and
  widgets). Verify the app behavior as well as the profile. If compatibility is
  unknown or a required service is missing, use a separate full simulator via
  the repo's fallback; never label a fallback run as slim.
- To evaluate a new workload, compare slim and full with the same build,
  runtime, fixtures, test, and comparable host load. Report boot/setup,
  execution, and cleanup times separately, plus memory and the app/test result.
  Do not infer a build speedup from a reduction in simulator memory.

Tool references: [Device MCP slim simulators](https://devicemcp.ai/docs/devices/ios-simulator#6-slim-simulators),
[SimSlim profiles and limitations](https://github.com/MobAI-App/simslim#what-you-lose).
