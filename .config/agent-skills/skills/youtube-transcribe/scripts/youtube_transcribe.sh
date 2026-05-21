#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  youtube_transcribe.sh URL [--output-dir DIR] [--model MODEL] [--language LANG] [--title TITLE]

Environment:
  AI_INBOX_DIR                   Shared artifact inbox root.
  YT_TRANSCRIBE_OUTPUT_DIR       Default output root; defaults to $AI_INBOX_DIR/YouTube.
  YT_TRANSCRIBE_WHISPER_MODEL    Default whisper.cpp ggml model path.
  YT_TRANSCRIBE_LANGUAGE         Default language, defaults to auto.
  YT_TRANSCRIBE_THREADS          Optional whisper-cli thread count.
  YT_TRANSCRIBE_WHISPER_NO_GPU   Set to 1/true/yes to pass -ng to whisper-cli.
USAGE
}

die() {
  printf 'error: %s\n' "$*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

url=""
output_dir="${YT_TRANSCRIBE_OUTPUT_DIR:-}"
if [ -z "$output_dir" ] && [ -n "${AI_INBOX_DIR:-}" ]; then
  output_dir="${AI_INBOX_DIR%/}/YouTube"
fi
model="${YT_TRANSCRIBE_WHISPER_MODEL:-}"
language="${YT_TRANSCRIBE_LANGUAGE:-auto}"
title_override=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --output-dir)
      [ "$#" -ge 2 ] || die "--output-dir requires a value"
      output_dir="$2"
      shift 2
      ;;
    --model)
      [ "$#" -ge 2 ] || die "--model requires a value"
      model="$2"
      shift 2
      ;;
    --language)
      [ "$#" -ge 2 ] || die "--language requires a value"
      language="$2"
      shift 2
      ;;
    --title)
      [ "$#" -ge 2 ] || die "--title requires a value"
      title_override="$2"
      shift 2
      ;;
    --)
      shift
      break
      ;;
    -*)
      die "unknown option: $1"
      ;;
    *)
      if [ -z "$url" ]; then
        url="$1"
      else
        die "unexpected argument: $1"
      fi
      shift
      ;;
  esac
done

[ -n "$url" ] || die "URL is required"
[ -n "$output_dir" ] || die "set AI_INBOX_DIR, YT_TRANSCRIBE_OUTPUT_DIR, or pass --output-dir"
[ -n "$model" ] || die "set YT_TRANSCRIBE_WHISPER_MODEL or pass --model"
[ -f "$model" ] || die "whisper model not found: $model"
case "$model" in
  *for-tests-ggml-*.bin)
    die "refusing whisper.cpp's empty test model; set YT_TRANSCRIBE_WHISPER_MODEL to a real ggml model"
    ;;
esac

need_cmd yt-dlp
need_cmd ffmpeg
need_cmd whisper-cli
need_cmd python3

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

metadata_tmp="$tmp_dir/metadata.json"
yt-dlp --dump-single-json --no-playlist "$url" > "$metadata_tmp"

folder_name="$(
  python3 - "$metadata_tmp" "$title_override" <<'PY'
import json
import re
import sys

path, override = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
title = override or data.get("title") or "youtube-video"
video_id = data.get("id") or "unknown-id"
slug = re.sub(r"[^A-Za-z0-9._ -]+", "", title).strip()
slug = re.sub(r"\s+", " ", slug)[:160].strip(" ._-")
print(f"{slug or 'youtube-video'} [{video_id}]")
PY
)"

work_dir="${output_dir%/}/$folder_name"
mkdir -p "$work_dir"
cp "$metadata_tmp" "$work_dir/metadata.json"

yt-dlp \
  --no-playlist \
  --format "bv*+ba/b" \
  --merge-output-format mp4 \
  --write-info-json \
  --write-thumbnail \
  --paths "$work_dir" \
  --output "%(title).200B [%(id)s].%(ext)s" \
  "$url"

video_path="$(
  python3 - "$work_dir" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
exts = {".mp4", ".mkv", ".webm", ".mov", ".m4v"}
files = [p for p in root.iterdir() if p.is_file() and p.suffix.lower() in exts]
if not files:
    raise SystemExit("no downloaded video file found")
print(max(files, key=lambda p: p.stat().st_size))
PY
)"

stable_video="$work_dir/video.${video_path##*.}"
if [ "$video_path" != "$stable_video" ]; then
  mv "$video_path" "$stable_video"
fi

audio_path="$work_dir/audio.wav"
ffmpeg -y -i "$stable_video" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$audio_path"

transcript_base="$work_dir/transcript"
whisper_args=(-m "$model" -f "$audio_path" -l "$language" -otxt -osrt -oj -of "$transcript_base" -pp)
case "${YT_TRANSCRIBE_WHISPER_NO_GPU:-}" in
  1|true|TRUE|yes|YES)
    whisper_args=(-ng "${whisper_args[@]}")
    ;;
esac
if [ -n "${YT_TRANSCRIBE_THREADS:-}" ]; then
  whisper_args=(-t "$YT_TRANSCRIBE_THREADS" "${whisper_args[@]}")
fi
whisper-cli "${whisper_args[@]}"

python3 - "$work_dir/metadata.json" "$transcript_base.txt" "$work_dir/transcript.md" "$url" "$stable_video" <<'PY'
import json
import sys
from pathlib import Path

metadata_path, transcript_path, md_path, source_url, video_path = sys.argv[1:]
metadata = json.load(open(metadata_path, encoding="utf-8"))
title = metadata.get("title") or Path(video_path).parent.name
channel = metadata.get("channel") or metadata.get("uploader") or ""
upload_date = metadata.get("upload_date") or ""
transcript = Path(transcript_path).read_text(encoding="utf-8").strip()

lines = [
    f"# {title}",
    "",
    f"- Source: {source_url}",
    f"- Video: {video_path}",
]
if channel:
    lines.append(f"- Channel: {channel}")
if upload_date:
    lines.append(f"- Upload date: {upload_date}")
lines.extend(["", "## Transcript", "", transcript, ""])

Path(md_path).write_text("\n".join(lines), encoding="utf-8")
PY

printf '%s\n' "$work_dir"
