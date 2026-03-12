# Dotfiles

Personal dotfiles managed with [yadm](https://yadm.io).

## 🚀 Setup

### New Machine

```bash
# Install yadm
brew install yadm  # macOS
sudo apt install yadm  # Ubuntu/Debian

# Clone and bootstrap
yadm clone https://github.com/pevd950/dotfiles.git
yadm bootstrap
```

### Sync Existing Machine

```bash
yadm pull
yadm bootstrap  # Re-run to apply any new setup changes
```

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
- Homebrew installation (if needed) and `brew bundle --global`
- Development tools via Brewfile plus Node version setup with nodenv
- iTerm2 shell integration

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
# Test bootstrap after changes
yadm bootstrap

# Force regenerate alternates
yadm alt --force
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
