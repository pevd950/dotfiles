# Claude Prompting Best Practices

Reviewed: 2026-10-01

Use Claude-specific guidance when the user names Claude. Verify current model availability and capabilities against Anthropic documentation rather than a fixed model roster.

## Claude Prompt Shape

Claude generally benefits from:

- Clear role and task
- Relevant context before instructions
- Explicit output format
- Examples for nuanced style or classification
- XML-style tags for separating source material, instructions, and output requirements when prompts are complex
- Clear tool-use and stopping conditions for agentic workflows

## Chat UI Pattern

```text
You are [role].

Task:
[What to do]

Context:
[Relevant background]

Instructions:
- [Concrete requirement]
- [Constraint]
- [Priority]

Output format:
[Sections, length, style]
```

For source-heavy prompts:

```xml
<context>
[source material]
</context>

<task>
[what to produce]
</task>

<requirements>
- [constraint]
- [format]
- [quality bar]
</requirements>
```

## Claude-Specific Notes

- Use examples when tone, format, or classification boundaries matter.
- Use tags to reduce ambiguity in long prompts.
- For agentic/coding prompts, specify what tools or sources to inspect, what changes are allowed, and how to verify.
- For thinking-capable modes, ask for concise reasoning summaries or decisions, not hidden chain-of-thought.
- Keep durable instructions compact and direct; avoid a pile-up of vague personality traits.

## When To Choose Claude

Use Claude-specific prompting when the user asks for Claude, Anthropic, XML-tagged prompts, long-document writing, careful editing, or Claude project/custom instruction work.

## Refresh Source

- Anthropic Claude prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
