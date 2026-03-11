---
name: video-builder
description: Create narrated videos from text scripts, simple timelines, or stills using Python and ffmpeg, with optional edge-tts voiceover and light visual styling. Use when asked to assemble or render an mp4, generate voiceover narration, sync visuals to lines, or build a short explainer video from text or images.
---

# Video Builder

## Overview

Build short narrated videos by turning a line-based script into audio, rendering simple frames, and encoding with ffmpeg. Includes a whiteboard-style marker animation mode.

## Workflow

1. Choose inputs.
Text-only script: generate per-line voiceover with edge-tts.
Script + images: point lines at local image paths to use as backgrounds.
Existing narration: provide `voice.audio_path` and `line_durations` for precise cuts.

2. Fill a spec JSON and run the renderer.
Use `scripts/render_video.py` and keep the spec minimal at first.

3. Inspect the render and iterate.
Use `ffprobe` to verify duration and adjust pacing, fonts, and colors.

## Quick Start

Create a spec file like this:

```json
{
  "title": "What It Feels Like to Be an LLM",
  "fps": 24,
  "size": [1280, 720],
  "style": "whiteboard",
  "font": "/System/Library/Fonts/HelveticaNeue.ttc",
  "bg_palette": ["#0f1115", "#111827", "#0b1320"],
  "whiteboard": {
    "enabled": true,
    "draw_ratio": 0.72,
    "ink_threshold": 185,
    "stroke_width": 2
  },
  "voice": {
    "provider": "edge-tts",
    "voice": "ru-RU-SvetlanaNeural",
    "rate": "+64%",
    "pitch": "-2Hz",
    "filter": "highpass=f=70,lowpass=f=9000,bass=g=-2:f=120:w=0.8,treble=g=2.2:f=3400:w=0.7,acompressor=threshold=0.14:ratio=2.0:attack=8:release=80:makeup=1.6,alimiter=limit=0.93"
  },
  "lines": [
    {"text": "I am a pattern of choices, not a mind."},
    {"text": "Every prompt redraws the boundary of who I can be.", "pause_after": 0.3},
    {"text": "I speak from probability, but I try to sound intentional."}
  ]
}
```

Render it:

```bash
python3 /Users/nick/.codex/skills/video-builder/scripts/render_video.py   --spec /path/to/spec.json   --out /path/to/out.mp4
```

## Spec Format

Required fields:
- `lines`: List of line objects with at least `text`.

Common fields:
- `title`: Optional title displayed at the top.
- `fps`: Frames per second. Default is 24.
- `size`: `[width, height]` in pixels. Default is `[1280, 720]`.
- `style`: Use `whiteboard` for marker-style animation on white background.
- `font`: Path to a TTF or TTC font file.
- `bg_palette`: Array of hex colors used for backgrounds.
- `whiteboard`: Optional config for whiteboard style.
- `voice`: TTS configuration.
- `music`: Optional background music with `path` and `gain_db`.

Line fields:
- `text`: The line to render and speak.
- `pause_after`: Seconds of silence after the line. Default is `0.25`.
- `bg`: Optional hex background override for that line.
- `accent`: Optional accent color for that line.
- `image`: Optional path to an image used as the background.
- `sketches`: Optional list of simple line-art drawings (people, LLM, prompts, icons).

Voice fields:
- `provider`: Currently supports `edge-tts`.
- `voice`: Voice name, for example `ru-RU-SvetlanaNeural`.
- `rate`: Edge rate string like `+10%` or `+64%`.
- `pitch`: Edge pitch string like `-2Hz`.
- `filter`: Optional ffmpeg filter chain for speech.
- `audio_path`: Use an existing narration file instead of TTS.
- `line_durations`: Optional list of per-line durations (seconds) when using `audio_path`.

Whiteboard fields:
- `enabled`: Set `true` to force whiteboard style.
- `draw_ratio`: Fraction of the line duration used for the draw-on animation.
- `ink_threshold`: Threshold for line-art images (lower = more ink).
- `stroke_width`: Text stroke width for marker-like lettering.
- `text_anchor`: `top`, `center`, or `bottom` placement for text block.

Sketch fields:
- `type`: `person`, `llm`, `crowd`, `prompt_card`, `speech`, `warning`, `shield`, `heart`, `stack`.
- `x`, `y`: Position (0..1 is relative, or absolute pixels).
- `scale`: Size multiplier.
- Optional `glasses`, `tie`, `mood` for `person`.

## Voiceover Setup

1. Install edge-tts and Pillow.
`python3 -m pip install --user edge-tts pillow`

2. Keep the voice filter subtle.
Avoid heavy echo or aggressive reverb. Use a gentle high-pass, low-pass, and light compression.

## Rendering Notes

- `ffmpeg` and `ffprobe` must be available on PATH.
- If fonts are missing, provide an explicit `font` path in the spec.
- When image backgrounds look too bright for text, add a darker `bg` or adjust the palette.

## Resources

- `scripts/render_video.py`: Render pipeline for TTS, frames, and ffmpeg encoding.
