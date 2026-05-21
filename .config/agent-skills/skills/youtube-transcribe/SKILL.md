---
name: youtube-transcribe
description: Download a YouTube video with yt-dlp, extract audio with ffmpeg, transcribe it with whisper.cpp, and save the media, transcript, subtitles, and metadata into a user-configured output folder such as iCloud Drive. Use when the user gives a YouTube URL and wants a local video/transcript archive.
---

# YouTube Transcribe

## Workflow

Use the bundled script:

```bash
scripts/youtube_transcribe.sh "https://www.youtube.com/watch?v=..."
```

The script creates one folder per video and writes:

- `video.*`
- `audio.wav`
- `transcript.md`
- `transcript.txt`
- `transcript.srt`
- `transcript.json`
- `metadata.json`

## Required Environment

The script needs these local tools on `PATH`:

```bash
yt-dlp
ffmpeg
whisper-cli
python3
```

Configure machine-local paths outside the tracked skill:

```bash
export AI_INBOX_DIR="..."
export YT_TRANSCRIBE_WHISPER_MODEL="..."
```

The script writes to `$AI_INBOX_DIR/YouTube` by default. Use `YT_TRANSCRIBE_OUTPUT_DIR`,
`--output-dir`, or `--model` for one-off overrides.

## Common Commands

Default run:

```bash
scripts/youtube_transcribe.sh "$URL"
```

Specify language and title hint:

```bash
scripts/youtube_transcribe.sh "$URL" --language auto --title "Short readable folder name"
```

Use a different output root or model:

```bash
scripts/youtube_transcribe.sh "$URL" --output-dir "$DIR" --model "$MODEL"
```

## Notes

- Prefer `AI_INBOX_DIR` as the shared artifact root for files that should sync outside the current host.
- Use `YT_TRANSCRIBE_OUTPUT_DIR` only when this workflow needs a tool-specific output root.
- Use `YT_TRANSCRIBE_WHISPER_MODEL` for the local model path.
- Do not hard-code personal filesystem paths into this skill.
- Keep generated artifacts in the per-video folder; do not scatter files into the output root.
