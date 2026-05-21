# Dotfiles

Personal dotfiles managed with [yadm](https://yadm.io).

## 🚀 Setup

### New Machine

This path is for normal interactive machines where applying dotfiles immediately
is acceptable.

```bash
# Install yadm
brew install yadm  # macOS
sudo apt install yadm  # Ubuntu/Debian

# Clone and bootstrap
yadm clone https://github.com/pevd950/dotfiles.git
yadm bootstrap
```

Operational infrastructure hosts should not start with `yadm clone` and
`yadm bootstrap`; use the staged Debian/Linux infrastructure path below instead.

### Debian/Linux Infrastructure Hosts

Operational Linux hosts should start with review and validation, not immediate
dotfile application. Debian hosts use `apt` packages; Homebrew-on-Linux is not a
dependency for this repo.

Minimal rollout prerequisites are `zsh` and `yadm`. The broader runtime package
set below matches the shell features this repo enables on Debian. Full local
validation also needs `shellcheck`.

Recommended staged path:

```bash
# 1. Review in a normal clone first. Do not use yadm yet.
mkdir -p ~/Developer
git clone https://github.com/pevd950/dotfiles.git ~/Developer/dotfiles
cd ~/Developer/dotfiles

# Run validation now only if shellcheck and zsh are already available.
if command -v shellcheck >/dev/null 2>&1 && command -v zsh >/dev/null 2>&1; then
  ./scripts/check.sh
fi

# 2. Later, install runtime/adoption prerequisites with apt after review.
sudo apt-get update
sudo apt-get install -y zsh yadm stow fzf fd-find bat direnv

# Optional: install validation tooling before running the full local check.
sudo apt-get install -y shellcheck
./scripts/check.sh

# 3. Back up existing shell and git config before yadm owns anything.
mkdir -p ~/.dotfiles-backup
cp -a ~/.bashrc ~/.profile ~/.gitconfig ~/.dotfiles-backup/ 2>/dev/null || true

# 4. Clone with yadm only after conflicts are reviewed.
yadm clone --no-bootstrap https://github.com/pevd950/dotfiles.git
yadm status
yadm alt

# 5. Test zsh before making it the login shell.
zsh -lic 'echo zsh startup ok'
```

Keep bash as the login shell until zsh startup is proven safe in interactive and
remote sessions. Only consider `chsh` after confirming a rollback path.

Do not run `yadm bootstrap` on infrastructure hosts until Linux support and
host-specific conflicts have been reviewed. Bootstrap may create directories,
install shell tooling when explicitly opted in, and link shared agent skills.

### Sync Existing Machine

```bash
yadm pull
yadm bootstrap  # Re-run to apply any new setup changes
```

## Development Workflow

Use a normal clone for non-trivial edits, then apply reviewed changes back to
the live yadm checkout after merge. This keeps `$HOME` closer to a deployed
worktree instead of the place where every experiment happens.

```bash
mkdir -p ~/Developer
git clone https://github.com/pevd950/dotfiles.git ~/Developer/dotfiles
cd ~/Developer/dotfiles
git switch -c topic/my-change

# edit, validate, commit, push, and open a PR
./scripts/check.sh
gh pr create --fill
```

After the PR merges:

```bash
cd ~
yadm pull --ff-only
yadm alt
yadm bootstrap
```

For tiny emergency fixes, yadm can still be used directly in `$HOME`, but prefer
branches and PRs for bootstrap, shell startup, agent-skills, and package changes.

## 📁 Structure

```
.
├── .config/
│   ├── Code/User/prompts/      # VS Code prompts source (XDG path)
│   ├── yadm/bootstrap          # Main bootstrap script
│   └── starship.toml           # Starship prompt config
├── .zshrc                      # Zsh configuration
├── .zshrc_custom/              # Custom shell functions/aliases
├── .Brewfile##template         # Base Homebrew packages
├── .Brewfile##os.Darwin,...    # Machine-specific Brewfiles
└── setup.sh                    # Shared environment bootstrap
```

## 🔧 Machine-Specific Configuration

### Set Machine Class
```bash
yadm config local.class personal  # or 'work'
yadm alt  # Regenerate alternates
```

### Alternates Pattern
- `.Brewfile##template` - Generated from template
- `.Brewfile##os.Darwin,hostname.kakarot` - Specific machine
- `.Brewfile##class.work` - Work machines
- `.gitconfig.local##class.personal` - Personal git config

### VS Code Prompts
Stored in `.config/Code/User/prompts/`. If an app still expects the macOS Application Support path, create the symlink manually.

## 🔀 GitHub Codespaces

This repo auto-configures Codespaces. GitHub runs `setup.sh` automatically (not the full yadm bootstrap).

## 📝 Scripts

### `setup.sh`
Shared environment bootstrap used by yadm bootstrap and Codespaces:
- Oh My Zsh + plugins
- Starship prompt
- macOS: Homebrew installation (if needed) and `brew bundle --global`
- Debian/Linux: prints apt package guidance by default and only installs apt
  packages when `DOTFILES_INSTALL_LINUX_PACKAGES=1` is set
- Debian/Linux: skips network shell installers by default; set
  `DOTFILES_INSTALL_LINUX_SHELL_TOOLS=1` only after reviewing host impact
- macOS development tools via Brewfile plus Node version setup with nodenv

### `.config/yadm/bootstrap`
Full yadm bootstrap:
1. Runs `yadm alt` for machine-specific configs
2. Creates required local directories
3. Calls `setup.sh` for remaining setup
4. Symlinks shared agent skills into Codex, Claude, and Copilot

Both scripts are designed to be safe to re-run.

### Shared AI Skills
- Canonical skill source lives in `.config/agent-skills/skills/`.
- Bootstrap symlinks each shared skill folder into `CODEX_HOME/skills` (defaulting to `.codex/skills/`), `.claude/skills/`, and `.copilot/skills/`.
- Skills that depend on machine-local secrets should read them from env vars at runtime rather than storing them in tracked files.
- Example: `poke-notify` uses `POKE_API_KEY`.

## 🧪 Testing

```bash
# Fast local validation for shell/bootstrap changes
./scripts/check.sh

# Force regenerate alternates
yadm alt --force

# Apply bootstrap changes to the current machine only after review/merge
yadm bootstrap
```

## 🆘 Common Issues

**VS Code prompts missing**: Create the symlink manually if a macOS app expects the Application Support path:
```bash
ln -snf ~/.config/Code/User/prompts ~/Library/Application\ Support/Code/User/prompts
```

**Wrong Brewfile**: Check hostname matches:
```bash
hostname -s  # Should match Brewfile##os.Darwin,hostname.XXX
```

**Brewfile not generating**: Remove existing and regenerate:
```bash
rm ~/.Brewfile && yadm alt
```
