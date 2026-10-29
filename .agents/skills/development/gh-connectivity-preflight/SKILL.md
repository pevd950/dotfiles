---
name: gh-connectivity-preflight
description: "Classify GitHub CLI and Git transport/auth failures before PR, CI, issue, or dotfiles work. Use when gh, Git HTTPS, DNS, local user lookup, credential helpers, Keychain, or token environment overrides may be the real blocker."
---

# GitHub Connectivity Preflight

Identify the failing layer without exposing credentials or mutating auth state.

## Safety rules

- Do not print token values, Keychain entries, credential-helper output, cookies, or 1Password secret values.
- Do not display raw remote URLs, helper definitions, or provider/transport stderr. Use the status-only helper below; do not collect verbose Git/curl traces or attempt to redact arbitrary secrets with a regex.
- Do not run `gh auth login`, delete credentials, change credential helpers, or modify Keychain unless the user explicitly approves that repair.
- Prefer read-only probes. If a probe could write, push, delete, revoke, or rotate credentials, stop and ask.
- Redact account identifiers in shared notes unless they are already-public repo/user names needed for routing.
- Treat `GH_TOKEN` and `GITHUB_TOKEN` as high-precedence overrides: an invalid env token breaks `gh` even when Keychain auth is healthy.

## Fast path

Run in the failing checkout; on the first failure, stop broad probing and classify below. Resolve this skill's `scripts/git_diagnostics.py` from the installed skill directory (the canonical path is shown). It emits only transport/helper categories, never URLs, helper arguments, or trace files:

```bash
gh --version | sed -n 1p
if gh auth status -h github.com >/dev/null 2>&1; then echo 'gh auth: ok'; else echo 'gh auth: unavailable'; fi
python3 "$HOME/.agents/skills/development/gh-connectivity-preflight/scripts/git_diagnostics.py"
python3 "$HOME/.agents/skills/development/gh-connectivity-preflight/scripts/git_diagnostics.py" --probe
```

## Layers

**`gh-cli-missing` / `gh-cli-broken`** — `command not found: gh` or `gh --version` fails before auth checks. Use the GitHub connector for read-only metadata; route local repair to host bootstrap/dotfiles. Do not install packages unasked.

**`env-token-override`** — auth/API calls fail while token vars are set. Probe presence without printing values (`test -n "${GH_TOKEN:-}" && echo GH_TOKEN=set`); compare exit status with `env -u GH_TOKEN -u GITHUB_TOKEN gh auth status -h github.com >/dev/null 2>&1`. Fix: ask before editing shell files; move stale automation-only exports into ignored host-local config or 1Password references — never copy raw token values into tracked docs.

**`gh-auth-or-scope`** — network works but `gh api user >/dev/null 2>&1` fails. Ask the user to re-auth or approve a repair path; use the GitHub connector for read-only PR/issue metadata meanwhile. Keep provider output suppressed, including on failures.

**`dns-network`** — DNS lookup fails (`dscacheutil -q host -a name github.com` or `nslookup github.com`), `curl -I --max-time 10 https://github.com >/dev/null 2>&1` cannot connect, or `gh` fails before auth. Do not change GitHub credentials; record whether it is host-local, VPN/Tailscale/proxy-related, or a broader outage.

**`git-https-transport`** — the suppressed `gh api user` check works but the helper's `--probe` reports unavailable. The helper disables inherited Git trace settings and discards all transport stdout/stderr. Continue into helper and Keychain classification before asking the user to re-auth. This deliberately reports less detail: if the layer remains unclear, report it as unresolved rather than collecting raw credential-bearing traces.

**`credential-helper-config`** — run the helper with `--scope global` and `--scope system` to compare with its default effective configuration. It reports exact known helper names, empty resets, or opaque custom-helper categories, including URL-scoped helpers. A custom category is not evidence of a broken helper. Never print its definition or configuration origin; route authorized portable changes through yadm/dotfiles setup, keeping macOS-only config in Darwin platform files.

**`keychain-access`** — `gh` expects Keychain-backed auth but Keychain is locked, inaccessible, or missing the entry. Presence check only (`security find-internet-password -s github.com >/dev/null 2>&1`); never dump Keychain item contents. Ask the user to unlock or repair local macOS auth, or approve a specific fix.

**`local-user-lookup`** — errors mention user lookup, `getpwuid`, home directory, permissions, or missing `$HOME`; or automation runs as a different user than the interactive shell (`id`, `whoami`, `dscl . -read "/Users/$(whoami)" NFSHomeDirectory`). Fix host-local runner/user configuration, not GitHub auth. Keep user-specific paths out of tracked guidance.

## Report shape

```text
GitHub/Git preflight:
Host:
Repo/path:
Failing command:
Layer:
Evidence:
Safe fallback:
Repair target:
Secrets exposed: no
```

## Routing

PR review/CI workflows return to `gh-pr-address-feedback`, `gh-fix-ci`, or `babysit-pr` after the preflight passes. Dotfiles credential-helper or bootstrap fixes belong in `dotfiles-manager` and setup scripts; 1Password item/env/SSH-agent setup in the 1Password developer baseline; connector visibility questions in `connector-readiness-triage`.
