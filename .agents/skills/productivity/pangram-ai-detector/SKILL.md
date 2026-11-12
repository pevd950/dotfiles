---
name: pangram-ai-detector
description: Analyze text or an image with Pangram's AI-detection APIs, or maintain the Pangram AI Detector shortcut. Use for classifications, detector scores, segment-level results, checking whether an image is AI-generated, or shortcut input/result changes.
---

# Pangram AI Detector

Use the bundled helper, with `PANGRAM_API_KEY` set in the local environment:

```bash
PANGRAM="$HOME/.agents/skills/productivity/pangram-ai-detector/scripts/pangram_detect.py"
"$PANGRAM" --file /path/to/writing.txt              # or pipe the text on stdin
"$PANGRAM" --file /path/to/writing.txt --segments   # segment-level metadata
"$PANGRAM" --file /path/to/writing.txt --json       # JSON
"$PANGRAM" --image /path/to/picture.jpg             # image, one per run
"$PANGRAM" --image /path/to/picture.jpg --model pangram-image-1
```

`--text "..."` also works but appears in shell history and process lists; use stdin or a file for private content. Output omits source-text fields and segment snippets in every mode.

Images are billed per submission, and a rerun is a new billed task. The default model is the cheaper `pangram-image-flash-1`; pass `--model pangram-image-1` when the user asks for the full model or a Flash result is `Unsure`. The image must be 32 MiB or smaller and at least 256 pixels a side; Pangram reports lower confidence below 512. Output is the verdict only: the heatmap, thumbnail and file metadata are dropped.

The helper uses Pangram's asynchronous endpoints: it creates a task, then polls it until `STAGE_SUCCESS` or `STAGE_FAILED`, and stops cleanly on provider failure, malformed responses, or timeout. Text goes to `POST /task` on `https://text.external-api.pangram.com`, images to `POST /v1/tasks` on `https://image.external-api.pangram.com`. `--poll-interval`, `--max-polls`, and `--timeout` tune those bounds. The synchronous `https://text.api.pangram.com/v3` endpoint is deprecated.

## Privacy And Interpretation

- Text and images are sent to Pangram. Submit only the requested content; get explicit approval before sending sensitive or confidential material.
- Results are probabilistic, not proof of authorship. Attribute classifications to Pangram.
- Keep `public_dashboard_link` disabled unless a public link is explicitly requested.

## Results

Report:

- for text, `prediction_short` and `headline` when present, and the AI-generated, AI-assisted, and human fractions as percentages;
- for an image, the prediction label, AI likelihood, confidence, and whether the verdict came from the model or from the file's C2PA content credentials;
- the Pangram version;
- notable segment-level evidence only when it helps explain a text result, without quoting the submitted text;
- a short caveat that the result is a detector signal, not definitive proof.

## Shortcut maintenance

For changes to the Apple shortcut, follow [shortcut maintenance](references/shortcut-maintenance.md) and the installed Shortcuts Playground skill. Preserve live customizations and verify the result on the installed shortcut.
