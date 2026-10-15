# Minimal Windows and WSL agent setup

These are separate, opt-in entry points. Existing macOS/Linux `setup.sh` and
`.config/yadm/bootstrap` behavior is unchanged. Neither new installer runs the
existing bootstrap, installs packages, launches skill helpers, or configures
credentials, SSH, applications, shells, Docker, GPU tooling, or runtimes.

## Review installation first

For a new WSL host, review this list before running installation commands:

| Component | Purpose | Required now? |
|---|---|---|
| Microsoft WSL2 platform/kernel | Run Linux alongside Windows | For WSL only |
| Ubuntu 24.04 LTS distribution | Linux userspace; includes its standard base packages | For this WSL path |
| `git` | Repository fetch/pull | Yes inside WSL |
| `yadm` | Manage the isolated dotfiles source work tree | Yes for YADM workflow |
| `ca-certificates` | HTTPS certificate verification | Yes; often already installed |
| Zsh, Oh My Zsh, Starship, shell plugins | Shell customization | No |
| stow, fzf, fd-find, bat, direnv | Optional shell utilities | No |
| Python, Node, Docker, CUDA toolkit | Workload/helper runtimes | No |
| shellcheck, Python test dependencies | Repository development/CI only | Not installed on the host |

Ubuntu and apt can install required dependencies in addition to named packages.
Preview apt transactions before accepting them. Do not use a broad upgrade as
part of this setup. Native Windows deployment uses existing PowerShell and Git;
it requires no WSL or additional packages.

After reviewing the platform/distro installation, use an administrator terminal:

```powershell
wsl --install --distribution Ubuntu-24.04 --no-launch
```

If Windows requests a restart, save work and arrange it explicitly. Do not force
a reboot as part of a bootstrap. Launch Ubuntu after installation to complete
its first-run Linux user setup; enter passwords only into the trusted local UI.
Verify the distribution is WSL2 with `wsl --list --verbose`.

Inside Ubuntu, review the apt transaction before installation:

```sh
sudo apt-get update
apt-get --simulate install --no-install-recommends git yadm ca-certificates
# Only after reviewing the simulation:
sudo apt-get install --no-install-recommends git yadm ca-certificates
```

## What is deployed

The shared `.codex/AGENTS.md` and the complete supporting trees for the four
skills listed in `scripts/agent-skills.txt`:

- Craft: knowledge-base operations and formatting.
- Task management: source-system ownership and task placement.
- Cross-host context: host selection and private-routing protocol (no private
  routing data is supplied by the public repo).
- Babysit PR: owns the GitHub media reference linked from global instructions.

The other personal skills are not deployed. No provider compatibility links,
private skills, `.codex/config.toml`, tokens, memories, plugins, or sessions are
copied. Global guidance alone does not make a platform-specific helper usable:
review each helper's prerequisites before invoking it. Existing MCP connectors
remain the preferred transport when available.

## Native Windows Codex

Clone this repository to a dedicated source directory, not the Windows home
itself. From that checkout, preview with PowerShell:

```powershell
.\scripts\setup-windows.ps1
# After reviewing the listed files:
.\scripts\setup-windows.ps1 -Apply
# Only for reviewed existing-file conflicts:
.\scripts\setup-windows.ps1 -Apply -BackupConflicts
```

Windows deployment copies real files, avoiding administrator symlink privileges.
Rerun after pulling source updates; it skips identical files and preserves
unrelated files. Conflicting files require explicit backed-up replacement.
Backups and the local hash manifest live under
`~/.local/state/dotfiles-agents/`; keep these local, never commit them.

The default destinations are `~/.codex/AGENTS.md` and
`~/.agents/skills/<category>/<name>`. `CODEX_HOME` is respected for native profile
deployment, but its directory must be directly inside the user home because
the shared instructions contain sibling-relative skill references. An explicit
`-TargetHome` uses an isolated profile and ignores ambient `CODEX_HOME` unless
`-CodexHome` is also supplied. Linked target ancestors and nonempty
`AGENTS.override.md` are rejected for manual review.

## WSL with YADM

Windows and WSL have separate user homes and Codex processes. Configuring one
does not configure the other. Do not aim a Linux-home clone at the Windows home.

Use an **isolated source work tree** instead of deploying every tracked dotfile
into the new Linux home. On a WSL account without an existing YADM repository:

```sh
yadm clone --no-bootstrap -w "$HOME/.local/share/dotfiles-source" https://github.com/pevd950/dotfiles.git
bash "$HOME/.local/share/dotfiles-source/scripts/setup-wsl-agents.sh"
# Review the preview, then:
bash "$HOME/.local/share/dotfiles-source/scripts/setup-wsl-agents.sh" --apply
```

If YADM is already configured, inspect `yadm status` and its work tree first;
reuse the correct source or a separate ordinary Git checkout rather than forcing
a clone over an existing YADM repository. Do not run `yadm bootstrap` for this
minimal profile. The new script does not depend on or alter YADM alternates.

WSL deployment copies `AGENTS.md` and links only selected skill directories into
the canonical `.agents/skills` tree. Retain the source checkout: those links
follow source updates. Back up reviewed conflicts with `--backup-conflicts`.
Unrelated content is never deleted. Inspect local source changes before a
fast-forward-only `yadm pull`; rerun the installer after updates. Windows copies
must be updated separately. Neither installer removes stale files automatically.

## Verify and recover

Start a fresh Codex chat in the intended Windows/WSL environment and verify it
loads global guidance and discovers the four selected skills. Confirm Craft
folder selection and readback using an existing connector. No API key or private
endpoint belongs in this repo.

Disposable-home checks (no test package installation required):

```powershell
pwsh -NoProfile -File scripts/test-setup-windows.ps1
```

```sh
bash scripts/test-setup-wsl-agents.sh
```

For rollback, inspect the local backup folder and restore only the exact files
replaced by this deployment. Remove only the newly deployed paths you have
verified; never remove the whole `.codex` or `.agents` directory. Windows retains
a manifest of deployed file paths/hashes; WSL records its source checkout path.

References: [WSL installation](https://learn.microsoft.com/en-us/windows/wsl/install),
[YADM clone](https://yadm.io/docs/getting_started),
[Codex guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Codex skills](https://learn.chatgpt.com/docs/build-skills).
