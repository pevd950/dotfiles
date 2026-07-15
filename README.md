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

### Linux

Linux hosts use their system package manager; Homebrew is only used on macOS.

```bash
sudo apt install yadm zsh
yadm clone --no-bootstrap https://github.com/pevd950/dotfiles.git
```

Review conflicts and bootstrap behavior on the target host before running
`yadm bootstrap` or changing the login shell.

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

### Host-Local Environment Files

Keep host-local values out of tracked dotfiles. Use the narrowest local file
that matches how the value is consumed:

- `~/.zshenv.local`: stable agent and automation runtime configuration that
  must be visible to non-interactive zsh commands. Keep it quiet and fast:
  `export` statements only, no command substitutions, no output, no network
  calls. Examples: `AGENT_HOST_ALIAS`, `CRAFT_SHARED_MEMORY_URL`,
  `CRAFT_AGENT_OPS_FRICTION_LOG_BLOCK_ID`,
  `CRAFT_PLATO_FRICTION_LOG_BLOCK_ID`, `AI_INBOX_DIR`, and local model paths.
- `~/.zshrc_custom/exports-local.zsh`: interactive shell exports, dynamic
  command-based exports, and tool credentials for human terminal sessions. It
  may use commands such as `gh auth token`, but Codex or cron-style
  non-interactive shells should not depend on it being sourced by default.
  Agent tools that need one of these credentials should load it deliberately for
  that action and avoid printing values.

Private object IDs, private Craft links, tokens, and host-specific paths belong
in one of these ignored local files, not in tracked skills or docs. Prefer
`.zshenv.local` for non-secret routing/path values that agents need frequently;
keep API tokens and dynamic auth in `exports-local.zsh` unless a scheduled
automation has a narrower, explicitly documented secrets-loading path. When a
value needs to be set on multiple hosts, include the env var names and
verification command in each live delegation prompt rather than committing the
private values. After verification, record only any durable routing convention
in shared Craft context; do not use Craft as a setup queue.

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
