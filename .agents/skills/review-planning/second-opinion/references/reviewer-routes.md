# Reviewer routes

Tested 2026-11-12 on macOS with claude 2.1.322, codex-cli 0.163.0 and copilot 0.0.421; all three worked read-only in a repository and text only. Flags change between releases: run a smoke test (`'Reply with exactly: OK'`) before a real review and record what actually ran.

## Shared setup

```bash
review_prompt_file="/path/to/brief.txt"
review_prompt="$(cat "$review_prompt_file")"
REPO="/path/to/checkout"
```

`timeout` is GNU coreutils (`gtimeout` on some Macs). Run without a time limit only after asking.

## Claude

```bash
(cd "$REPO" && timeout 15m claude --model opus -p --max-budget-usd 2.00 --output-format text \
  --no-session-persistence --strict-mcp-config --settings '{"disableAllHooks":true}' \
  --tools "Read,Grep,Glob,Bash" \
  --allowedTools "Read" "Grep" "Glob" "Bash(gh issue list:*)" "Bash(gh issue view:*)" \
    "Bash(gh pr view:*)" "Bash(gh pr diff:*)" "Bash(git log:*)" "Bash(git show:*)" \
  -- "$review_prompt")
```

- Anything outside the allowed list is refused, so the reviewer cannot write or post. Text only: replace the two tool lines with `--tools ""` and run from an empty directory.
- `--settings '{"disableAllHooks":true}'` is required. With the user's hooks on, a hook that waits (the agent bus's does) holds a headless run open until the timeout, with no output.
- `--strict-mcp-config` starts no MCP servers, so GitHub is read through `gh`.
- Screenshots and other files are read with the `Read` tool: name their paths in the prompt.
- `opus` follows the account's newest Opus model. Pin a full model name when the review must be repeatable.
- "OAuth session expired" means the CLI needs `claude auth login`, which is the user's step.

## Codex

```bash
(cd "$REPO" && timeout 15m codex exec --sandbox read-only --ephemeral "$review_prompt")
```

- The sandbox blocks writes; reads, `gh` and `git` work. Text only: add `-C "$(mktemp -d)" --skip-git-repo-check`.
- Add images after the prompt: `"$review_prompt" -i round1-light.png round1-dark.png`. `-i` takes several files and swallows a prompt that follows it.
- It uses the configured default model; `-m <model>` pins one.

## Copilot

```bash
(cd "$REPO" && timeout 15m copilot -p "$review_prompt" --disable-builtin-mcps --silent --stream off \
  --deny-tool 'write' \
  --allow-tool 'shell(gh issue:*)' 'shell(gh pr view:*)' 'shell(gh pr diff:*)' 'shell(git log:*)' 'shell(git show:*)')
```

- Copilot runs commands it recognizes as read-only without asking; the deny rule blocks file writes. Text only: drop the two rule lines and add `--no-custom-instructions --available-tools=''`.
- It serves OpenAI and Anthropic models, so as a third reviewer it adds little. It is useful when Codex or Claude is out of usage.

Antigravity and Cursor were dropped on the test date: headless Antigravity returned nothing once a tool needed a permission, and the Cursor CLI was not signed in.

## Agent-bus chat

The same operations exist as `buddy_agent_*` MCP tools. Your handle is in the session-start context ("message this chat as ...").

```bash
BUS='/Applications/Codex Buddy Host.app/Contents/Helpers/codex-buddy-mcp'
"$BUS" --agent spawn --as "$MY_HANDLE" --harness codex --project "$REPO" \
  --name "Review: <artifact>" --body-file "$review_prompt_file"
"$BUS" --agent wait --as "$MY_HANDLE" --timeout 600 --new-only
"$BUS" --agent link --to "$REVIEWER_HANDLE" --markdown   # a link for the user
```

- `--harness` is `codex`, `claude` or `grok`. To ask a chat that already exists, use `send --chat NAME` instead of `spawn`.
- The project must be under the user's allowed spawn roots (`~/Developer` by default), and a sender gets five spawns an hour.
- The new chat is a full agent under its own approval settings. The brief asks for a read-only review and a reply through the bus.
- Opening a chat needs the Codex Buddy Host app running; without it the call returns `host_unavailable`. On the test date a new Codex chat replied through the bus in about 30 seconds. When the host is down, use a CLI route and say so in the report.
- Acknowledge the reply (`ack MSG`), and offer to archive the review chat once its findings are in the report.
