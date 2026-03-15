---
name: video-spec-builder
description: Build a minimal JSON render spec for the local video pipeline from script lines, still images, or narration assets. Use when the spec artifact must exist before any MP4 render can run.
---

# Video Spec Builder

## Metadata
- Trigger when: the user has script lines, images, or narration assets and needs a clean render spec before rendering.
- Do not use when: a spec JSON already exists and the real job is running the renderer.

## Skill Purpose

Turn raw video inputs into one minimal, explicit JSON spec that the renderer can execute without guesswork.

## Instructions
1. Gather the smallest honest input mode first: text plus TTS, script plus image backgrounds, or existing narration plus explicit timing. Lock the required asset paths before writing anything.
2. Write a minimal JSON spec with explicit size, fps, voice/input mode, and line structure. Keep the first spec lean instead of anticipating every future tweak.
3. Validate the spec: confirm referenced files exist, required fields are explicit, and the next rendering command is obvious. If the spec is ready, hand off to `$video-render-run`.

## Non-Negotiable Acceptance Criteria
- The spec is minimal but complete enough for the renderer to run.
- Asset paths, timing assumptions, and narration mode are explicit.
- The skill does not render the video itself; it stops at the spec artifact.
- If key assets or timing inputs are missing, the blocker is stated directly.

## Output
- The spec JSON path.
- A short note on the chosen input mode and required assets.
- `Next skill options` (only if needed): `$video-render-run` — render and validate the MP4 from this spec.
