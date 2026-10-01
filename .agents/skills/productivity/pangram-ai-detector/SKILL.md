---
name: pangram-ai-detector
description: Check whether requested text is classified by Pangram as AI-generated, AI-assisted, mixed, or human-written. Use when Pablo asks whether his writing or someone else's text looks AI-written, wants a detector score, or needs segment-level AI-writing signals.
---

# Pangram AI Detector

Use the bundled helper:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py --help
```

Authentication uses `PANGRAM_API_KEY` from the host's local environment, normally `~/.zshenv.local`. Never print, paste, commit, or store the key in skill files, repository files, notes, logs, or generated reports.

## Privacy And Interpretation

- Pangram is an external service. Send only the text Pablo asked to analyze.
- Do not upload unrelated email, private messages, credentials, medical or financial material, confidential work, or unpublished sensitive documents without explicit approval for that content.
- AI detection is probabilistic. Report the returned classification and fractions as evidence, not proof of authorship or misconduct.
- Do not accuse another person of using AI based only on this result. Phrase conclusions as `Pangram classified...` or `Pangram found...`.
- Keep `public_dashboard_link` disabled unless Pablo explicitly requests a public link.
- The helper deliberately omits Pangram's returned source-text fields and segment snippets from both human-readable and JSON output.

## Common Usage

Analyze a file:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py \
  --file /path/to/writing.txt
```

Analyze piped text:

```bash
cat /path/to/writing.txt | $HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py
```

Analyze explicit non-sensitive text only (`--text` is visible in process arguments and may enter shell history). Use stdin or a private file for sensitive writing:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py \
  --text "Text to analyze"
```

Show segment-level metadata without source-text snippets:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py \
  --file /path/to/writing.txt \
  --segments
```

Return machine-readable JSON without echoing the submitted text:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py \
  --file /path/to/writing.txt \
  --json
```

The current API is asynchronous. The helper creates a task, polls it with a bounded number of status checks, and stops cleanly on provider failure, malformed responses, or timeout. `--poll-interval`, `--max-polls`, and `--timeout` can tune those bounds when necessary.

## Reporting Contract

Report:

- `prediction_short` and the locally generated classification headline;
- AI-generated, AI-assisted, and human fractions as percentages;
- the Pangram API version when it matches a numeric version format; otherwise report unavailable;
- notable segment-level evidence only when it helps explain the result, without quoting the submitted text;
- a short caveat that the result is a detector signal, not definitive proof.

Use Pangram's current asynchronous inference endpoints on `https://text.external-api.pangram.com`: create with `POST /task`, then poll `GET /task/{task_id}` until `STAGE_SUCCESS` or `STAGE_FAILED`. Do not use the deprecated synchronous `https://text.api.pangram.com/v3` endpoint.
