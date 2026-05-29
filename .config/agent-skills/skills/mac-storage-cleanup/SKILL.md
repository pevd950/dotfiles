---
name: mac-storage-cleanup
description: Safely inspect and reclaim local Mac storage by classifying disk usage, Xcode and developer caches, Codex worktrees, simulator data, OrbStack or Docker state, Trash, and personal-data buckets before deleting anything.
---

# Mac Storage Cleanup

Use this skill when the user wants to find or reclaim disk space on a Mac safely.

## Default Stance

- Start read-only.
- Separate evidence from deletion recommendations.
- Do not treat macOS Storage categories as deletion instructions.
- Preserve active repo checkouts, main-checkout Docker volumes, dirty worktrees, personal data, and app data unless the user explicitly approves a specific cleanup.
- If deletion is requested, do the smallest bounded pass first.

## Read-Only Triage

1. Confirm host and free space:
   - `hostname -s`
   - `df -h /`
2. Inspect high-yield buckets before broad scans:
   - `du -xhd 1 "$HOME" 2>/tmp/du-home.err`
   - `du -xhd 1 "$HOME/Library" 2>/tmp/du-library.err`
   - `du -xhd 1 "$HOME/.codex" 2>/tmp/du-codex.err`
   - `du -xhd 1 "$HOME/Developer" 2>/tmp/du-developer.err`
3. Check snapshots and developer caches:
   - `tmutil listlocalsnapshots /`
   - `xcode-select -p` and `xcodebuild -version` when Xcode tools exist
   - `xcrun simctl list devices unavailable` when Simulator tools exist
   - inspect `~/Library/Developer`, project `.context`, DerivedData, SwiftPM caches, and other developer cache roots.
4. Attribute containers before pruning:
   - `docker ps -a --size`
   - `docker inspect --size <container>` for large candidates
   - use compose labels such as `com.docker.compose.project.working_dir` to distinguish main checkout state from branch or old-checkout state.
5. Classify personal/app-data buckets such as Messages, Photos, Group Containers, Application Support, and synced-drive folders as review-required by default.

## Xcode And Apple Developer Data

Close Xcode, Simulator, and active `xcodebuild` jobs before destructive cleanup. Prefer moving files to Trash when practical, and report the rebuild or redownload cost before deleting.

Start with size attribution:

```bash
du -xhd 1 "$HOME/Library/Developer" 2>/tmp/du-developer-library.err
du -xhd 1 "$HOME/Library/Developer/Xcode" 2>/tmp/du-xcode.err
du -xhd 1 "$HOME/Library/Developer/CoreSimulator" 2>/tmp/du-coresimulator.err
du -xhd 1 "$HOME/Library/Caches/com.apple.dt.Xcode" 2>/tmp/du-xcode-cache.err
du -xhd 1 "$HOME/Library/Caches/org.swift.swiftpm" 2>/tmp/du-swiftpm-cache.err
```

Use risk tiers:

- Low-risk with rebuild cost: stale `~/Library/Developer/Xcode/DerivedData`, Xcode logs, documentation/module caches, SwiftPM caches, and project-local `.build` or `.context` caches after confirming no active build depends on them.
- Low-risk via supported tool: unavailable simulator devices with `xcrun simctl delete unavailable`.
- Review-required: `~/Library/Developer/Xcode/Archives`, because archives and dSYMs may be needed for symbolication, resubmission, or App Store history.
- Review-required: `~/Library/Developer/Xcode/iOS DeviceSupport` and other device-support folders; remove only OS versions the user no longer debugs.
- Review-required: `~/Library/Developer/CoreSimulator/Devices`; deleting simulator devices can remove app containers, test databases, and local simulator state.
- Prefer Xcode UI for simulator runtimes: Xcode Settings > Components can remove unused runtimes. Terminal/runtime paths under `/Library/Developer/CoreSimulator` may be protected or managed by Xcode.

Do not delete all of `~/Library/Developer` unless Xcode and Apple-platform development are intentionally being removed from the host.

## Other Developer Caches

Common review buckets:

- Homebrew cache and logs.
- package-manager caches: npm, pnpm, Yarn, pip, Poetry, CocoaPods, Gradle, Maven, Cargo, Go modules, Flutter/Pub.
- repo-local generated output: `node_modules`, `Pods`, `.build`, `target`, `dist`, `coverage`, `.pytest_cache`, `__pycache__`.

Treat these as rebuild-cost decisions, not automatic deletion targets. For repo-local outputs, check the active repo state and ignored files first.

## Codex Worktree Cleanup

A Codex worktree is low-risk only when all are true:

- worktree is clean;
- HEAD is reachable from the intended base such as `origin/main`;
- upstream branch is gone or the user confirms it is obsolete;
- it is not the active checkout for a running task.

If cleaning Codex local state beyond worktrees, avoid deleting or rewriting active sessions while Codex is open. Prefer archive-style cleanup over permanent deletion when preserving chat history or generated artifacts may matter.

Use the repository's main checkout to remove it:

```bash
git -C /path/to/main-checkout worktree remove /path/to/worktree
git -C /path/to/main-checkout worktree prune
```

Do not delete worktree directories with `rm -rf` unless Git metadata is already broken and the user approves the fallback.

## Docker And OrbStack

- Preserve containers and volumes for the main checkout by default.
- Treat branch-specific stopped containers, old compose projects, and unused images as candidates only after labels or names prove ownership.
- `docker system df` can overstate safe reclaim because useful caches may be marked reclaimable.
- Explain rebuild cost before deleting volumes, module caches, databases, or object stores.

## Output

Report:

- largest verified buckets;
- low-risk cleanup candidates;
- review-required candidates;
- explicitly skipped items and why;
- exact commands to run, or exact commands already run;
- space before and after when cleanup was performed.

Stop with a recommendation rather than deleting when ownership is unclear, data is personal, permissions fail, or rebuild cost is not acceptable.
