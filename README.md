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

```text
.
├── .config/
│   ├── git/                    # Git settings and identity/platform alternates
│   ├── zsh/                    # Shell configuration, custom modules and wrappers
│   ├── vscode/                 # Portable dotfiles workspace
│   ├── yadm/alt/               # Brewfile template and macOS login alternate
│   └── yadm/bootstrap          # Main bootstrap script
├── .vim/vimrc                  # Native Vim configuration path
├── .gitconfig                  # Git entry point
├── .zshenv                     # Noninteractive Zsh entry point
├── .zshrc                      # Interactive Zsh entry point
├── AGENTS.md                   # Repository guidance
├── README.md
└── setup.sh                    # Codespaces and shared bootstrap entry point
```

## Updating an existing home

After pulling this layout for the first time, use the existing shell to run:

```sh
yadm pull --ff-only
python3 "$HOME/scripts/migrate-zsh-layout.py"       # Preview local additions
python3 "$HOME/scripts/migrate-zsh-layout.py" --apply
yadm alt
exec zsh -l
```

Resolve any tracked local changes before pulling. The migration moves untracked
plugins, completions, private overrides, and custom executables into
`~/.config/zsh/custom/` without reading their contents or overwriting collisions. Relative symlink
targets are adjusted when needed to keep pointing to the same location.
It keeps `~/.zshrc_custom` as a compatibility link for existing application paths.
If both directories contain the same path, it stops before making changes so you
can compare and resolve that path privately. Running it again is safe. Before
migration, interactive Zsh continues to use the old directory for local plugins
and overrides and the new directory for the shared configuration.

The root `.zshenv` and `.zshrc` loaders retain Zsh's normal startup order;
`ZDOTDIR` is unchanged and `~/.zshenv.local` stays at its existing private path.
Yadm creates `~/.Brewfile` and `~/.zprofile` from `.config/yadm/alt/`, so Homebrew
and login shells keep using their normal entry points. Vim reads `~/.vim/vimrc`
directly, including older versions that lack XDG configuration support.

Open the workspace at `~/.config/vscode/dotfiles.code-workspace`; its relative
folder path works in both a deployed home and a developer checkout. `setup.sh`
stays at the root for Codespaces discovery. This migration does not require
bootstrap, package installation, credential changes, or moving other repositories.

## 🔧 Machine-Specific Configuration

### Set Machine Class
```bash
yadm config local.class personal  # or 'work'
yadm alt  # Regenerate alternates
```

### Alternates Pattern
- `.config/yadm/alt/.Brewfile##template` - Generated from template
- `.config/yadm/alt/.Brewfile##os.Darwin,hostname.example` - Specific machine
- `.config/yadm/alt/.Brewfile##class.work` - Work machines
- `.config/git/local.conf##class.personal` - Personal Git config

### Git Configuration

Keep Git settings together in `.config/git/`:

```text
.gitconfig                         # Small entry point, includes settings.conf
.config/git/
├── settings.conf                  # Shared settings and includes
├── local.conf##class.personal     # Personal identity
├── local.conf##class.work         # Work identity
├── platform.conf##os.Darwin       # macOS settings
└── platform.conf##os.Linux        # Linux settings
```

`yadm alt` creates `local.conf` and `platform.conf` beside their alternates.
Includes resolve relative to the file containing them, so the layout works
without machine-specific absolute paths. The entry point keeps working even
when `XDG_CONFIG_HOME` is customized. `settings.conf` has a distinct name to
avoid loading it twice alongside Git's automatic `.config/git/config` lookup;
an existing XDG Git config is left in place.

Host-local authentication settings may live in the ignored
`~/.config/git/auth.conf`. Existing `~/.gitconfig.auth` files remain included
for compatibility, followed by `auth.conf`; there is no automatic move or
credential change. The original order of identity, platform, authentication,
and shared settings is preserved.

After this reorganization is merged, use `yadm pull --ff-only` and `yadm alt`
to install it. Bootstrap is not needed for this change. Old root-level
`.gitconfig.local` and `.gitconfig.platform` symlinks may remain after the
old alternate sources disappear; they are no longer read and can be removed
after verifying the new links. Preserve regular files at those paths for
review rather than deleting them.

### VS Code Prompts
Stored in `.config/Code/User/prompts/`. If an app still expects the macOS Application Support path, create the symlink manually.

### Host-Local Environment Files

Keep host-local values out of tracked dotfiles. Use the narrowest local file
that matches how the value is consumed:

- `~/.zshenv.local`: stable agent and automation runtime configuration that
  must be visible to non-interactive zsh commands. Keep it quiet and fast:
  `export` statements only, no command substitutions, no output, no network
  calls. Examples: `AGENT_HOST_ALIAS`, `AGENT_SHARED_CONTEXT_URL`,
  `CRAFT_AGENT_OPS_FRICTION_LOG_BLOCK_ID`,
  `CRAFT_PLATO_FRICTION_LOG_BLOCK_ID`, `AI_INBOX_DIR`, and local model paths.
- `~/.config/zsh/custom/exports-local.zsh`: interactive shell exports, dynamic
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

Use `AGENT_SHARED_CONTEXT_URL` for the provider-neutral cross-host context root.
Existing hosts may keep `CRAFT_SHARED_MEMORY_URL` as a compatibility alias while
they migrate; when both are set, they must identify the same root.

The configured root must contain a compact `Routing Directory`, or an equivalent
host table such as the existing `Host Snapshot`, with one entry per host. Each
entry records its canonical `AGENT_HOST_ALIAS` and any accepted local hostname
aliases. Agents resolve the root first, then require the trimmed current alias or
hostname to match exactly one entry case-insensitively before reading subject
context or writing; missing or ambiguous matches fail closed for shared context.

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

### Unattended GitHub authentication

Before native IDE or CI setup in an existing HTTPS GitHub checkout, run:

```sh
python3 scripts/setup-github-git-auth.py --repository /path/to/checkout
python3 scripts/setup-github-git-auth.py --repository /path/to/checkout --apply
```

The first command checks the stored GitHub CLI identity, exercises the selected
credential helper even for public origins, and reads the origin with prompts
disabled, without interactive shell token exports. Empty repositories are valid.
`--apply` verifies the proposed helper and origin before changing existing local
helper values, then installs a
bounded credential adapter under `~/.local/libexec/dotfiles/` and pins that checkout's
GitHub HTTPS helper to its immutable, content-addressed version. A failed later
setup can leave an unused cached version, but cannot replace a helper used by
another checkout. Keep older versions while any checkout still references them.
Repeat the check with `--git /path/to/Xcode.app/Contents/Developer/usr/bin/git`
when preparing Xcode Cloud. The setup is idempotent and leaves other hosts and
global Git configuration intact. Apply is limited to standalone checkouts without
linked siblings: both linked worktrees and primary checkouts with siblings are
rejected because their local Git config is shared. Check-only mode can inspect
either kind of checkout. Existing proxy and custom CA settings are preserved.
The two helper values are installed atomically and the previous configuration is
restored if verification fails or is interrupted. Setup uses a host Python interpreter outside active
virtual environments. It discovers `gh` only through stable host locations, not
an activated development environment's `PATH`. For another installation, pass
`--gh /absolute/persistent/path/to/gh` and keep that executable path available.
Check-only mode honors path-scoped origin helpers; apply
rejects path-scoped or wildcard GitHub helpers before making changes and checks
included and worktree settings before reporting success.

The adapter uses the existing `gh` identity, times out credential lookup after
15 seconds, and stops Git from falling back to another helper or a password dialog
when authentication is unavailable. Tokens are never copied to files or diagnostic
output. This uses Git's documented [helper reset and quit behavior](https://git-scm.com/docs/gitcredentials)
and the existing [GitHub CLI credential integration](https://cli.github.com/manual/gh_auth_setup-git).

Provision the GitHub CLI identity once through the approved host authentication
setup. A locked or revoked credential, a new host/account, or Apple's interactive
account verification still needs recovery; this command reports failure instead
of trying to sign in. Xcode may use its own account flow outside Git.

To undo this checkout's override, remove only `credential.https://github.com.helper`
from its local Git config. That restores inherited helpers. If the checkout had a
custom local helper before setup, restore its previous values instead.

### Shared AI Skills
- Canonical skill source lives in `.config/agent-skills/skills/`.
- Bootstrap symlinks each shared skill folder into `CODEX_HOME/skills` (defaulting to `.codex/skills/`), `.claude/skills/`, and `.copilot/skills/`.
- Skills that depend on machine-local secrets should read them from env vars at runtime rather than storing them in tracked files.
- Notify the user: load `$notify-user` (`.agents/skills/productivity/notify-user/`). Do not call ActionBuddy, Poke, or Buddy MCP for routine handoffs.
- Example secret: the default-enabled Poke provider under `$notify-user` requires `POKE_API_KEY` (missing key soft-skips).

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

## Validation

Bootstrap installs checker dependencies into the ignored `.venv-checks` environment.
For a developer clone or an existing installation, run:

```sh
bash scripts/setup-checks.sh
./scripts/check.sh
```

Python 3.9+ with venv support, ShellCheck, and Zsh are required (Debian/Ubuntu:
`python3-venv shellcheck zsh`). Dependency installation is explicit; validation
itself does not install packages. `DOTFILES_CHECK_PYTHON` can select an existing
interpreter containing the dependencies in `scripts/requirements-checks.txt`.
