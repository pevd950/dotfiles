# Dotfiles

Personal dotfiles managed with [yadm](https://yadm.io).

## New computer

Install prerequisites for your OS:

```sh
# macOS (Homebrew required)
brew install yadm python shellcheck

# Debian/Ubuntu
sudo apt install yadm zsh git curl python3-venv shellcheck stow fzf fd-find bat direnv
```

Preserve any existing files that conflict with the clone.

Bootstrap installs dependencies and configures runtimes, skill links, and
macOS 1Password/Git/SSH integration. Review it before running.

```sh
yadm clone --no-bootstrap https://github.com/pevd950/dotfiles.git
yadm config local.class personal  # or work
yadm bootstrap
```

On Linux, replace the last command with
`DOTFILES_INSTALL_LINUX_SHELL_TOOLS=1 yadm bootstrap` to install shell tools.

## Update

Commit or stash tracked local changes before pulling.

```sh
yadm status
yadm pull --ff-only
yadm alt
```

Run `yadm bootstrap` only when you need setup changes applied.

## Windows

From a separate Git checkout of this repo, preview and apply:

```powershell
.\scripts\setup-windows.ps1
.\scripts\setup-windows.ps1 -Apply
```

This copies global Codex guidance and its four referenced skills: Craft, task
management, cross-host context, and babysit-pr. It installs no packages. Existing
different files (including empty files), linked paths, and custom `CODEX_HOME`
need manual review; nothing is overwritten. Move reviewed conflicts aside, then
rerun. Pull and rerun to update; start a fresh Codex chat to load the guidance.

## WSL (optional)

Review the distro and package list before installing:

```powershell
wsl --install --distribution Ubuntu-24.04 --no-launch
```

Launch Ubuntu to create the Linux user. If Windows requests a reboot, save work
first. Inside Ubuntu:

```sh
sudo apt-get update
apt-get --simulate install --no-install-recommends git yadm ca-certificates
# After reviewing dependencies:
sudo apt-get install --no-install-recommends git yadm ca-certificates
yadm clone --no-bootstrap -w "$HOME/.local/share/dotfiles-source" https://github.com/pevd950/dotfiles.git
```

Use an account without an existing YADM repository. This keeps dotfiles in an
isolated source work tree; do not run the full bootstrap for this minimal setup.
Native Windows Codex uses the Windows profile configured above, not the WSL home.
