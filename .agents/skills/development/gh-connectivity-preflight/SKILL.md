---
name: gh-connectivity-preflight
description: "Classify GitHub CLI and Git transport/auth failures before PR, CI, issue, or dotfiles work. Use when gh, Git HTTPS, DNS, local user lookup, credential helpers, Keychain, or token environment overrides may be the real blocker."
---

# GitHub Connectivity Preflight

Use this before a `gh`-heavy workflow or a GitHub HTTPS push/pull fails in a confusing way. The goal is to identify the failing layer without exposing credentials or mutating auth state.

## Safety Rules

- Do not print token values, Keychain entries, credential-helper output, cookies, or 1Password secret values.
- Do not run `gh auth login`, delete credentials, change credential helpers, or modify Keychain unless the user explicitly approves that repair.
- Redact account identifiers in shared notes unless they are already public repo/user names needed for routing.
- Prefer read-only probes. If a probe could write, push, delete, revoke, or rotate credentials, stop and ask.
- Treat `GH_TOKEN` and `GITHUB_TOKEN` as high-precedence overrides. An invalid env token can break `gh` even when Keychain auth is healthy.

## Fast Path

Run these in the repo or dotfiles checkout that failed:

```bash
printf 'host=%s\n' "${AGENT_HOST_ALIAS:-$(hostname -s 2>/dev/null || hostname)}"
command -v gh || true
gh --version | sed -n '1p' || true
gh auth status -h github.com
gh repo view --json nameWithOwner -q .nameWithOwner
git remote -v
git config --show-origin --get-all credential.helper
git ls-remote --heads origin >/dev/null
```

If any command fails, stop broad probing and classify the layer below.

## Layer Classification

### `gh` CLI Missing Or Broken

Signals:
- `command not found: gh`
- `gh --version` fails before auth checks.

Classify as: `gh-cli-missing` or `gh-cli-broken`.

Next action:
- Use the GitHub connector for read-only metadata if available.
- For local repair, route to host bootstrap/dotfiles setup. Do not install packages unless the user asked.

### Environment Token Override

Probe without printing values:

```bash
test -n "${GH_TOKEN:-}" && printf 'GH_TOKEN=set\n' || printf 'GH_TOKEN=unset\n'
test -n "${GITHUB_TOKEN:-}" && printf 'GITHUB_TOKEN=set\n' || printf 'GITHUB_TOKEN=unset\n'
env | awk -F= '/^(GH_TOKEN|GITHUB_TOKEN)=/{print $1"=<redacted>"}'
```

Signals:
- `gh auth status` reports an env token.
- API calls fail with `bad credentials`, `401`, `403`, or missing scopes while env token variables are set.
- Unsetting the env token in a subshell makes `gh auth status` or `gh api user` work.

Safe confirmation:

```bash
env -u GH_TOKEN -u GITHUB_TOKEN gh auth status -h github.com
```

Classify as: `env-token-override`.

Next action:
- Ask before editing shell files.
- Prefer moving stale automation-only exports into ignored host-local config or 1Password references; never copy raw token values into tracked docs.

### GitHub API Auth Or Scope

Probes:

```bash
gh auth status -h github.com
gh api user --jq .login
gh auth status -h github.com 2>&1 | sed -E 's/(token: ).*/\1<redacted>/'
```

Signals:
- `gh` is installed and network works, but `gh api user` fails.
- `gh auth status` says not logged in, token expired, or missing scopes.

Classify as: `gh-auth-or-scope`.

Next action:
- Ask the user to re-auth or approve a repair path.
- For read-only PR/issue metadata, use the GitHub connector if available and healthy.

### DNS Or Network

Probes:

```bash
getent hosts github.com 2>/dev/null || dscacheutil -q host -a name github.com 2>/dev/null || nslookup github.com
curl -I --max-time 10 https://github.com
gh api rate_limit
```

Signals:
- DNS lookup fails.
- `curl` cannot connect to GitHub.
- `gh` fails before auth with network, TLS, proxy, or DNS errors.

Classify as: `dns-network`.

Next action:
- Do not change GitHub credentials.
- Record whether the failure is host-local, VPN/Tailscale/proxy-related, or a broader outage.

### Git HTTPS Transport

Probes:

```bash
git remote -v
git ls-remote --heads origin
GIT_TRACE=1 GIT_CURL_VERBOSE=1 git ls-remote --heads origin 2> /tmp/git-https-trace.log
sed -E 's/(Authorization: ).*/\1<redacted>/; s/(password=)[^& ]+/\1<redacted>/g' /tmp/git-https-trace.log | tail -80
```

Signals:
- `gh api user` works, but `git ls-remote` fails.
- Git reports authentication failed, could not read username, credential helper failure, or HTTP 401/403.

Classify as: `git-https-transport`.

Next action:
- Continue to credential helper and Keychain layers before asking the user to re-auth.
- Do not paste raw trace logs into Craft or PRs; redact first.

### Credential Helper

Probes:

```bash
git config --show-origin --get-all credential.helper
git config --global --get-all credential.helper
git config --system --get-all credential.helper 2>/dev/null || true
```

Signals:
- No helper is configured on a host that expects `gh auth git-credential` or Keychain.
- Helper points to a host-specific path that does not exist.
- Multiple helpers conflict or a platform-specific helper leaked into a shared file.

Classify as: `credential-helper-config`.

Next action:
- Route portable changes through yadm/dotfiles setup.
- Put macOS-only helper config in Darwin platform files; keep Linux/headless behavior explicit.

### macOS Keychain

Probes:

```bash
security list-keychains 2>/dev/null | sed -n '1,8p'
security find-internet-password -s github.com 2>/dev/null >/dev/null && printf 'github-keychain-entry=present\n' || printf 'github-keychain-entry=missing-or-inaccessible\n'
gh auth status -h github.com
```

Signals:
- `gh` expects Keychain-backed auth but Keychain is locked, inaccessible, or missing the entry.
- `security` returns interaction or permission errors in a non-interactive session.

Classify as: `keychain-access`.

Next action:
- Do not dump Keychain item contents.
- Ask the user to unlock/repair local macOS auth or approve a specific repair.

### Local User Lookup

Probes:

```bash
id
whoami
dscl . -read "/Users/$(whoami)" NFSHomeDirectory 2>/dev/null || getent passwd "$(whoami)" 2>/dev/null || true
printf 'HOME=%s\n' "$HOME"
```

Signals:
- Git/gh errors mention user lookup, home directory, `getpwuid`, permissions, or missing `$HOME`.
- Host automation runs under a different user than the interactive shell.

Classify as: `local-user-lookup`.

Next action:
- Fix host-local runner/user configuration, not GitHub auth.
- Keep user-specific paths out of public/tracked guidance unless they are generic examples.

## Report Shape

Use this compact summary in chat, Craft issue notes, or automation memory:

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

- PR review/CI workflows should return to `gh-pr-address-feedback`, `gh-fix-ci`, or `pr-babysitter` after this preflight passes.
- Dotfiles credential helper or bootstrap fixes belong in `dotfiles-manager` and setup scripts.
- 1Password item/env/SSH-agent setup belongs in 1Password developer baseline guidance, not this skill.
- Connector visibility questions belong in `connector-readiness-triage`.
