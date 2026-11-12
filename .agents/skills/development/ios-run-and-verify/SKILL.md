---
name: ios-run-and-verify
description: Pablo's rules for running and verifying an iOS app, covering which tool to use, binding to the repo's simulator and build settings, and cleanup. Load whenever building, running, or checking an iOS app on a simulator or device, or working with TestFlight and App Store Connect, alongside the tool's own debugger skill.
---

# iOS run and verify

These rules sit on top of the tool-specific skills (the iOS plugin's debugger skill,
Xcode's own skills), which carry the mechanics.

## Tools

- **XcodeBuildMCP** for builds, tests, simulator runs, logs and LLDB. List its
  tools first; names change between versions.
- **Device MCP** for driving a simulator or a physical device: taps, typing,
  screenshots, the element tree. Prefer it over Xcode's device interaction tools.
- **`asc`** for builds, TestFlight, versions and review state in App Store Connect.

## Rules

1. **Bind to the repo's choices before any build or run:** project or workspace,
   scheme and configuration, DerivedData path and simulator, taken from repo
   guidance (`AGENTS.md`, README, Makefile targets, helper scripts). A simulator
   that is already booted may belong to other work. When the repo has a simulator
   lease workflow, wait for the lease or use the repo's fallback.
2. **Name what you create.** A simulator you create or clone is named for its
   owner: project, agent, and worktree or thread, for example
   `stuff-codex-holiday-sharing`. Anyone can then tell whose it is, and you can
   find it again for cleanup.
3. **Done means the app ran.** Check the screen after launch (element tree or
   screenshot), and report a tooling blocker instead of claiming validation.
4. **Clean up:** shut down simulators you booted, delete simulators you created,
   and remove build output you created outside the repo's DerivedData path. Leave
   what was there before you started.
