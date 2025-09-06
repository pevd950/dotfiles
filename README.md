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
│   ├── Code/User/prompts/      # VS Code prompts (XDG path)
│   ├── yadm/bootstrap          # Main bootstrap script
│   └── starship.toml           # Starship prompt config
├── .zshrc                      # Zsh configuration
├── .zshrc_custom/              # Custom shell functions/aliases
├── .Brewfile##template         # Base Homebrew packages
├── .Brewfile##os.Darwin,...    # Machine-specific Brewfiles
└── setup.sh                    # Lightweight setup (Codespaces-compatible)
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
Stored in `.config/Code/User/prompts/` and automatically symlinked to macOS Application Support path via bootstrap.

## 🔀 GitHub Codespaces

This repo auto-configures Codespaces. GitHub runs `setup.sh` automatically (not the full yadm bootstrap).

## 📝 Scripts

### `setup.sh`
Lightweight setup for shells/tools (Codespaces-compatible):
- Oh My Zsh + plugins
- Starship prompt
- Development tools (nodenv, pyenv, rbenv)
- Homebrew packages

### `.config/yadm/bootstrap`
Full yadm bootstrap:
1. Runs `yadm alt` for machine-specific configs
2. Creates VS Code prompts symlink (macOS)
3. Calls `setup.sh` for remaining setup

Both scripts are idempotent.

## 🧪 Testing

```bash
# Test bootstrap after changes
yadm bootstrap

# Force regenerate alternates
yadm alt --force
```

## 🆘 Common Issues

**VS Code prompts missing**: Bootstrap creates the symlink automatically. Manual fix:
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