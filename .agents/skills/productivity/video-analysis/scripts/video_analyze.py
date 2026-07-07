#!/usr/bin/env python3
"""Analyze videos with Gemini plus local timestamped frame artifacts."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


@dataclass
class FrameInfo:
    path: str
    timestamp_seconds: float
    timestamp: str


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required binary: {name}")


def is_url(source: str) -> bool:
    parsed = urllib.parse.urlparse(source)
    return parsed.scheme in {"http", "https"}


def parse_time(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    parts = text.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        pass
    raise SystemExit(f"Cannot parse time {value!r}; expected SS, MM:SS, or HH:MM:SS")


def format_time(seconds: float) -> str:
    millis = int(round((seconds - int(seconds)) * 1000))
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, sec = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}.{millis:03d}"
    return f"{minutes:02d}:{sec:02d}.{millis:03d}"


def safe_time_for_name(seconds: float) -> str:
    return format_time(seconds).replace(":", "-").replace(".", "-")


def default_out_dir(source: str) -> Path:
    stem = Path(urllib.parse.urlparse(source).path if is_url(source) else source).stem or "video"
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return Path(tempfile.gettempdir()) / f"video-analysis-{stem}-{stamp}"


def resolve_source(source: str, out_dir: Path) -> Path:
    if not is_url(source):
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"Video file does not exist: {path}")
        return path

    require_binary("yt-dlp")
    download_dir = out_dir / "download"
    download_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(download_dir / "%(title).200B-%(id)s.%(ext)s")
    run([
        "yt-dlp",
        "--no-playlist",
        "-f",
        "bv*+ba/b",
        "-o",
        output_template,
        source,
    ])
    candidates = [p for p in download_dir.iterdir() if p.is_file()]
    if not candidates:
        raise SystemExit("yt-dlp completed but no video file was found")
    return max(candidates, key=lambda p: p.stat().st_size)


def probe(video_path: Path) -> dict:
    require_binary("ffprobe")
    result = run([
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ], capture=True)
    data = json.loads(result.stdout)
    video_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    audio_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    duration = float(video_stream.get("duration") or data.get("format", {}).get("duration") or 0)
    return {
        "path": str(video_path),
        "duration_seconds": duration,
        "width": int(video_stream.get("width") or 0),
        "height": int(video_stream.get("height") or 0),
        "codec": video_stream.get("codec_name"),
        "format": data.get("format", {}).get("format_name"),
        "audio": {
            "present": bool(audio_stream),
            "codec": audio_stream.get("codec_name"),
            "sample_rate": int(audio_stream.get("sample_rate") or 0) if audio_stream else 0,
            "channels": int(audio_stream.get("channels") or 0) if audio_stream else 0,
            "channel_layout": audio_stream.get("channel_layout"),
            "duration_seconds": float(audio_stream.get("duration") or 0) if audio_stream else 0,
            "bit_rate": int(audio_stream.get("bit_rate") or 0) if audio_stream and str(audio_stream.get("bit_rate") or "").isdigit() else 0,
        },
    }


def choose_defaults(mode: str, focused: bool) -> tuple[float, int, int]:
    if mode == "ui-bug":
        return (10.0 if focused else 4.0, 600 if focused else 360, 1280)
    if mode == "visual-regression":
        return (6.0 if focused else 2.0, 420 if focused else 240, 1280)
    return (1.0, 160, 960)


def extract_frames(
    video_path: Path,
    frames_dir: Path,
    *,
    start: float,
    end: float,
    fps: float,
    max_frames: int,
    width: int,
) -> tuple[list[FrameInfo], float]:
    require_binary("ffmpeg")
    frames_dir.mkdir(parents=True, exist_ok=True)
    duration = max(0.001, end - start)
    effective_fps = min(fps, max_frames / duration)
    if effective_fps <= 0:
        raise SystemExit("Frame extraction FPS resolved to zero")

    temp_pattern = frames_dir / "raw_%05d.jpg"
    vf = f"fps={effective_fps:.6f},scale={width}:-2"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(video_path),
        "-t",
        f"{duration:.3f}",
        "-vf",
        vf,
        "-frames:v",
        str(max_frames),
        "-q:v",
        "2",
        str(temp_pattern),
    ]
    run(cmd)

    raw_frames = sorted(frames_dir.glob("raw_*.jpg"))
    frames: list[FrameInfo] = []
    for index, raw in enumerate(raw_frames, start=1):
        timestamp = start + ((index - 1) / effective_fps)
        name = f"frame_{index:05d}_t{safe_time_for_name(timestamp)}.jpg"
        final = frames_dir / name
        raw.rename(final)
        frames.append(FrameInfo(str(final), timestamp, format_time(timestamp)))
    return frames, effective_fps


def make_contact_sheets(frames_dir: Path, sheets_dir: Path, frame_count: int) -> list[str]:
    if frame_count == 0:
        return []
    require_binary("ffmpeg")
    sheets_dir.mkdir(parents=True, exist_ok=True)
    sheet_paths: list[str] = []
    per_sheet = 50
    for sheet_index, start_index in enumerate(range(0, frame_count, per_sheet), start=1):
        end_index = min(start_index + per_sheet - 1, frame_count - 1)
        rows = max(1, ((end_index - start_index + 1) + 4) // 5)
        sheet_path = sheets_dir / f"sheet_{sheet_index:03d}.jpg"
        vf = (
            f"select='between(n\\,{start_index}\\,{end_index})',"
            "scale=320:-2,"
            f"tile=5x{rows}:padding=8:margin=8:color=white"
        )
        run([
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-framerate",
            "1",
            "-pattern_type",
            "glob",
            "-i",
            str(frames_dir / "frame_*.jpg"),
            "-vf",
            vf,
            "-frames:v",
            "1",
            str(sheet_path),
        ])
        sheet_paths.append(str(sheet_path))
    return sheet_paths


def extract_audio(video_path: Path, audio_dir: Path, *, start: float, end: float, has_audio: bool) -> str | None:
    if not has_audio:
        return None
    require_binary("ffmpeg")
    audio_dir.mkdir(parents=True, exist_ok=True)
    output = audio_dir / "audio.m4a"
    duration = max(0.001, end - start)
    run([
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(video_path),
        "-t",
        f"{duration:.3f}",
        "-vn",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        str(output),
    ])
    return str(output)


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, data: bytes | None = None) -> dict:
    req = urllib.request.Request(url, method=method, headers=headers or {}, data=data)
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            body = response.read()
            return json.loads(body.decode("utf-8")) if body else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini request failed: HTTP {exc.code}: {detail}") from exc


def start_gemini_upload(api_key: str, video_path: Path, mime_type: str) -> str:
    url = f"{GEMINI_API_BASE}/upload/v1beta/files?key={urllib.parse.quote(api_key)}"
    size = video_path.stat().st_size
    payload = json.dumps({"file": {"display_name": video_path.name}}).encode("utf-8")
    req = urllib.request.Request(
        url,
        method="POST",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            upload_url = response.headers.get("X-Goog-Upload-URL")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini upload start failed: HTTP {exc.code}: {detail}") from exc
    if not upload_url:
        raise SystemExit("Gemini upload start did not return X-Goog-Upload-URL")
    return upload_url


def upload_to_gemini(api_key: str, video_path: Path) -> dict:
    mime_type = mimetypes.guess_type(video_path.name)[0] or "video/mp4"
    upload_url = start_gemini_upload(api_key, video_path, mime_type)
    with video_path.open("rb") as handle:
        payload = handle.read()
    response = request_json(
        upload_url,
        method="POST",
        headers={
            "Content-Type": mime_type,
            "X-Goog-Upload-Command": "upload, finalize",
            "X-Goog-Upload-Offset": "0",
        },
        data=payload,
    )
    file_obj = response.get("file", response)
    name = file_obj.get("name")
    if not name:
        raise SystemExit(f"Gemini upload response did not include a file name: {response}")

    poll_url = f"{GEMINI_API_BASE}/v1beta/{name}?key={urllib.parse.quote(api_key)}"
    for _ in range(90):
        current = request_json(poll_url)
        state = current.get("state") or current.get("file", {}).get("state")
        if state in {None, "ACTIVE"}:
            return current
        if state == "FAILED":
            raise SystemExit(f"Gemini file processing failed: {current}")
        time.sleep(2)
    raise SystemExit("Gemini file processing timed out")


def gemini_prompt(mode: str, question: str | None, start: float, end: float) -> str:
    task = question or "Summarize the video and call out notable visual and audio moments."
    focus = f"The local frame extraction range is {format_time(start)} to {format_time(end)}."
    ui = (
        "Pay special attention to subtle UI bugs: content rendering under navigation/status bars, dynamic island, "
        "toolbars, keyboards, or input accessories; ghosted, duplicated, stale, or clipped messages; user messages briefly "
        "using the wrong style, alignment, width, or role treatment before settling; scroll-position jumps; "
        "flicker, layout jumps, clipped text, transient wrong states, stutters, skipped animation states, "
        "button or toolbar flashes, dimming overlays, and timing-sensitive visual regressions. "
        "Return suspicious timestamps even if confidence is low."
    )
    return "\n".join([
        "Analyze this video for a coding assistant.",
        f"Mode: {mode}.",
        focus,
        f"User question: {task}",
        ui if mode in {"ui-bug", "visual-regression"} else "",
        "Return concise Markdown with: Summary, Timeline, Suspicious timestamps, and Follow-up local frame windows.",
    ]).strip()


def analyze_with_gemini(api_key: str, video_path: Path, *, model: str, mode: str, question: str | None, start: float, end: float) -> dict:
    file_obj = upload_to_gemini(api_key, video_path)
    file_uri = file_obj.get("uri") or file_obj.get("file", {}).get("uri")
    mime_type = file_obj.get("mimeType") or file_obj.get("mime_type") or mimetypes.guess_type(video_path.name)[0] or "video/mp4"
    if not file_uri:
        raise SystemExit(f"Gemini file response did not include uri: {file_obj}")

    url = f"{GEMINI_API_BASE}/v1beta/models/{model}:generateContent?key={urllib.parse.quote(api_key)}"
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"fileData": {"mimeType": mime_type, "fileUri": file_uri}},
                {"text": gemini_prompt(mode, question, start, end)},
            ],
        }],
    }
    response = request_json(
        url,
        method="POST",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )
    texts: list[str] = []
    for candidate in response.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if "text" in part:
                texts.append(part["text"])
    return {"model": model, "file": file_obj, "response": response, "text": "\n\n".join(texts).strip()}


def write_outputs(
    out_dir: Path,
    *,
    source: str,
    video_path: Path,
    mode: str,
    question: str | None,
    metadata: dict,
    start: float,
    end: float,
    requested_fps: float,
    effective_fps: float,
    frames: list[FrameInfo],
    sheets: list[str],
    audio_path: str | None,
    gemini: dict | None,
) -> None:
    timeline = {
        "source": source,
        "local_video_path": str(video_path),
        "mode": mode,
        "question": question,
        "metadata": metadata,
        "range": {"start_seconds": start, "end_seconds": end, "start": format_time(start), "end": format_time(end)},
        "frames": {
            "requested_fps": requested_fps,
            "effective_fps": effective_fps,
            "count": len(frames),
            "items": [frame.__dict__ for frame in frames],
        },
        "contact_sheets": sheets,
        "audio": {
            "path": audio_path,
            "metadata": metadata.get("audio", {}),
        },
        "gemini": {
            "model": gemini.get("model") if gemini else None,
            "text": gemini.get("text") if gemini else None,
            "file": gemini.get("file") if gemini else None,
        },
    }
    (out_dir / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")

    lines = [
        "# Video Analysis",
        "",
        f"- Source: `{source}`",
        f"- Local video: `{video_path}`",
        f"- Mode: `{mode}`",
        f"- Duration: {format_time(metadata['duration_seconds'])} ({metadata['duration_seconds']:.2f}s)",
        f"- Range: {format_time(start)} to {format_time(end)}",
        f"- Frames: {len(frames)} at {effective_fps:.3f} fps (requested {requested_fps:.3f})",
        f"- Frame directory: `{out_dir / 'frames'}`",
        f"- Contact sheets: {len(sheets)}",
        f"- Audio: `{audio_path}`" if audio_path else "- Audio: none",
        "",
    ]
    if mode in {"ui-bug", "visual-regression"}:
        lines.extend([
            "## Local Frame Review Checklist",
            "",
            "- Verify Gemini timestamp hints against local frames before reporting them as bugs.",
            "- Check for content under navigation/status bars, dynamic island, toolbars, keyboard, or input accessory.",
            "- Check for ghosted, duplicated, stale, or clipped messages during transitions.",
            "- Check whether newly sent user messages briefly use the wrong style, alignment, width, or role treatment.",
            "- Check for scroll jumps, whole-screen dimming, flicker, clipped text, and animation discontinuities.",
            "",
        ])
    if question:
        lines.extend(["## Question", "", question, ""])
    if gemini and gemini.get("text"):
        lines.extend(["## Gemini Analysis", "", gemini["text"], ""])
    elif gemini is None:
        lines.extend(["## Gemini Analysis", "", "Not run.", ""])
    else:
        lines.extend(["## Gemini Analysis", "", "Gemini returned no text.", ""])
    lines.extend(["## Contact Sheets", ""])
    lines.extend([f"- `{sheet}`" for sheet in sheets] or ["- none"])
    lines.extend(["", "## Audio", ""])
    if audio_path:
        audio = metadata.get("audio", {})
        lines.extend([
            f"- Path: `{audio_path}`",
            f"- Codec: {audio.get('codec') or 'unknown'}",
            f"- Channels: {audio.get('channels') or 'unknown'}",
            f"- Sample rate: {audio.get('sample_rate') or 'unknown'} Hz",
        ])
    else:
        lines.append("- none")
    lines.extend(["", "## Frame Index", ""])
    lines.extend([f"- `{frame.path}` ({frame.timestamp})" for frame in frames[:200]])
    if len(frames) > 200:
        lines.append(f"- ... {len(frames) - 200} more frames in timeline.json")
    (out_dir / "analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a video with Gemini and timestamped local frames.")
    parser.add_argument("source", help="Local video path or public URL")
    parser.add_argument("--mode", choices=["summary", "ui-bug", "visual-regression", "gemini-only", "frame-only"], default="ui-bug")
    parser.add_argument("--question", default=None, help="Question or task for the analysis")
    parser.add_argument("--start", default=None, help="Start time: SS, MM:SS, or HH:MM:SS")
    parser.add_argument("--end", default=None, help="End time: SS, MM:SS, or HH:MM:SS")
    parser.add_argument("--fps", type=float, default=None, help="Local frame extraction FPS")
    parser.add_argument("--max-frames", type=int, default=None, help="Maximum local frames")
    parser.add_argument("--resolution", type=int, default=None, help="Extracted frame width")
    parser.add_argument("--out-dir", default=None, help="Output directory")
    parser.add_argument("--no-gemini", action="store_true", help="Skip Gemini even if a key is available")
    parser.add_argument("--no-audio-extract", action="store_true", help="Skip local audio extraction")
    parser.add_argument("--gemini-model", default=DEFAULT_GEMINI_MODEL, help=f"Gemini model for video analysis (default: {DEFAULT_GEMINI_MODEL})")
    parser.add_argument("--gemini-api-key-env", default="GEMINI_API_KEY,GOOGLE_API_KEY", help="Comma-separated env var names to check")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else default_out_dir(args.source)
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = resolve_source(args.source, out_dir)
    metadata = probe(video_path)

    full_duration = metadata["duration_seconds"]
    start = parse_time(args.start) or 0.0
    end = parse_time(args.end) if args.end else full_duration
    if end <= start:
        raise SystemExit("--end must be greater than --start")
    if full_duration and start >= full_duration:
        raise SystemExit("--start is past the end of the video")
    if full_duration:
        end = min(end, full_duration)

    focused = args.start is not None or args.end is not None
    default_fps, default_max_frames, default_width = choose_defaults(args.mode, focused)
    fps = args.fps if args.fps is not None else default_fps
    max_frames = args.max_frames if args.max_frames is not None else default_max_frames
    width = args.resolution if args.resolution is not None else default_width

    frames: list[FrameInfo] = []
    effective_fps = 0.0
    sheets: list[str] = []
    if args.mode != "gemini-only":
        frames, effective_fps = extract_frames(
            video_path,
            out_dir / "frames",
            start=start,
            end=end,
            fps=fps,
            max_frames=max_frames,
            width=width,
        )
        sheets = make_contact_sheets(out_dir / "frames", out_dir / "contact_sheets", len(frames))

    audio_path = None
    if not args.no_audio_extract:
        audio_path = extract_audio(
            video_path,
            out_dir / "audio",
            start=start,
            end=end,
            has_audio=bool(metadata.get("audio", {}).get("present")),
        )

    gemini = None
    if args.mode != "frame-only" and not args.no_gemini:
        api_key = None
        for name in [part.strip() for part in args.gemini_api_key_env.split(",") if part.strip()]:
            api_key = os.environ.get(name)
            if api_key:
                break
        if api_key:
            gemini = analyze_with_gemini(
                api_key,
                video_path,
                model=args.gemini_model,
                mode=args.mode,
                question=args.question,
                start=start,
                end=end,
            )
        else:
            print("Gemini skipped: no API key found in requested environment variables.", file=sys.stderr)

    write_outputs(
        out_dir,
        source=args.source,
        video_path=video_path,
        mode=args.mode,
        question=args.question,
        metadata=metadata,
        start=start,
        end=end,
        requested_fps=fps,
        effective_fps=effective_fps,
        frames=frames,
        sheets=sheets,
        audio_path=audio_path,
        gemini=gemini,
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
