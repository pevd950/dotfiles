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

Copies Codex guidance, Craft, task management, cross-host context, and the linked
GitHub media reference. No packages installed. Different existing files, linked
paths, and custom `CODEX_HOME` require manual review. Move reviewed conflicts
aside and rerun; start a fresh Codex chat to load the guidance.

## WSL (optional source checkout)

After reviewing the distro, run in **PowerShell as Administrator**:

```powershell
wsl --install --distribution Ubuntu-24.04 --no-launch
```

Launch Ubuntu to create a user. Inside Ubuntu, review packages before installing:

```sh
sudo apt-get update
apt-get --simulate install --no-install-recommends git yadm ca-certificates
sudo apt-get install --no-install-recommends git yadm ca-certificates
mkdir -p "$HOME/.local/share/dotfiles-source"
yadm clone --no-bootstrap -w "$HOME/.local/share/dotfiles-source" https://github.com/pevd950/dotfiles.git
```

Use an account without an existing YADM repository. This only checks out source;
Windows Codex uses the Windows setup above. Do not run the full bootstrap here.
