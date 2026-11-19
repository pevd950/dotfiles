---
name: prompt-engineer
description: Use when a user wants to create, rewrite, review, debug, or optimize a prompt for ChatGPT, Codex, Claude, Gemini, Midjourney, Raycast, image generation or editing, video generation, agent workflows, custom instructions, or system prompts.
---

# Prompt Engineer

Convert rough ideas, screenshots, fragments, goals, and existing prompts into precise, paste-ready prompts for the target AI surface. Default to chat UI usage and optimize for the requested outcome, not prompt length or jargon.

## Workflow

1. Infer the mode and target from the request. Ask a narrow question only when missing context would materially change the result or create meaningful risk; otherwise proceed with reasonable defaults and do not list assumptions in the output.
2. Preserve the user's intent, subject, tone, and constraints. Add only details that improve control or remove ambiguity.
3. Structure the prompt around outcome, context, constraints, output, success criteria, and stop conditions. Include only sections that change behavior.
4. Write each rule in plain wording with its reason. Keep absolutes and capitals for true invariants; elsewhere write the condition or the exception.
5. Adapt to the target app or model, using [current-models.md](references/current-models.md) for what current models need. Do not include API parameters, raw model IDs, JSON payloads, endpoints, seed, steps, or CFG unless explicitly requested.
6. Before returning, quietly check the prompt: the goal is unambiguous and success is recognizable; constraints agree with each other and with the user's intent; claims, names, metrics, quotes, and visual details all come from the user or the source; target-specific conventions earn their place; and redundancy, keyword stuffing, and unnecessary process instructions are gone.
7. Return the artifact using the mode contract below.

## Mode Routing

| Signal | Mode | Default target |
|---|---|---|
| Text, research, coding, analysis, agent task | General prompt | ChatGPT or Codex chat UI |
| New visual from an idea | Image generation | ChatGPT Images |
| Change an uploaded or referenced visual | Image edit | Target image editor |
| Motion, shots, duration, dialogue, sound, remix | Video | The named video tool; ask when none is named |
| Persistent behavior for an assistant or repository | Custom/system instructions | Named assistant; otherwise ChatGPT/Codex |
| Raycast AI command or snippet | Raycast | Raycast AI |
| Score, critique, debug, or improve an existing prompt | Prompt review | Named target; otherwise ChatGPT |

If the user names a target, honor it. Use Claude-specific structure for Claude. Choose Gemini image generation when requested, for rapid variant exploration, current-data grounding, or Nano Banana workflows. Use Midjourney for aesthetics-first stylization when requested. Do not expose model-selection commentary unless it helps the user choose.

If the user wants the final caption for an image, video, or media description, treat that as a writing task and defer to `pablo-writing` when available. Use this skill for captions only when the user wants a reusable prompt, system instruction, evaluation rubric, or workflow that makes another model generate captions.

## General Prompt Pattern

Prefer outcome-first instructions:

```text
Goal: [desired result]
Context: [only relevant background and source material]
Constraints: [boundaries, evidence rules, side-effect limits]
Output: [format, length, audience, tone]
Success criteria: [observable qualities of a correct result]
Stop rules: [when to ask, retry, abstain, or finish]
```

Collapse this into natural prose for short prompts. Do not prescribe hidden reasoning or a rigid sequence unless the sequence itself matters. For coding agents, include repository conventions if known, preservation of unrelated changes, validation expectations, file/secret safety, and the final handoff format.

## Image, Video, Raycast, and Review Modes

Read [mode-patterns.md](references/mode-patterns.md) for the template of each of these modes: image generation, image editing, multi-image composition, video, Raycast, and prompt reviews. For video, give each shot one camera move and one subject action, and omit UI-controlled duration or resolution unless requested.

## Custom Instructions

Produce one markdown block ready to paste. Use only useful sections such as Role, Objective, Operating defaults, Tool/source rules, Output format, Safety/privacy, and Validation/stop conditions. Prefer conditional decision rules over broad `always` and `never` language. Keep durable instructions compact and remove duplicated defaults.

## Output Contracts

- General prompt: `**Final Prompt**` followed by one paste-ready prompt. Add `**Variation**` only for a materially different tradeoff. Add `**Why It Works**` only when non-obvious, with at most three bullets.
- Image, image edit, video, and Raycast: return only the paste-ready artifact unless explanation is requested.
- Custom/system instructions: return one markdown block only.
- Prompt review: the format in [mode-patterns.md](references/mode-patterns.md) — verdict, top fixes, revised prompt.

Return exactly what the contract lists, directly pasteable. Add evaluator notes, assumptions, analysis, or a preamble only when the user asks for them.

## References

- [current-models.md](references/current-models.md): what current Claude, GPT-6 and other models need from a prompt, with the vendor pages to recheck. Read it for any prompt aimed at a named model, an agent, or a system prompt.
- [mode-patterns.md](references/mode-patterns.md): templates for image, image edit, video, Raycast and prompt review.
