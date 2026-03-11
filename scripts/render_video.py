#!/usr/bin/env python3
"""
Render a simple narrated video from a JSON spec.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow is required. Install with: python3 -m pip install --user pillow"
    ) from exc

try:
    import edge_tts
except ImportError:
    edge_tts = None

DEFAULT_FPS = 24
DEFAULT_SIZE = (1280, 720)
DEFAULT_PAUSE = 0.25
DEFAULT_VOICE = "ru-RU-SvetlanaNeural"
DEFAULT_RATE = "+0%"
DEFAULT_PITCH = "+0Hz"
DEFAULT_FILTER = ""
DEFAULT_BG = "#0f1115"
DEFAULT_ACCENT = "#60a5fa"
DEFAULT_PALETTE = ["#0f1115", "#111827", "#0b1320", "#0a0f1a"]

FONT_CANDIDATES = [
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]


def run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def run_capture(cmd: List[str]) -> str:
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()


def require_tool(tool: str) -> None:
    if shutil.which(tool) is None:
        raise SystemExit(f"Missing dependency: {tool} (not found on PATH)")


def parse_color(value: Optional[str], fallback: str) -> Tuple[int, int, int]:
    text = (value or fallback).lstrip("#")
    if len(text) != 6:
        text = fallback.lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def resolve_font_path(path: Optional[str]) -> Optional[str]:
    if path and Path(path).exists():
        return path
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def load_font(path: Optional[str], size: int) -> ImageFont.FreeTypeFont:
    resolved = resolve_font_path(path)
    if resolved:
        return ImageFont.truetype(resolved, size=size)
    return ImageFont.load_default()


def ffprobe_duration(path: Path) -> float:
    output = run_capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ]
    )
    try:
        return float(output)
    except ValueError:
        raise SystemExit(f"Unable to read duration for {path}")


async def tts_to_mp3(text: str, voice: str, rate: str, pitch: str, out_path: Path) -> None:
    if edge_tts is None:
        raise SystemExit(
            "edge-tts is required for TTS. Install with: python3 -m pip install --user edge-tts"
        )
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


def render_line_image(
    line: Dict[str, Any],
    size: Tuple[int, int],
    font_path: Optional[str],
    title: Optional[str],
    palette: List[str],
    index: int,
    total: int,
) -> Image.Image:
    width, height = size
    bg_color = parse_color(line.get("bg"), palette[index % len(palette)] if palette else DEFAULT_BG)
    accent_color = parse_color(line.get("accent"), DEFAULT_ACCENT)

    image_path = line.get("image")
    if image_path and Path(image_path).exists():
        base = Image.open(image_path).convert("RGB")
        base = ImageOps.fit(base, size, centering=(0.5, 0.5))
        overlay = Image.new("RGBA", size, (0, 0, 0, 120))
        img = Image.alpha_composite(base.convert("RGBA"), overlay).convert("RGB")
    else:
        img = Image.new("RGB", size, bg_color)

    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width, 6], fill=accent_color)

    title_font = load_font(font_path, size=int(height * 0.05))
    body_font = load_font(font_path, size=int(height * 0.06))

    if title:
        title_box = draw.textbbox((0, 0), title, font=title_font)
        title_x = (width - (title_box[2] - title_box[0])) / 2
        draw.text((title_x, height * 0.08), title, font=title_font, fill=(220, 224, 235))

    text = line.get("text", "").strip()
    wrap_width = max(20, int(width / (body_font.size * 0.55)))
    wrapped = textwrap.fill(text, width=wrap_width)
    text_box = draw.multiline_textbbox((0, 0), wrapped, font=body_font, spacing=6)
    text_w = text_box[2] - text_box[0]
    text_h = text_box[3] - text_box[1]
    text_x = (width - text_w) / 2
    text_y = (height - text_h) / 2
    draw.multiline_text(
        (text_x, text_y),
        wrapped,
        font=body_font,
        fill=(235, 238, 245),
        spacing=6,
        align="center",
    )

    counter = f"{index + 1}/{total}"
    counter_font = load_font(font_path, size=int(height * 0.03))
    counter_box = draw.textbbox((0, 0), counter, font=counter_font)
    counter_x = width - (counter_box[2] - counter_box[0]) - width * 0.05
    counter_y = height - (counter_box[3] - counter_box[1]) - height * 0.06
    draw.text((counter_x, counter_y), counter, font=counter_font, fill=(140, 150, 170))

    return img


def build_audio(
    lines: List[Dict[str, Any]],
    audio_dir: Path,
    voice_cfg: Dict[str, Any],
) -> Tuple[Path, List[float]]:
    require_tool("ffmpeg")
    require_tool("ffprobe")

    audio_dir.mkdir(parents=True, exist_ok=True)
    durations: List[float] = []

    audio_path = voice_cfg.get("audio_path")
    line_durations = voice_cfg.get("line_durations")
    if audio_path:
        source = Path(audio_path)
        if not source.exists():
            raise SystemExit(f"voice.audio_path not found: {source}")
        output = audio_dir / "final_mix.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-ac",
                "1",
                "-ar",
                "48000",
                str(output),
            ]
        )
        if line_durations:
            durations = [float(value) for value in line_durations]
        else:
            total = ffprobe_duration(output)
            per = total / max(1, len(lines))
            durations = [per for _ in lines]
        return output, durations

    voice = voice_cfg.get("voice", DEFAULT_VOICE)
    rate = voice_cfg.get("rate", DEFAULT_RATE)
    pitch = voice_cfg.get("pitch", DEFAULT_PITCH)
    filter_chain = voice_cfg.get("filter", DEFAULT_FILTER)

    for index, line in enumerate(lines, start=1):
        mp3_path = audio_dir / f"line_{index:02d}.mp3"
        wav_path = audio_dir / f"line_{index:02d}.wav"
        asyncio.run(tts_to_mp3(line["text"], voice, rate, pitch, mp3_path))
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            "48000",
        ]
        if filter_chain:
            cmd += ["-af", filter_chain]
        cmd.append(str(wav_path))
        run(cmd)
        durations.append(ffprobe_duration(wav_path))

    concat_list = audio_dir / "concat.txt"
    silence_paths: List[Path] = []
    with concat_list.open("w") as handle:
        for index, line in enumerate(lines, start=1):
            wav_path = audio_dir / f"line_{index:02d}.wav"
            handle.write(f"file '{wav_path.as_posix()}'\n")
            pause = float(line.get("pause_after", DEFAULT_PAUSE))
            if pause > 0:
                silence_path = audio_dir / f"silence_{index:02d}.wav"
                silence_paths.append(silence_path)
                run(
                    [
                        "ffmpeg",
                        "-y",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-t",
                        f"{pause:.3f}",
                        "-i",
                        "anullsrc=channel_layout=mono:sample_rate=48000",
                        str(silence_path),
                    ]
                )
                handle.write(f"file '{silence_path.as_posix()}'\n")

    narration = audio_dir / "narration.wav"
    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-ac",
            "1",
            "-ar",
            "48000",
            str(narration),
        ]
    )

    music = voice_cfg.get("music")
    if music and Path(music["path"]).exists():
        mixed = audio_dir / "final_mix.wav"
        gain = float(music.get("gain_db", -18))
        run(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-i",
                str(narration),
                "-i",
                str(music["path"]),
                "-filter_complex",
                f"[1:a]volume={gain}dB[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2",
                "-ac",
                "1",
                "-ar",
                "48000",
                str(mixed),
            ]
        )
        return mixed, durations

    return narration, durations


def render_video(spec: Dict[str, Any], out_path: Path, workdir: Path) -> None:
    require_tool("ffmpeg")
    require_tool("ffprobe")

    fps = int(spec.get("fps", DEFAULT_FPS))
    size = tuple(spec.get("size", DEFAULT_SIZE))
    title = spec.get("title")
    font_path = spec.get("font")
    palette = spec.get("bg_palette", DEFAULT_PALETTE)
    lines = spec.get("lines", [])

    if not lines:
        raise SystemExit("Spec must include a non-empty 'lines' array.")

    frames_dir = workdir / "frames"
    audio_dir = workdir / "audio"
    frames_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    voice_cfg = spec.get("voice", {})
    music_cfg = spec.get("music")
    if music_cfg:
        voice_cfg = dict(voice_cfg)
        voice_cfg["music"] = music_cfg

    audio_path, durations = build_audio(lines, audio_dir, voice_cfg)

    frame_index = 0
    total_lines = len(lines)
    for idx, line in enumerate(lines):
        duration = durations[idx] if idx < len(durations) else DEFAULT_PAUSE
        frame_count = max(1, int(math.ceil(duration * fps)))
        img = render_line_image(
            line=line,
            size=size,
            font_path=font_path,
            title=title if idx == 0 else None,
            palette=palette,
            index=idx,
            total=total_lines,
        )
        for _ in range(frame_count):
            frame_path = frames_dir / f"frame_{frame_index:05d}.png"
            img.save(frame_path)
            frame_index += 1

    run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame_%05d.png"),
            "-i",
            str(audio_path),
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "medium",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_path),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a narrated video from a JSON spec.")
    parser.add_argument("--spec", required=True, help="Path to JSON spec file.")
    parser.add_argument("--out", required=True, help="Output mp4 path.")
    parser.add_argument(
        "--workdir",
        help="Working directory for frames/audio (default: <spec_dir>/build_video).",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec).expanduser().resolve()
    if not spec_path.exists():
        raise SystemExit(f"Spec file not found: {spec_path}")

    with spec_path.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)

    workdir = Path(args.workdir).expanduser().resolve() if args.workdir else spec_path.parent / "build_video"
    out_path = Path(args.out).expanduser().resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    render_video(spec, out_path, workdir)


if __name__ == "__main__":
    main()
