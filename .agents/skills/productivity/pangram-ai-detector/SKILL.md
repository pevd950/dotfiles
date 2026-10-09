---
name: pangram-ai-detector
description: Analyze text with Pangram's AI-detection API. Use when asked for a classification, detector score, or segment-level results.
---

# Pangram AI Detector

Use the bundled helper:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py --help
```

Set `PANGRAM_API_KEY` in the local environment. Never include the key in repository files, logs, or reports.

## Privacy And Interpretation

- Text is sent to Pangram. Submit only the requested content; get explicit approval before sending sensitive or confidential material.
- Results are probabilistic, not proof of authorship. Attribute classifications to Pangram.
- Keep `public_dashboard_link` disabled unless a public link is explicitly requested.
- Output omits source-text fields and segment snippets.

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

Analyze explicit text (`--text` may appear in shell history and process lists; use stdin or a file for private content):

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

Return JSON without source-text fields:

```bash
$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py \
  --file /path/to/writing.txt \
  --json
```

The current API is asynchronous. The helper creates a task, polls it with a bounded number of status checks, and stops cleanly on provider failure, malformed responses, or timeout. `--poll-interval`, `--max-polls`, and `--timeout` can tune those bounds when necessary.

## Results

Report:

- `prediction_short` and `headline` when present;
- AI-generated, AI-assisted, and human fractions as percentages;
- the Pangram API version;
- notable segment-level evidence only when it helps explain the result, without quoting the submitted text;
- a short caveat that the result is a detector signal, not definitive proof.

Use Pangram's current asynchronous inference endpoints on `https://text.external-api.pangram.com`: create with `POST /task`, then poll `GET /task/{task_id}` until `STAGE_SUCCESS` or `STAGE_FAILED`. Do not use the deprecated synchronous `https://text.api.pangram.com/v3` endpoint.
