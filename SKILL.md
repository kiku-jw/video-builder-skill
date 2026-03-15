---
name: video-builder
description: Create short narrated videos from text scripts, simple timelines, or still images using Python and ffmpeg, with optional edge-tts voiceover. Use when the user asks for an MP4 render, narration generation, or a simple explainer video build.
---

# Video Builder

## Metadata
- Trigger when: the task is to render a short narrated or slide-like video from script or still assets.
- Do not use when: the user only wants storyboarding or copywriting with no actual render pipeline involved.

## Skill Purpose

Stay as the entrypoint for video work, then route into the narrowest lane: build a clean render spec or run the renderer from an existing spec.

## Instructions
1. Classify the request first. If the user needs help turning script/assets into a minimal JSON spec, prefer `$video-spec-builder`. If the user already has a spec and needs an actual render, prefer `$video-render-run`.
2. If a child lane is unavailable in the current run, continue here with the same split: first define the smallest honest spec, then render it with `/Users/nick/.codex/skills/video-builder/scripts/render_video.py` using `python3 /Users/nick/.codex/skills/video-builder/scripts/render_video.py --spec /absolute/path/to/spec.json --out /absolute/path/to/out.mp4`.
3. Validate the render with `ffprobe` or an equivalent playback check. Confirm duration, pacing, narration alignment, font availability, and whether the output needs one targeted iteration or is ready to ship.

## Non-Negotiable Acceptance Criteria
- `ffmpeg` and `ffprobe` must be available, or the missing dependency is stated clearly.
- The first render starts from a minimal spec instead of a giant kitchen-sink configuration.
- Voice mode, narration timing, and output size are explicit.
- If fonts or narration assets are missing, the skill says so instead of silently substituting broken defaults.

## Output
- The spec path and rendered video path.
- The narration mode used: edge-tts or existing audio.
- A short validation note on duration, pacing, and any needed follow-up tweak.
- `Next skill options` (only if needed): `$video-spec-builder` — turn script/assets into a minimal render spec; `$video-render-run` — render and validate an MP4 from an existing spec.
