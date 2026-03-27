# CLAUDE.md — Project Instructions

## Project: Biblical Storytelling Channel
**Directory:** C:\Users\jcoul\Desktop\storytelling
**Purpose:** TikTok-first biblical storytelling channel focused on
little-known and underexplored Bible stories. 3-minute videos.
**Platform Priority:** TikTok first → YouTube Shorts second → YouTube long-form later

---

## Current Pipeline (v2 — Fully Automated)generate_audio.py     — Kokoro TTS local (RTX 4060)
add_sfx.py            — Music bed + silence injection
generate_images.py    — ComfyUI SDXL local (RTX 4060)
compile_video.py      — ffmpeg Ken Burns + text overlays + variable timing
run_pipeline.py       — Single command orchestrator

Run a full story end to end:
    python tools/run_pipeline.py --story 002_elijah_still_small_voice

---

## Hardware
- GPU: RTX 4060 8GB VRAM
- OS: Windows 11
- ComfyUI: C:\Users\jcoul\Documents\Dev\ComfyUI
- ComfyUI model: juggernautXL_ragnarokBy.safetensors
- Storytelling venv: C:\Users\jcoul\Desktop\storytelling\venv
- ComfyUI venv: C:\Users\jcoul\Documents\Dev\ComfyUI\venv
- ffmpeg: C:\ProgramData\chocolatey\bin\ffmpeg.EXE

## Two Terminals Always Required
- Terminal 1: ComfyUI server (its own venv)
- Terminal 2: Storytelling pipeline (storytelling venv)

---

## Content Rules
- KJV primary, ESV secondary — always cite scripture reference
- Storytelling-first — never lecture style
- Biblically accurate — no speculation presented as fact
- Label extra-biblical context as "historical context" or "tradition holds"
- Hook within first 3 seconds — question or broken promise format
- Comment bait line on every video — one unresolved provocative truth
- Series hook at end of every video — tease next story by name

---

## Script Format — Required Markers[pause]              Kokoro natural breath (~0.3s) → converted to ...
[SILENCE: 1.0]       Real silence injected in audio + subtracted from timing
[TEXT: "line"]       Burned onto video frame for 2.5s at that position

Full marker reference: templates/script_template.md

---

## Kokoro TTS Rules (CRITICAL)
- NEVER use phonetic respellings (SAY-myu-el, Gil-BOH-ah, En-DOR)
  Kokoro reads real words better than approximations
- ALL CAPS can sound robotic — use sparingly for emphasis only
- No accented characters (é, ā, ō) — plain ASCII only
- No semicolons, em-dashes, or parentheses — Kokoro stumbles on these
- Max 15 words per sentence
- Default voice: am_michael, speed: 0.92

---

## Video Specs
- Format: 1080x1920 vertical (TikTok 9:16)
- FPS: 30
- Runtime target: 3 minutes (~180 seconds)
- Scenes: 30 per story
- Image size: 768x768 (SDXL optimized for 4060 8GB)

## Variable Timing (compile_video.py)
- Scenes 1-5:   2.5s  (hook — fast cuts signal active content)
- Scenes 6-20:  4.5s  (build — medium pacing)
- Scenes 21-30: 7.0s  (climax — slow, earned weight)

---

## Audio Stack
- Layer 1: Kokoro narration WAV (generate_audio.py)
- Layer 2: Music bed MP3 at 15% volume with 3s fade in/out (add_sfx.py)
- Layer 3: Silence injection via [SILENCE: X.0] markers (add_sfx.py)
- Music files go in: stories/{story_id}/assets/music/
- Mixed output: assets/audio/{story_id}_mixed_{timestamp}.wav

---

## Image Style (apply to every prompt)
biblical epic oil painting, Rembrandt chiaroscuro lighting,
cinematic composition, photorealistic painting, masterwork quality,
deep shadows, warm amber and gold tones, sacred and austere atmosphere

Negative prompt (always include):
modern clothing, fantasy aesthetic, Halloween witch, cartoon, anime,
watermark, text, logo, low quality, blurry, extra limbs,
deformed hands, medieval European architecture, carved stone reliefs

---

## Story Naming Convention
001_witch_of_endor
002_elijah_still_small_voice
003_nephilim
004_story_name

---

## Stories
- [x] 001 — The Witch of Endor (1 Samuel 28) — COMPLETE — POSTED
- [ ] 002 — Elijah and the Still Small Voice (1 Kings 18-19) — IN PROGRESS
- [ ] 003 — The Nephilim (Genesis 6) — QUEUED
- [ ] 004 — The Hand Writing on the Wall (Daniel 5) — QUEUED
- [ ] 005 — Ananias and Sapphira (Acts 5) — QUEUED
- [ ] 006 — Jezebel's End (2 Kings 9) — QUEUED

---

## TikTok Engagement Rules
- Hook format: question or broken promise — never a statement
- First 5 scenes: fast cuts (2.5s) — signal active content to algorithm
- Comment bait: one unresolved provocative truth at the end
- Series hook: tease next story by mystery not by title
- Captions: always on — verify biblical names after auto-caption

---

## Pipeline Log
All steps log to: logs/pipeline.json
Orchestrator reads this to skip completed steps automatically.
Use --force to re-run a completed step.
Use --from generate_images to resume from a specific step.

---

## Key Lessons Learned
See lessons.md for full history. Critical entries:

1. KOKORO: Never phonetic respellings. Real words only.
2. AUDIO: Kokoro returns (graphemes, phonemes, audio) tuples — unpack correctly.
3. WINDOWS: All paths passed to ffmpeg must use forward slashes.
4. COMFYUI: Checkpoint name must match exactly — case sensitive filename.
5. PARSER: Script parser strips all ## sections except ## FULL SCRIPT.
6. IMAGES: 30 scenes needed for 3-min video at variable timing.
7. CHARACTER: Repeat character descriptors across scenes for consistency.
8. UNICODE: Use sys.stdout.reconfigure(encoding='utf-8') in all tool scripts.