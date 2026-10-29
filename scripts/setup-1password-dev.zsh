#!/usr/bin/env zsh
# 1Password client bootstrap for a developer host. Idempotent: every write goes through
# commit_file, which only replaces a file whose content would change. Pass --dry-run (or set
# ONEPASSWORD_SETUP_DRY_RUN=1) to print what would change without touching the filesystem.
#
# What it ensures, per OS (macOS and Linux; Windows only gets the documented paths and commands):
#   - the `op` CLI is installed (Homebrew / 1Password apt or rpm repository / winget hint);
#   - ~/.config/1Password/ssh/agent.toml offers the SSH keys of one vault (default `Servers`);
#   - ~/.ssh/config gets a final-pass fallback to the per-OS 1Password agent socket for local
#     (non-inbound) sessions, after user-provided agent choices;
#   - macOS extras: op plugins.sh, the Codex 1Password MCP entry, gh git_protocol=ssh.
set -euo pipefail

truthy() {
  [[ "${1:-}" == "1" || "${1:-}" == "true" || "${1:-}" == "yes" ]]
}

DRY_RUN=0
truthy "${ONEPASSWORD_SETUP_DRY_RUN:-0}" && DRY_RUN=1
# Decided here, at top level: inside a command substitution stdout is never a terminal.
INTERACTIVE=0
[[ -t 0 && -t 1 ]] && INTERACTIVE=1
for arg in "$@"; do
  case "$arg" in
    --dry-run|-n) DRY_RUN=1 ;;
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      print -u2 -r -- "unknown argument: $arg (use --dry-run)"
      exit 2
      ;;
  esac
done

status() {
  printf "%-36s %s\n" "$1" "$2"
}

display_path() {
  local path="$1"
  if [[ -n "$path" ]]; then
    print -r -- "${path//$HOME/~}"
  else
    print -r -- "missing"
  fi
}

# Host OS: macos, linux, windows (MSYS/Git Bash/Cygwin), or other.
host_os() {
  case "$(uname -s 2>/dev/null)" in
    Darwin) print -r -- macos ;;
    Linux) print -r -- linux ;;
    MINGW*|MSYS*|CYGWIN*|Windows_NT) print -r -- windows ;;
    *) print -r -- other ;;
  esac
}
OS="$(host_os)"

on_macos() {
  [[ "$OS" == "macos" ]]
}

# Agent socket as ssh expects it (tilde kept for the config file) and as a filesystem path.
onepassword_agent_socket_config() {
  case "$OS" in
    macos) print -r -- '~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock' ;;
    linux) print -r -- '~/.1password/agent.sock' ;;
    *) print -r -- '' ;;
  esac
}

onepassword_agent_socket_path() {
  local config_path
  config_path="$(onepassword_agent_socket_config)"
  [[ -z "$config_path" ]] || print -r -- "$HOME/${config_path#"~/"}"
}

# The desktop app is what runs the SSH agent; its presence (not the socket, which only exists after
# sign-in) decides whether ssh config should point at the 1Password agent. Only install artefacts
# count: the ~/.1password data directory outlives an uninstall and would leave IdentityAgent pointing
# at a socket that never comes back.
onepassword_app_installed() {
  case "$OS" in
    macos) [[ -d /Applications/1Password.app ]] ;;
    linux)
      command -v 1password >/dev/null 2>&1 \
        || [[ -x /opt/1Password/1password ]] \
        || [[ -f /usr/share/applications/1password.desktop ]] \
        || [[ -f "$HOME/.local/share/applications/1password.desktop" ]] \
        || [[ -d /var/lib/flatpak/app/com.onepassword.OnePassword ]] \
        || [[ -d "$HOME/.local/share/flatpak/app/com.onepassword.OnePassword" ]]
      ;;
    *) return 1 ;;
  esac
}

# agent.toml location per 1Password docs. On Windows the script only writes it when run from a
# POSIX shell that exposes LOCALAPPDATA and cygpath; otherwise it prints the path.
agent_toml_path() {
  case "$OS" in
    macos|linux) print -r -- "$HOME/.config/1Password/ssh/agent.toml" ;;
    windows)
      if [[ -n "${LOCALAPPDATA:-}" ]] && command -v cygpath >/dev/null 2>&1; then
        print -r -- "$(cygpath -u "$LOCALAPPDATA")/1Password/config/ssh/agent.toml"
      fi
      ;;
  esac
}

# commit_file <candidate> <target> <label> [backup]
# Replaces <target> with <candidate> only when the content differs; removes <candidate> either way.
# With backup=1 the first rewrite copies the previous file to <target>.bak (never overwritten).
# Returns 0 when the target changed (or would change in dry-run), 1 when it was already current.
commit_file() {
  local candidate="$1" target="$2" label="$3" backup="${4:-0}"

  if [[ -e "$target" ]] && cmp -s "$candidate" "$target"; then
    rm -f "$candidate"
    return 1
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -e "$target" ]]; then
      status "$label" "would rewrite $(display_path "$target")"
      diff -u "$target" "$candidate" 2>/dev/null | sed 's/^/    /' | sed "s#$HOME#~#g" || true
    else
      status "$label" "would create $(display_path "$target")"
    fi
    rm -f "$candidate"
    return 0
  fi

  mkdir -p "$(dirname "$target")"
  if [[ "$backup" -eq 1 && -e "$target" && ! -e "$target.bak" ]]; then
    cp -p "$target" "$target.bak"
    status "$label" "backed up to $(display_path "$target.bak")"
  fi
  mv "$candidate" "$target"
  chmod 600 "$target"
  return 0
}

remove_file() {
  local target="$1" label="$2"
  [[ -e "$target" ]] || return 1
  if [[ "$DRY_RUN" -eq 1 ]]; then
    status "$label" "would remove $(display_path "$target")"
  else
    rm -f "$target"
  fi
  return 0
}

ssh_config_file() {
  local ssh_config="$HOME/.ssh/config"

  if [[ -L "$ssh_config" && -e "$ssh_config" ]]; then
    print -r -- "${ssh_config:A}"
  else
    print -r -- "$ssh_config"
  fi
}

# ---------------------------------------------------------------------------------------------
# op CLI
# ---------------------------------------------------------------------------------------------

# Runs a command as root: directly when already root, otherwise through non-interactive sudo so an
# unattended run fails cleanly instead of hanging on a password prompt.
as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo -n "$@"
  fi
}

install_op_linux_apt() {
  local arch keyring="/usr/share/keyrings/1password-archive-keyring.gpg"
  local policy_dir="/etc/debsig/policies/AC2D62742012EA22" debsig_dir="/usr/share/debsig/keyrings/AC2D62742012EA22"
  arch="$(dpkg --print-architecture)"
  # 1Password's documented Debian/Ubuntu steps: signing key, apt source, debsig policy, install.
  curl -sS https://downloads.1password.com/linux/keys/1password.asc | as_root gpg --dearmor --yes --output "$keyring"
  printf 'deb [arch=%s signed-by=%s] https://downloads.1password.com/linux/debian/%s stable main\n' "$arch" "$keyring" "$arch" \
    | as_root tee /etc/apt/sources.list.d/1password.list >/dev/null
  as_root mkdir -p "$policy_dir" "$debsig_dir"
  curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | as_root tee "$policy_dir/1password.pol" >/dev/null
  curl -sS https://downloads.1password.com/linux/keys/1password.asc | as_root gpg --dearmor --yes --output "$debsig_dir/debsig.gpg"
  as_root apt-get update -qq
  as_root env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq 1password-cli
}

install_op_linux_rpm() {
  local manager="$1"
  # 1Password's documented RPM steps: import the key, add the stable repository, install.
  as_root rpm --import https://downloads.1password.com/linux/keys/1password.asc
  printf '[1password]\nname=1Password Stable Channel\nbaseurl=https://downloads.1password.com/linux/rpm/stable/$basearch\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey="https://downloads.1password.com/linux/keys/1password.asc"\n' \
    | as_root tee /etc/yum.repos.d/1password.repo >/dev/null
  as_root "$manager" install -y 1password-cli
}

ensure_op_cli() {
  if command -v op >/dev/null 2>&1; then
    status "op" "$(display_path "$(command -v op)") ($(op --version 2>/dev/null || printf unknown))"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    status "op" "missing; would install"
    return 0
  fi

  case "$OS" in
    macos)
      if ! command -v brew >/dev/null 2>&1; then
        status "op" "missing; Homebrew not found, install from https://developer.1password.com/docs/cli/get-started/"
        return 0
      fi
      brew install --cask 1password-cli
      ;;
    linux)
      if ! command -v curl >/dev/null 2>&1; then
        status "op" "missing; curl is required to add the 1Password repository"
        return 0
      fi
      if [[ "$(id -u)" -ne 0 ]] && ! sudo -n true 2>/dev/null; then
        status "op" "missing; needs sudo without a password prompt (run: sudo -v; then rerun)"
        return 0
      fi
      if command -v apt-get >/dev/null 2>&1; then
        install_op_linux_apt
      elif command -v dnf >/dev/null 2>&1; then
        install_op_linux_rpm dnf
      elif command -v yum >/dev/null 2>&1; then
        install_op_linux_rpm yum
      else
        status "op" "missing; no apt/dnf/yum, see https://developer.1password.com/docs/cli/get-started/"
        return 0
      fi
      ;;
    windows)
      status "op" "missing; run: winget install 1password-cli"
      return 0
      ;;
    *)
      status "op" "missing; unsupported OS, see https://developer.1password.com/docs/cli/get-started/"
      return 0
      ;;
  esac

  if command -v op >/dev/null 2>&1; then
    status "op" "installed $(op --version 2>/dev/null || printf unknown)"
  else
    status "op" "install ran but op is not on PATH; open a new shell and rerun"
  fi
}

# ---------------------------------------------------------------------------------------------
# agent.toml
# ---------------------------------------------------------------------------------------------

# Resolves the vault's ID through op so an older entry that named the same vault by ID is recognised
# as the managed entry instead of being kept as a duplicate. Only in an interactive terminal: the
# desktop-app integration may raise an unlock prompt, which must not stall an unattended bootstrap.
# Prints nothing when op is missing, not signed in, or the run is unattended; the ID is only compared.
managed_vault_id() {
  local vault_name="$1"
  command -v op >/dev/null 2>&1 || return 0
  [[ "$INTERACTIVE" -eq 1 ]] || return 0
  op vault get "$vault_name" --format json 2>/dev/null </dev/null \
    | sed -nE 's/.*"id":[[:space:]]*"([^"]+)".*/\1/p' | head -n1 || true
}

# Writes agent.toml with ONE vault-level [[ssh-keys]] entry so the 1Password SSH agent offers every
# SSH Key item in that vault. Item IDs change when items move between vaults, which left the old
# per-item list pointing at nothing (found 2026-10-27); a vault entry never goes stale and needs no
# op session to write. Existing [[ssh-keys]] entries that are not item-specific (other vaults, or
# account-scoped entries) are kept after the managed entry; entries with an `item` key are dropped.
# Per-host key selection stays in ssh config (1Password SSH bookmarks or IdentityFile + IdentitiesOnly).
ensure_agent_toml() {
  local agent_config vault_name="${ONEPASSWORD_SSH_KEY_VAULT:-Servers}" vault_id candidate

  agent_config="$(agent_toml_path)"
  if [[ -z "$agent_config" ]]; then
    status "agent.toml" 'skipped; on Windows write %LOCALAPPDATA%\1Password\config\ssh\agent.toml by hand'
    return 0
  fi

  vault_id="$(managed_vault_id "$vault_name")"

  candidate="$(mktemp)"
  {
    printf "# Generated by dotfiles scripts/setup-1password-dev.zsh; rerun it instead of editing.\n"
    printf "# One vault-level entry: every SSH Key item in the '%s' vault is offered by the 1Password SSH agent.\n" "$vault_name"
    printf "# Item IDs are not listed on purpose; they change when items move between vaults.\n"
    printf "# Pick keys per host with 1Password SSH bookmarks or IdentityFile + IdentitiesOnly in ~/.ssh/config.d.\n"
    printf "\n[[ssh-keys]]\nvault = \"%s\"\n" "$vault_name"
    if [[ -f "$agent_config" ]]; then
      # Keep every other [[ssh-keys]] block that has no `item` key and does not name the managed vault.
      awk -v managed_name="$vault_name" -v managed_id="$vault_id" '
        function flush() {
          if (in_block && !has_item && !is_managed && lines != "") {
            if (!announced) { print ""; print "# Entries kept from the previous agent.toml (not item-specific):"; announced = 1 }
            print ""; print "[[ssh-keys]]"; printf "%s", lines
          }
          in_block = 0; has_item = 0; is_managed = 0; lines = ""
        }
        # A header or key line may carry a trailing TOML comment: `[[ssh-keys]] # work`, `vault = "X" # y`.
        /^[[:space:]]*\[\[ssh-keys\]\][[:space:]]*(#.*)?$/ { flush(); in_block = 1; next }
        /^[[:space:]]*\[/ { flush(); next }
        in_block {
          line = $0
          sub(/^[[:space:]]+/, "", line)
          if (line == "" || line ~ /^#/) next
          key = line; sub(/[[:space:]]*=.*$/, "", key)
          value = line; sub(/^[^=]*=[[:space:]]*/, "", value)
          if (value ~ /^"/) { sub(/^"/, "", value); sub(/"[[:space:]]*(#.*)?$/, "", value) } else { sub(/[[:space:]]*#.*$/, "", value) }
          if (key == "item") has_item = 1
          if (key == "vault" && (value == managed_name || (managed_id != "" && value == managed_id))) is_managed = 1
          lines = lines line "\n"
        }
        END { flush() }
      ' "$agent_config"
    fi
  } > "$candidate"

  if commit_file "$candidate" "$agent_config" "agent.toml" 1; then
    [[ "$DRY_RUN" -eq 1 ]] || status "agent.toml" "wrote vault-level entry for '$vault_name'"
  else
    status "agent.toml" "current; vault-level entry for '$vault_name'"
  fi
}

# ---------------------------------------------------------------------------------------------
# ssh config
# ---------------------------------------------------------------------------------------------

# Retire only our old fragment. Leaving Include directives intact preserves quoted, wildcard,
# and multi-file user includes; OpenSSH ignores a missing included file. Never remove unmarked
# IdentityAgent directives: even the old socket path can be an intentional per-host choice.
retire_ssh_agent_fragment() {
  local include_file="$1"
  if [[ -f "$include_file" ]] && grep -q '^# Generated by dotfiles scripts/setup-1password-dev\.zsh\.$' "$include_file"; then
    remove_file "$include_file" "ssh agent legacy fragment" || true
  fi
}

ensure_ssh_config_identity_agent() {
  local ssh_dir="$HOME/.ssh"
  local ssh_config include_file="$ssh_dir/config.d/1password-agent.conf"
  local agent_path agent_socket tmp_file installed=0

  agent_path="$(onepassword_agent_socket_config)"
  agent_socket="$(onepassword_agent_socket_path)"
  ssh_config="$(ssh_config_file)"

  if [[ -z "$agent_path" ]]; then
    status "ssh config agent" 'skipped; on Windows the 1Password agent uses the OpenSSH named pipe (no IdentityAgent needed)'
    return 0
  fi

  onepassword_app_installed && installed=1
  if [[ "$installed" -eq 1 ]]; then
    if [[ -S "$agent_socket" ]]; then
      status "1Password agent socket" "present"
    else
      status "1Password agent socket" "missing; sign in to the 1Password app and enable Settings > Developer > SSH agent"
    fi
    if [[ "$DRY_RUN" -eq 0 ]]; then
      mkdir -p "$ssh_dir"
      chmod 700 "$ssh_dir"
    fi
  fi

  tmp_file="$(mktemp)"
  if [[ -e "$ssh_config" ]]; then
    awk '
      /^# >>> dotfiles 1Password SSH agent$/ { skip=1; next }
      /^# <<< dotfiles 1Password SSH agent$/ { skip=0; restore_scope=1; next }
      # The old block ended in Match all. Preserve that context if the user
      # appended directives after it, without accumulating headers on reruns.
      !skip && restore_scope && /^[[:space:]]*[^#[:space:]]/ {
        print "Match all"
        restore_scope=0
      }
      !skip { print }
    ' "$ssh_config" > "$tmp_file"
  fi
  if [[ "$installed" -eq 1 ]]; then
    {
      printf '%s\n' '# >>> dotfiles 1Password SSH agent'
      printf '%s\n' '# Fallback only: earlier Host, Include, and Match final agent choices take precedence.'
      printf '%s\n' '# Keep this block at the end of the file; inbound sessions retain their own agent.'
      printf '%s\n' 'Match final exec "test x${SSH_CONNECTION}${SSH_CLIENT} = x"'
      printf '  IdentityAgent "%s"\n' "$agent_path"
      printf '%s\n' 'Match all'
      printf '%s\n' '# <<< dotfiles 1Password SSH agent'
    } >> "$tmp_file"
  fi

  if [[ -e "$ssh_config" || "$installed" -eq 1 ]]; then
    if commit_file "$tmp_file" "$ssh_config" "ssh config agent"; then
      [[ "$DRY_RUN" -eq 1 ]] || status "ssh config agent" "updated managed fallback"
    else
      status "ssh config agent" "current"
    fi
  else
    rm -f "$tmp_file"
    status "ssh config agent" "skipped; 1Password app not installed"
  fi
  # The old early fragment must disappear even when a user wildcard also includes it.
  retire_ssh_agent_fragment "$include_file"
}

# ---------------------------------------------------------------------------------------------
# macOS extras: op plugins, Codex MCP, gh over SSH
# ---------------------------------------------------------------------------------------------

ensure_op_plugins_file() {
  local plugin_file="$HOME/.config/op/plugins.sh"

  if [[ -e "$plugin_file" ]]; then
    status "op plugins.sh" "present"
    return 0
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    status "op plugins.sh" "would create without global aliases"
    return 0
  fi
  mkdir -p "$(dirname "$plugin_file")"
  printf "export OP_PLUGIN_ALIASES_SOURCED=1\n" > "$plugin_file"
  status "op plugins.sh" "created without global aliases"
}

ensure_codex_mcp() {
  local mcp_bin="/Applications/1Password.app/Contents/MacOS/onepassword-mcp"

  if ! command -v codex >/dev/null 2>&1; then
    status "codex mcp:1password" "skipped; codex missing"
    return 0
  fi

  if [[ ! -x "$mcp_bin" ]]; then
    status "codex mcp:1password" "skipped; onepassword-mcp missing"
    return 0
  fi

  if codex mcp list 2>/dev/null | awk 'BEGIN{found=0} /^1password[[:space:]]/ {found=1} END{exit found ? 0 : 1}'; then
    status "codex mcp:1password" "configured"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    status "codex mcp:1password" "would add"
    return 0
  fi

  if codex mcp add 1password -- "$mcp_bin"; then
    status "codex mcp:1password" "added"
  else
    status "codex mcp:1password" "failed to add"
  fi
}

ssh_agent_has_keys() {
  local agent_socket="$1"
  local key_count

  [[ -n "$agent_socket" && -S "$agent_socket" ]] || return 1
  SSH_AUTH_SOCK="$agent_socket" ssh-add -l >/dev/null 2>&1 || return 1
  key_count="$(SSH_AUTH_SOCK="$agent_socket" ssh-add -l 2>/dev/null | wc -l | tr -d ' ')"
  [[ "${key_count:-0}" -gt 0 ]]
}

github_ssh_auth_ready() {
  local configured_agent=""
  local ssh_config

  ssh_config="$(ssh_config_file)"

  if command -v ssh >/dev/null 2>&1 && [[ -f "$ssh_config" ]]; then
    configured_agent="$(ssh -F "$ssh_config" -G github.com 2>/dev/null | awk 'tolower($1) == "identityagent" { $1=""; sub(/^[[:space:]]+/, ""); print; exit }' || true)"
  fi

  case "$configured_agent" in
    "")
      ssh_agent_has_keys "${SSH_AUTH_SOCK:-}"
      ;;
    "none")
      return 1
      ;;
    "SSH_AUTH_SOCK")
      ssh_agent_has_keys "${SSH_AUTH_SOCK:-}"
      ;;
    "~/"*)
      ssh_agent_has_keys "$HOME/${configured_agent#"~/"}"
      ;;
    *)
      ssh_agent_has_keys "$configured_agent"
      ;;
  esac
}

github_ssh_login_ready() {
  local ssh_config
  local output
  local rc

  ssh_config="$(ssh_config_file)"
  [[ -f "$ssh_config" ]] || return 1

  set +e
  output="$(ssh -F "$ssh_config" -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o ConnectTimeout=5 -T git@github.com 2>&1)"
  rc=$?
  set -e

  [[ "$rc" -eq 1 && "$output" == *"successfully authenticated"* ]]
}

ensure_gh_ssh_protocol() {
  if ! command -v gh >/dev/null 2>&1; then
    status "gh git_protocol" "skipped; gh missing"
    return 0
  fi

  if ! github_ssh_auth_ready || ! github_ssh_login_ready; then
    status "gh git_protocol" "skipped; SSH auth unavailable"
    return 0
  fi

  if [[ "$(gh config get git_protocol -h github.com 2>/dev/null || true)" == "ssh" ]]; then
    status "gh git_protocol" "ssh"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    status "gh git_protocol" "would set to ssh"
    return 0
  fi

  if gh config set git_protocol ssh -h github.com >/dev/null 2>&1; then
    status "gh git_protocol" "set to ssh"
  else
    status "gh git_protocol" "failed to set"
  fi
}

main() {
  [[ "$DRY_RUN" -eq 1 ]] && status "mode" "dry run; nothing is written"
  status "os" "$OS"

  case "$OS" in
    macos|linux) ;;
    windows)
      # Windows is documented, not automated: agent.toml lives under %LOCALAPPDATA% and the agent is a
      # named pipe that Windows OpenSSH picks up without IdentityAgent.
      ensure_op_cli
      ensure_agent_toml
      ensure_ssh_config_identity_agent
      return 0
      ;;
    *)
      status "1Password dev setup" "skipped; unsupported OS"
      return 0
      ;;
  esac

  if on_macos; then
    status "1Password.app" "$([[ -d /Applications/1Password.app ]] && printf present || printf missing)"
    status "onepassword-mcp" "$([[ -x /Applications/1Password.app/Contents/MacOS/onepassword-mcp ]] && printf present || printf missing)"
  else
    status "1Password app" "$(onepassword_app_installed && printf present || printf missing)"
  fi

  ensure_op_cli
  ensure_agent_toml
  ensure_ssh_config_identity_agent
  if on_macos; then
    ensure_op_plugins_file
    ensure_codex_mcp
    ensure_gh_ssh_protocol
    status "read-only preflight" "~/.config/zsh/custom/bin/onepassword-dev-preflight"
  fi
}

main "$@"
