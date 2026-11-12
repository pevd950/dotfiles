---
name: video-analysis
description: "Analyze local or URL videos with Gemini video understanding plus timestamped local frames/contact sheets; use for video summaries, UI bug diagnosis, animation glitches, visual regressions, demo validation, and questions about screen recordings."
---

# Video Analysis

Combines Gemini video understanding (whole-video summaries, timestamp hints) with local `ffmpeg` frame/contact-sheet extraction for inspectable evidence. Supports local files and downloadable URLs via `yt-dlp`; extracts the selected audio range to `audio/audio.m4a` when present.

## Workflow

1. Run the script — `--mode ui-bug` for app screen recordings, subtle animation issues, or regression diagnosis (dense frame extraction); `--mode frame-only` for local artifacts without Gemini; `--start`/`--end` (and higher `--fps`) whenever the user names a specific moment:

```bash
python3 "$HOME/.agents/skills/productivity/video-analysis/scripts/video_analyze.py" \
  /path/to/repro.mov --mode ui-bug --start 00:12 --end 00:16 --fps 10 \
  --question "Find the subtle animation glitch during navigation"
```

2. Read the generated `analysis.md`, `timeline.json`, and contact sheets; open individual frames when exact visual evidence matters.
3. For UI bugs, Gemini timestamps are hypotheses only — verify or reject them from local frames before reporting. If Gemini flags a bug the frames do not confirm, call it a false lead and keep scanning the frame evidence.
4. For long videos, run Gemini on the whole file first, then rerun focused local extraction around suspicious timestamps.
5. In the answer, cite timestamps and say whether evidence came from Gemini, local frames, or both.

## UI-bug frame checklist

- Content rendering under the navigation bar, status bar, dynamic island, toolbar, keyboard, or input accessory.
- Ghosted, duplicated, stale, or partially clipped messages during transitions.
- Newly sent user messages briefly using the wrong style, alignment, width, or role treatment before settling.
- Scroll position jumps, especially after sending a message or on keyboard show/hide.
- Whole-screen dimming or disabled-state overlays lasting longer than expected.
- Flicker, layout jumps, clipped text, transient wrong route/content, animation discontinuities.

## Output and config

The script prints the output directory and writes `analysis.md`, `timeline.json`, `frames/frame_*_t*.jpg`, `contact_sheets/sheet_*.jpg`, and `audio/audio.m4a` (skip with `--no-audio-extract`).

Each run writes to a new private directory (0700; files 0600). A failed run removes its partial output; remove successful artifacts once they are no longer needed. Omit `--out-dir` to get a unique private directory under the system temp directory. An explicit `--out-dir` must name a directory that does not exist yet, as a canonical path (for example `/private/tmp/new-analysis` on macOS), under existing parents owned by you or root with no symlinks, no ACLs, and no unprotected write access for other users. On macOS, paths under the home directory, Desktop and Downloads included, usually fail the ACL check because of the home directory's deny-delete ACL.

`GEMINI_API_KEY` preferred (`GOOGLE_API_KEY` accepted); source the user's local shell exports if not visible. Default model `gemini-2.5-flash`; pass `--gemini-model gemini-2.5-pro` when deeper whole-video reasoning justifies the latency/cost.
