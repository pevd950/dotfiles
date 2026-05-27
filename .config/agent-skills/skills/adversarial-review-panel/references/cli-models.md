# CLI Model Selection Notes

Checked 2026-05-26.

## Shared Command Setup

Store substantial review prompts in a temporary file and pass the file contents as a quoted argument. Do not paste untrusted file excerpts directly into a shell command.

```bash
review_timeout() {
  if command -v timeout >/dev/null 2>&1; then timeout "$@";
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "$@";
  else echo "No timeout/gtimeout available; ask before running without a runtime cap." >&2; return 124;
  fi
}

review_prompt_file="/path/to/sanitized-review-prompt.txt"
review_prompt="$(cat "$review_prompt_file")"
```

## Claude Code

Claude Code model choice is configuration and account dependent.

Information current as of May 2026.

- `claude --model <alias|name>` sets the model for the current session.
- `ANTHROPIC_MODEL=<alias|name>` also sets the model for the launched session.
- The `model` setting in Claude Code settings sets the initial model for new sessions.
- `opus` means the latest available Opus-class model. Anthropic's current docs say it resolves to Opus 4.7 on Anthropic API and Claude Platform on AWS, with provider-specific differences for Bedrock, Vertex, and Foundry.
- `default` depends on account type. Current docs list Max and Team Premium as Opus 4.7, Pro/Team Standard/Enterprise/API as Sonnet 4.6, and Bedrock/Vertex/Foundry as Sonnet 4.5, with automatic fallback possible when limits are hit.
- Opus 4.7 requires Claude Code v2.1.111 or newer.

Practical review command:

```bash
review_timeout 10m claude --model opus -p --max-budget-usd 1.00 --output-format text --tools "" --no-session-persistence "$review_prompt"
```

Pin only when supported:

```bash
review_timeout 10m claude --model claude-opus-4-7 -p --max-budget-usd 1.00 --output-format text --tools "" --no-session-persistence "$review_prompt"
```

Do not use `--permission-mode dontAsk` for review-panel defaults. `--tools ""` removes built-in tools from the invocation, but it is not a complete MCP isolation guarantee in every Claude Code setup; if local MCP/tool startup cannot be ruled out or isolated, skip Claude or use a verified clean Claude configuration.

## Google Antigravity and Gemini CLI

Google is transitioning consumer Gemini CLI usage to Antigravity CLI. On 2026-05-26, local `agy --version` returned `1.0.2`, authenticated through keyring, and selected `Gemini 3.5 Flash (Medium)` by default during smoke testing.

Antigravity is agentic and can auto-discover user plugins, MCP servers, and hooks. For review-panel use, run it only with sanitized public context, from an empty temp directory, with `--sandbox`, and only after verifying plugins/MCP/hooks are disabled or clean for the review. If clean isolation cannot be verified, skip Antigravity.

```bash
review_dir="$(mktemp -d "${TMPDIR:-/tmp}/agy-review.XXXXXX")"
(cd "$review_dir" && review_timeout 2m agy --sandbox --print "$review_prompt" --print-timeout 90s)
```

Important: `agy --print` expects the prompt immediately after `--print`. Put `--print-timeout` after the prompt, or the CLI may treat `--print-timeout` itself as the task.

Legacy Gemini CLI model choice is configuration, access, and release-channel dependent.

- `gemini --model <alias-or-name>` or `gemini -m <alias-or-name>` sets the model for that run.
- Current docs list `auto` as the default alias.
- `auto` resolves to Gemini 2.5 Pro or Gemini 3 Pro Preview depending on preview features.
- `pro` is the complex-reasoning alias and uses the preview model when enabled.
- Gemini 3.1 Pro Preview is rolling out. Current docs say to check `/model` > Manual for `gemini-3.1-pro-preview`; if available, it can be launched with `-m gemini-3.1-pro-preview`.

Use legacy Gemini only when it can run outside the trusted target repo with sanitized prompt context and tool isolation. Do not use a trusted-workspace headless command as the default review-panel path.

Practical isolated shape:

```bash
review_dir="$(mktemp -d "${TMPDIR:-/tmp}/gemini-review.XXXXXX")"
(cd "$review_dir" && review_timeout 10m gemini --model pro --prompt "$review_prompt" --approval-mode plan --output-format text)
```

Pin only when available:

```bash
(cd "$review_dir" && review_timeout 10m gemini --model gemini-3.1-pro-preview --prompt "$review_prompt" --approval-mode plan --output-format text)
```

If neither `timeout` nor `gtimeout` is available, ask before running without a runtime cap.

## GitHub Copilot CLI

GitHub Copilot CLI model choice is account and policy dependent.

- `copilot --model <model>` selects a model when available.
- `copilot -p <prompt>` runs noninteractively.
- Use `--available-tools=''`, `--disable-builtin-mcps`, and `--no-custom-instructions` for text-only review-panel prompts.
- `gh copilot -- ...` runs the same installed CLI through GitHub CLI.

Practical review command:

```bash
review_timeout 2m copilot -p "$review_prompt" --mode plan --no-custom-instructions --disable-builtin-mcps --available-tools='' --silent --stream off
```

GitHub CLI wrapper:

```bash
review_timeout 2m gh copilot -- -p "$review_prompt" --mode plan --no-custom-instructions --disable-builtin-mcps --available-tools='' --silent --stream off
```

## Local Checks Before Use

Run these before depending on either CLI:

```bash
command -v claude
claude --version
command -v gemini
gemini --version
command -v agy
agy --version
command -v copilot
copilot --version
```

Prefer low-risk smoke tests over `--help` greps for capability checks because CLI help output may omit supported flags. Record failures as reviewer coverage gaps instead of guessing.

## Sources

- Claude Code model configuration: https://code.claude.com/docs/en/model-config
- Claude Code settings and CLI configuration: https://code.claude.com/docs/en/settings
- Google Antigravity CLI transition: https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Google Antigravity CLI docs: https://www.antigravity.google/docs/cli-getting-started
- Gemini CLI reference: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/cli-reference.md
- Gemini 3 on Gemini CLI: https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/gemini-3.md
- GitHub Copilot CLI install docs: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli
