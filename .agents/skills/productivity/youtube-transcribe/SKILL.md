---
name: youtube-transcribe
description: Download a YouTube video with yt-dlp, extract audio with ffmpeg, transcribe it with whisper.cpp, and save the media, transcript, subtitles, and metadata into a user-configured output folder such as a synced drive. Use when the user gives a YouTube URL and wants a local video/transcript archive.
---

# YouTube Transcribe

Use the bundled script:

```bash
scripts/youtube_transcribe.sh "https://www.youtube.com/watch?v=..."
```

It creates one folder per video and writes `video.*`, `audio.wav`, `transcript.md`, `transcript.txt`, `transcript.srt`, `transcript.json`, and `metadata.json`. Keep generated artifacts in the per-video folder; do not scatter files into the output root.

## Environment

Requires `yt-dlp`, `ffmpeg`, `whisper-cli`, and `python3` on `PATH`. Machine-local configuration stays outside the tracked skill:

- Output root: `$AI_INBOX_DIR/YouTube` by default; override with `YT_TRANSCRIBE_OUTPUT_DIR` or `--output-dir` only when this workflow needs a tool-specific root.
- Whisper model path: `YT_TRANSCRIBE_WHISPER_MODEL`, or `--model` for one-offs.

## Options

```bash
scripts/youtube_transcribe.sh "$URL" --language auto --title "Short readable folder name"
scripts/youtube_transcribe.sh "$URL" --output-dir "$DIR" --model "$MODEL"
```

Do not hard-code personal filesystem paths into this skill.
