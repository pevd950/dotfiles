---
name: video-analysis
description: "Analyze local or URL videos with Gemini video understanding plus timestamped local frames/contact sheets; use for video summaries, UI bug diagnosis, animation glitches, visual regressions, demo validation, and questions about screen recordings."
---

# Video Analysis

## What this skill does
- Uses Gemini video understanding for whole-video summaries and timestamp hints.
- Extracts local timestamped frames and contact sheets with `ffmpeg` for inspectable evidence.
- Extracts the selected audio range to `audio/audio.m4a` when the source has an audio stream.
- Supports local files and public/downloadable URLs via `yt-dlp`.
- Biases `ui-bug` mode toward dense frame extraction so brief animation glitches, flicker, layout jumps, and transient UI states can be inspected.

## When to use it
- The user provides a video URL or local video path and asks what happens in it.
- The user asks to diagnose, validate, or inspect a UI screen recording.
- The user mentions animation glitches, flicker, visual regressions, layout jumps, or brief states.

## Workflow
1. Run `scripts/video_analyze.py` with the video source and task.
2. Prefer `--mode ui-bug` for app screen recordings, subtle animation issues, visual validation, or regression diagnosis.
3. Use `--start` and `--end` whenever the user names a specific moment; focused extraction is much better for brief UI states.
4. Read the generated `analysis.md`, `timeline.json`, and contact sheets. Open individual frame files when exact visual evidence matters.
5. For UI bugs, treat Gemini timestamps as hypotheses only. Verify or reject them from local frames before reporting a finding.
6. In the answer, cite timestamps and say whether evidence came from Gemini, local frames, or both.

## UI bug local-frame checklist
When inspecting contact sheets or individual frames, explicitly check for:

- Content rendering under the navigation bar, status bar, dynamic island, toolbar, keyboard, or input accessory.
- Ghosted, duplicated, stale, or partially clipped messages during transitions.
- Newly sent user messages briefly using the wrong style, alignment, width, or role treatment before settling.
- Scroll position jumps, especially after sending a message or when the keyboard appears/disappears.
- Whole-screen dimming or disabled-state overlays that remain longer than expected.
- Flicker, layout jumps, clipped text, transient wrong route/content, and animation discontinuities.

If Gemini flags a bug that local frames do not confirm, say it was a false lead and continue scanning the local frame evidence.

## Commands
Gemini plus dense local frames for a UI bug:

```bash
python3 "$HOME/.config/agent-skills/skills/video-analysis/scripts/video_analyze.py" \
  /path/to/repro.mov \
  --mode ui-bug \
  --question "Find the subtle animation glitch during navigation"
```

Focused inspection around a known moment:

```bash
python3 "$HOME/.config/agent-skills/skills/video-analysis/scripts/video_analyze.py" \
  /path/to/repro.mov \
  --mode ui-bug \
  --start 00:12 \
  --end 00:16 \
  --fps 10
```

Local-only artifacts when Gemini is unnecessary or unavailable:

```bash
python3 "$HOME/.config/agent-skills/skills/video-analysis/scripts/video_analyze.py" \
  /path/to/video.mp4 \
  --mode frame-only \
  --question "Inspect the transition"
```

## Output
The script prints the output directory and writes:

- `analysis.md` - short report with paths and Gemini response when available.
- `timeline.json` - metadata, frame timestamps, contact sheets, and Gemini text.
- `frames/frame_00001_t00-00-000.jpg` - timestamped local frames.
- `contact_sheets/sheet_001.jpg` - tiled frame overview for quick inspection.
- `audio/audio.m4a` - selected audio range when present.

## Notes
- `GEMINI_API_KEY` is preferred; `GOOGLE_API_KEY` is accepted as a fallback.
- The default Gemini model is `gemini-2.5-flash`; pass `--gemini-model gemini-2.5-pro` when deeper whole-video reasoning is worth the extra latency/cost.
- If the key is not visible in the shell, source the user's local shell exports before running the script.
- Pass `--no-audio-extract` to skip local audio artifact generation.
- For subtle UI issues, do not rely on Gemini alone. Use local high-FPS frames or contact sheets as evidence.
- For long videos, run Gemini on the whole file first, then rerun focused local extraction around suspicious timestamps.
