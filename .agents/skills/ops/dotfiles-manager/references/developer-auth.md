# Developer authentication

## 1Password developer baseline

For 1Password, GitHub auth, SSH agent, or developer-token routing work, start with the non-mutating preflight, and use it to classify the host, not to collect secrets:

```bash
~/.zshrc_custom/bin/onepassword-dev-preflight
```

It answers: whether `op`, 1Password.app, `onepassword-mcp`, and the Codex `1password` MCP entry are available; whether `op account list`, `op plugin list`, `gh auth status`, and `gh api user` run without printing their output; whether `GH_TOKEN`/`GITHUB_TOKEN` env overrides are masking the baseline; whether `SSH_AUTH_SOCK`, `ssh-add`, 1Password `agent.toml`, GitHub `IdentityAgent`, and SSH auth to GitHub are usable; and which variable names quiet local env files export, without values.

Run the mutating `scripts/setup-1password-dev.zsh` only after the baseline shows the intended gap or the user asked for repair. Keep tracked guidance to command names, variable names, and non-secret mechanics; never commit private 1Password item paths, vault IDs, token values, host-local Craft links, or generated secret files. For remote hosts, verify inheritance by pulling the yadm commit there and re-running the preflight — do not assume local 1Password app, SSH socket, or CLI auth state exists remotely.
