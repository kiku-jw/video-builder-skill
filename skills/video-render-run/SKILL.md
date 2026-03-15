---
name: video-render-run
description: Render and validate an MP4 from an existing `video-builder` spec JSON using the bundled Python pipeline. Use when a spec already exists and the job is actual rendering, not story or spec design.
---

# Video Render Run

## Metadata
- Trigger when: a video spec JSON already exists and the task is to render and verify output.
- Do not use when: the user still needs help designing the spec or choosing the input mode.

## Skill Purpose

Take an existing spec, run the renderer deterministically, and validate the resulting MP4 instead of mixing render execution with preproduction planning.

## Instructions
1. Verify the spec path, required assets, fonts, and `ffmpeg` plus `ffprobe` availability before running the pipeline.
2. Render with `/Users/nick/.codex/skills/video-builder/scripts/render_video.py` using `python3 /Users/nick/.codex/skills/video-builder/scripts/render_video.py --spec /absolute/path/to/spec.json --out /absolute/path/to/out.mp4`.
3. Validate the MP4 with `ffprobe` or equivalent playback checks. Confirm duration, pacing, narration alignment, and whether the render is ready or needs one targeted fix.

## Non-Negotiable Acceptance Criteria
- A real spec path exists before rendering starts.
- Missing dependencies, fonts, or assets are reported directly.
- Validation covers output existence plus playback sanity, not just command success.
- The skill does not silently rewrite the spec unless the task explicitly asked for repair.

## Output
- The spec path and rendered MP4 path.
- A short validation note on duration, pacing, narration alignment, and any blocker.
- `Next skill options` (only if needed): `$video-spec-builder` — repair or rebuild the spec when the current spec is incomplete or wrong.
