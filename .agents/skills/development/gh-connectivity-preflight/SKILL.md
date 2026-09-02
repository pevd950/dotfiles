---
name: gh-connectivity-preflight
description: "Classify GitHub CLI and Git transport/auth failures before PR, CI, issue, or dotfiles work. Use when gh, Git HTTPS, DNS, local user lookup, credential helpers, Keychain, or token environment overrides may be the real blocker."
---

# GitHub Connectivity Preflight

Identify the failing layer without exposing credentials or mutating auth state.

## Safety rules

- Do not print token values, Keychain entries, credential-helper output, cookies, or 1Password secret values.
- Do not run `gh auth login`, delete credentials, change credential helpers, or modify Keychain unless the user explicitly approves that repair.
- Prefer read-only probes. If a probe could write, push, delete, revoke, or rotate credentials, stop and ask.
- Redact account identifiers in shared notes unless they are already-public repo/user names needed for routing.
- Treat `GH_TOKEN` and `GITHUB_TOKEN` as high-precedence overrides: an invalid env token breaks `gh` even when Keychain auth is healthy.

## Fast path

Run in the failing checkout; on the first failure, stop broad probing and classify below:

```bash
gh --version | sed -n 1p
gh auth status -h github.com
gh repo view --json nameWithOwner -q .nameWithOwner
git remote -v
git config --show-origin --get-all credential.helper
git ls-remote --heads origin >/dev/null
```

## Layers

**`gh-cli-missing` / `gh-cli-broken`** — `command not found: gh` or `gh --version` fails before auth checks. Use the GitHub connector for read-only metadata; route local repair to host bootstrap/dotfiles. Do not install packages unasked.

**`env-token-override`** — `gh auth status` reports an env token, or API calls fail with 401/403/bad-credentials while the vars are set. Probe presence without printing values (`test -n "${GH_TOKEN:-}" && echo GH_TOKEN=set`); confirm with `env -u GH_TOKEN -u GITHUB_TOKEN gh auth status -h github.com`. Fix: ask before editing shell files; move stale automation-only exports into ignored host-local config or 1Password references — never copy raw token values into tracked docs.

**`gh-auth-or-scope`** — network works but `gh api user --jq .login` fails, or auth status reports not logged in, expired, or missing scopes. Ask the user to re-auth or approve a repair path; use the GitHub connector for read-only PR/issue metadata meanwhile.

**`dns-network`** — DNS lookup fails (`dscacheutil -q host -a name github.com` or `nslookup github.com`), `curl -I --max-time 10 https://github.com` cannot connect, or `gh` fails before auth with network/TLS/proxy errors. Do not change GitHub credentials; record whether it is host-local, VPN/Tailscale/proxy-related, or a broader outage.

**`git-https-transport`** — `gh api user` works but `git ls-remote --heads origin` fails with authentication, could-not-read-username, credential-helper, or HTTP 401/403 errors. Trace with `GIT_TRACE=1 GIT_CURL_VERBOSE=1 git ls-remote --heads origin 2> /tmp/git-https-trace.log`, then redact before sharing anywhere: `sed -E 's/(Authorization: ).*/\1<redacted>/; s/(password=)[^& ]+/\1<redacted>/g' /tmp/git-https-trace.log | tail -80`. Continue into the helper and Keychain layers before asking the user to re-auth.

**`credential-helper-config`** — `git config --show-origin --get-all credential.helper` (also `--global` and `--system`) shows no helper where `gh auth git-credential` or Keychain is expected, a helper pointing at a missing host-specific path, or conflicting/leaked platform-specific helpers. Route portable changes through yadm/dotfiles setup; keep macOS-only helper config in Darwin platform files with Linux/headless behavior explicit.

**`keychain-access`** — `gh` expects Keychain-backed auth but Keychain is locked, inaccessible, or missing the entry. Presence check only (`security find-internet-password -s github.com >/dev/null`); never dump Keychain item contents. Ask the user to unlock or repair local macOS auth, or approve a specific fix.

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
