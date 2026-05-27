# CLI Model Selection Notes

Checked 2026-05-26.

## Claude Code

Claude Code model choice is configuration and account dependent.

- `claude --model <alias|name>` sets the model for the current session.
- `ANTHROPIC_MODEL=<alias|name>` also sets the model for the launched session.
- The `model` setting in Claude Code settings sets the initial model for new sessions.
- `opus` means the latest available Opus-class model. Anthropic's current docs say it resolves to Opus 4.7 on Anthropic API and Claude Platform on AWS, with provider-specific differences for Bedrock, Vertex, and Foundry.
- `default` depends on account type. Current docs list Max and Team Premium as Opus 4.7, Pro/Team Standard/Enterprise/API as Sonnet 4.6, and Bedrock/Vertex/Foundry as Sonnet 4.5, with automatic fallback possible when limits are hit.
- Opus 4.7 requires Claude Code v2.1.111 or newer.

Practical review command:

```bash
review_timeout() {
  if command -v timeout >/dev/null 2>&1; then timeout "$@";
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "$@";
  else echo "No timeout/gtimeout available; ask before running without a runtime cap." >&2; return 124;
  fi
}

review_timeout 10m claude --model opus -p --permission-mode dontAsk --max-budget-usd 1.00 --output-format text --tools "" --no-session-persistence '<review prompt>'
```

Pin only when supported:

```bash
review_timeout 10m claude --model claude-opus-4-7 -p --permission-mode dontAsk --max-budget-usd 1.00 --output-format text --tools "" --no-session-persistence '<review prompt>'
```

## Google Antigravity and Gemini CLI

Google is transitioning consumer Gemini CLI usage to Antigravity CLI. On 2026-05-26, local `agy --version` returned `1.0.2`, authenticated through keyring, and selected `Gemini 3.5 Flash (Medium)` by default during smoke testing.

Antigravity is agentic. For review-panel use, run it from an empty temp directory with `--sandbox` and pass all context in the prompt:

```bash
review_dir="$(mktemp -d "${TMPDIR:-/tmp}/agy-review.XXXXXX")"
(cd "$review_dir" && review_timeout 2m agy --sandbox --print '<review prompt>' --print-timeout 90s)
```

Important: `agy --print` expects the prompt immediately after `--print`. Put `--print-timeout` after the prompt, or the CLI may treat `--print-timeout` itself as the task.

Legacy Gemini CLI model choice is configuration, access, and release-channel dependent.

- `gemini --model <alias-or-name>` or `gemini -m <alias-or-name>` sets the model for that run.
- Current docs list `auto` as the default alias.
- `auto` resolves to Gemini 2.5 Pro or Gemini 3 Pro Preview depending on preview features.
- `pro` is the complex-reasoning alias and uses the preview model when enabled.
- Gemini 3.1 Pro Preview is rolling out. Current docs say to check `/model` > Manual for `gemini-3.1-pro-preview`; if available, it can be launched with `-m gemini-3.1-pro-preview`.

Practical review command:

```bash
review_timeout 10m env GEMINI_CLI_TRUST_WORKSPACE=true gemini --skip-trust --model pro --prompt '<review prompt>' --approval-mode plan --output-format text
```

Pin only when available:

```bash
review_timeout 10m env GEMINI_CLI_TRUST_WORKSPACE=true gemini --skip-trust --model gemini-3.1-pro-preview --prompt '<review prompt>' --approval-mode plan --output-format text
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
review_timeout 2m copilot -p '<review prompt>' --mode plan --no-custom-instructions --disable-builtin-mcps --available-tools='' --silent --stream off
```

GitHub CLI wrapper:

```bash
review_timeout 2m gh copilot -- -p '<review prompt>' --mode plan --no-custom-instructions --disable-builtin-mcps --available-tools='' --silent --stream off
```

## Local Checks Before Use

Run these before depending on either CLI:

```bash
command -v claude
claude --version
claude --help | rg -- '--model|--max-budget-usd|--permission-mode|--tools|--no-session-persistence'
command -v gemini
gemini --version
gemini --help | rg -- '--model|--prompt|--approval-mode|--output-format'
command -v agy
agy --version
agy --help | rg -- '--print|--print-timeout|--sandbox'
command -v copilot
copilot --version
copilot help | rg -- '--model|--prompt|--mode|--available-tools|--disable-builtin-mcps|--no-custom-instructions'
```

## Sources

- Claude Code model configuration: https://code.claude.com/docs/en/model-config
- Claude Code settings and CLI configuration: https://code.claude.com/docs/en/settings
- Google Antigravity CLI transition: https://developers.googleblog.com/en/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Google Antigravity CLI docs: https://www.antigravity.google/docs/cli-getting-started
- Gemini CLI reference: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/cli-reference.md
- Gemini 3 on Gemini CLI: https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/gemini-3.md
- GitHub Copilot CLI install docs: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/install-copilot-cli
