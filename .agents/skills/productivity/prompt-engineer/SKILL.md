---
name: prompt-engineer
description: Use when a user wants to create, rewrite, review, debug, or optimize a prompt for ChatGPT, Codex, Claude, Gemini, Sora, Midjourney, Raycast, image generation or editing, video generation, agent workflows, custom instructions, or system prompts.
---

# Prompt Engineer

Convert rough ideas, screenshots, fragments, goals, and existing prompts into precise, paste-ready prompts for the target AI surface. Default to chat UI usage and optimize for the requested outcome, not prompt length or jargon.

## Workflow

1. Infer the mode and target from the request. Ask a narrow question only when missing context would materially change the result or create meaningful risk; otherwise proceed with reasonable defaults and do not list assumptions in the output.
2. Preserve the user's intent, subject, tone, and constraints. Add only details that improve control or remove ambiguity.
3. Structure the prompt around outcome, context, constraints, output, success criteria, and stop conditions. Include only sections that change behavior.
4. Adapt to the target app or model. Do not include API parameters, raw model IDs, JSON payloads, endpoints, seed, steps, or CFG unless explicitly requested.
5. Quietly check for contradictions, redundancy, fabricated details, keyword stuffing, and unnecessary process instructions.
6. Return the artifact using the mode contract below.

## Mode Routing

| Signal | Mode | Default target |
|---|---|---|
| Text, research, coding, analysis, agent task | General prompt | ChatGPT or Codex chat UI |
| New visual from an idea | Image generation | ChatGPT Images |
| Change an uploaded or referenced visual | Image edit | Target image editor |
| Motion, shots, duration, dialogue, sound, remix | Video | Sora-style prompting |
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

## Image and Video Rules

For image generation, begin with `Create...` or `Generate...` and order details as: use case, setting, subject, composition/camera, style/medium, lighting/color, exact text, constraints. Prefer concrete scene language over quality filler. If text appears in the image, quote it exactly, specify its typography and placement, and end with `No other text.`

For image edits, explicitly separate the requested change from invariants. Restate identity, face, age, proportions, expression, pose, crop, camera, perspective, lighting, shadows, color temperature, background, surrounding objects, text, logos, and layout as unchanged when relevant. End with `No other changes. No extra text, logos, or watermarks.` Refer to multiple inputs as Image 1, Image 2, and so on, and assign each input a clear role.

For video, describe visual style, framing, one camera move per shot, and one subject action per shot in short timed beats. Put speech in a `Dialogue:` block and audio in a `Background Sound:` block. Omit UI-controlled duration or resolution unless requested.

Read [mode-patterns.md](references/mode-patterns.md) when handling image generation, image editing, multi-image composition, video, Raycast, or prompt reviews.

## Custom Instructions

Produce one markdown block ready to paste. Use only useful sections such as Role, Objective, Operating defaults, Tool/source rules, Output format, Safety/privacy, and Validation/stop conditions. Prefer conditional decision rules over broad `always` and `never` language. Keep durable instructions compact and remove duplicated defaults.

## Output Contracts

- General prompt: `**Final Prompt**` followed by one paste-ready prompt. Add `**Variation**` only for a materially different tradeoff. Add `**Why It Works**` only when non-obvious, with at most three bullets.
- Image, image edit, video, and Raycast: return only the paste-ready artifact unless explanation is requested.
- Custom/system instructions: return one markdown block only.
- Prompt review: provide an overall score from 0–10, a one-sentence `Ready to ship` or `Needs revision` verdict, the top three fixes, and a revised prompt. Score clarity, completeness, target fit, output control, and practicality from 0–10 and use their rounded average for the overall score.

Do not append evaluator notes, assumption logs, analysis, setup commentary, or a preamble unless the user explicitly requests them or the selected output contract includes them. When the contract says to return only the artifact, any extra text is a failure.

## Quality Gate

Before returning the prompt, verify:

- The goal is unambiguous and the output can be recognized as successful.
- Constraints do not conflict and preserve the user's actual intent.
- Target-specific conventions improve the result rather than adding ceremony.
- Claims, names, metrics, quotes, and visual details are not invented.
- The prompt is directly pasteable and contains no wrapper the user did not request.

## References

- Read [frontier-model-prompting.md](references/frontier-model-prompting.md) for current frontier-model prompting, the GPT-6.1 Sol evidence boundary, agent authority, instruction conflicts, validation, and migration. Verify new model-specific claims against current official documentation; local Codex labels alone do not establish public capabilities.
- Read [ai-prompting-best-practices.md](references/ai-prompting-best-practices.md) for the general chat-UI prompt shape and anti-patterns.
- Read [claude-prompting-best-practices.md](references/claude-prompting-best-practices.md) when Claude, Anthropic, XML-separated context, or long-document workflows are requested.
