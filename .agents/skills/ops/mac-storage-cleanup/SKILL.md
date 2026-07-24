---
name: mac-storage-cleanup
description: Safely inspect and reclaim local Mac storage by classifying disk usage, Xcode and developer caches, Codex worktrees, simulator data, OrbStack or Docker state, Trash, and personal-data buckets before deleting anything.
---

# Mac Storage Cleanup

Start read-only and separate evidence from deletion recommendations. macOS Storage categories are not deletion instructions. Preserve active repo checkouts, main-checkout Docker volumes, dirty worktrees, personal data, and app data unless the user explicitly approves a specific cleanup — and when deletion is approved, do the smallest bounded pass first.

## Read-only triage

1. Host and free space: `hostname -s`, `df -h /`.
2. High-yield buckets before broad scans: `du -xhd 1` on `$HOME`, `$HOME/Library`, `$HOME/.codex`, and `$HOME/Developer` (send stderr to a scratch file).
3. Snapshots and developer caches: `tmutil listlocalsnapshots /`; when Xcode tooling exists, `xcode-select -p`, `xcodebuild -version`, `xcrun simctl list devices unavailable`; inspect `~/Library/Developer`, DerivedData, SwiftPM caches, and project `.context`/`.build` roots.
4. Attribute containers before pruning: `docker ps -a --size`, `docker inspect --size <container>` for large candidates, and compose labels such as `com.docker.compose.project.working_dir` to distinguish main-checkout state from branch or old-checkout state.
5. Personal/app-data buckets (Messages, Photos, Group Containers, Application Support, synced-drive folders) are review-required by default.

## Xcode and Apple developer data

Close Xcode, Simulator, and active `xcodebuild` jobs before destructive cleanup. Prefer moving to Trash when practical, and report the rebuild or redownload cost before deleting. Attribute sizes first with `du -xhd 1` on `~/Library/Developer`, `~/Library/Developer/Xcode`, `~/Library/Developer/CoreSimulator`, `~/Library/Caches/com.apple.dt.Xcode`, and `~/Library/Caches/org.swift.swiftpm`.

Risk tiers:

- Low-risk with rebuild cost: stale DerivedData, Xcode logs, documentation/module caches, SwiftPM caches, and project-local `.build`/`.context` caches after confirming no active build depends on them.
- Low-risk via supported tool: `xcrun simctl delete unavailable`.
- Review-required: `Xcode/Archives` — archives and dSYMs may be needed for symbolication, resubmission, or App Store history.
- Review-required: `iOS DeviceSupport` and other device-support folders — remove only OS versions the user no longer debugs.
- Review-required: `CoreSimulator/Devices` — deleting simulator devices removes app containers, test databases, and local simulator state.
- Simulator runtimes: prefer Xcode Settings > Components; runtime paths under `/Library/Developer/CoreSimulator` may be protected or Xcode-managed.
- Never delete all of `~/Library/Developer` unless Apple-platform development is intentionally being removed from the host.

## Other developer caches

Homebrew cache/logs; npm, pnpm, Yarn, pip, Poetry, CocoaPods, Gradle, Maven, Cargo, Go module, and Flutter/Pub caches; repo-local outputs (`node_modules`, `Pods`, `.build`, `target`, `dist`, coverage and pycache dirs). All are rebuild-cost decisions, not automatic targets. Check active repo state and ignored files before touching repo-local output.

## Codex worktrees

A worktree is low-risk only when all hold: clean; HEAD reachable from the intended base such as `origin/main`; upstream branch gone or confirmed obsolete; not the active checkout for a running task. Remove through the main checkout — `git -C <main-checkout> worktree remove <path>` then `worktree prune` — never `rm -rf` unless Git metadata is already broken and the user approves the fallback. For other Codex local state, avoid deleting or rewriting active sessions while Codex is open, and prefer archive-style cleanup where chat history or generated artifacts may matter.

## Docker and OrbStack

Preserve main-checkout containers and volumes by default. Branch-specific stopped containers, old compose projects, and unused images become candidates only after labels or names prove ownership. `docker system df` overstates safe reclaim because useful caches count as reclaimable. Explain rebuild cost before deleting volumes, module caches, databases, or object stores.

## Output

Largest verified buckets; low-risk candidates; review-required candidates; explicitly skipped items and why; exact commands run or to run; before/after space when cleanup happened. Stop with a recommendation instead of deleting when ownership is unclear, data is personal, permissions fail, or rebuild cost is not acceptable.
