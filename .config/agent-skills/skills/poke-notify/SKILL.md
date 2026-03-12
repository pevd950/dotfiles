---
name: poke-notify
description: "Send Pablo a concise handoff message through Poke's inbound SMS webhook using the local POKE_API_KEY environment variable; use when the user asks an agent to notify him that work is done, ready for review, or needs attention, and include helpful URLs or concrete follow-up details when available."
---

# Poke Notify

## When to use it
- The user explicitly asks you to send a message through Poke.
- You need to notify Pablo that work is done, ready for review, or needs attention on his laptop.
- Treat Poke as a relay/messenger, not the reviewer or executor of the task.
- Use it for handoffs, not just pings. Include the minimum context Pablo needs to act without reopening the full thread first.

## Endpoint
- `https://poke.com/api/v1/inbound-sms/webhook`

## Requirements
- `POKE_API_KEY` must already be set in the shell environment.
- Never print, store, commit, log, or echo the resolved secret value.
- The payload must include a non-empty `message` field.
- Include direct URLs when they exist and are useful, such as PRs, issues, CI runs, docs, designs, or other hosted review artifacts.

## Workflow
1. Confirm the message text is appropriate, concise, and contains the useful handoff context.
2. Write the message so Poke understands it is a relay for Pablo, not a new task for Poke.
3. Include these fields when they are available:
   - current status or request: what is done, blocked, or ready for review
   - concrete context: branch, feature, bug, or decision in one short clause
   - direct URLs: PR, issue, CI run, design, doc, or other click-ready links
   - next action: what Pablo should do, if anything
4. Prefer this structure:
   - `For Pablo from <agent>: <status/update>. Context: <one-line handoff>. Links: <label> <url> [| <label> <url>]. Next step: <review/merge/respond/etc>. No action needed from you beyond relaying this message.`
5. Keep URLs as plain text, not Markdown, so they remain clickable in the final message.
6. Do not invent links or pad the message. Omit sections that do not have real content.
7. Validate first:
   - `scripts/send_notification.py --check --message "For Pablo from Codex: work on the notification skill is ready for review. Context: updated the skill so agents include handoff details and click-ready PR or issue links. Links: PR https://github.com/org/repo/pull/123 | Issue https://github.com/org/repo/issues/456. Next step: review the wording and merge if it looks right. No action needed from you beyond relaying this message."`
8. Send only after the check passes:
   - `scripts/send_notification.py --send --message "For Pablo from Codex: work on the notification skill is ready for review. Context: updated the skill so agents include handoff details and click-ready PR or issue links. Links: PR https://github.com/org/repo/pull/123 | Issue https://github.com/org/repo/issues/456. Next step: review the wording and merge if it looks right. No action needed from you beyond relaying this message."`
9. Report only the redacted result back to the user.

## Message content rules
- Prefer one compact paragraph over multiple short fragments.
- Include URLs only when they materially help Pablo jump into the work faster.
- If there is a review request, say what kind: review PR, answer blocker, inspect CI, or read issue context.
- If there is no action for Pablo, say that explicitly.
- If the handoff depends on local-only context, summarize that context in the message instead of referencing a path Pablo cannot open from his phone.

## Notes
- Auth uses `Authorization: Bearer $POKE_API_KEY`.
- The helper script performs schema validation before any real delivery.
- The canonical skill lives in `~/.config/agent-skills/skills/poke-notify/`.
- Provider-specific locations should use symlinks to this shared folder.
- Avoid imperative messages like `come to my laptop` with no context; they make Poke infer the wrong role.
- Good link targets include GitHub PRs, GitHub issues, CI/build pages, docs, designs, and other URLs Pablo can open directly from iMessage.
