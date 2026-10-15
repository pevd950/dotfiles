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

## Windows and WSL: minimal agent setup

Use the separate [Windows/WSL agent setup](docs/windows-agents.md). It previews
changes by default, installs no packages, and deploys only shared Codex guidance
and four selected skills. It does not run the Mac/Linux bootstrap or configure
shells, runtimes, credentials, or applications.
