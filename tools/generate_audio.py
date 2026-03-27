"""
generate_audio.py
=================
Step 1 of the Autonomous Biblical Storytelling Pipeline

PURPOSE:
    Reads a Kokoro-optimized TikTok script, strips all non-TTS content,
    generates a WAV file via Kokoro TTS, and saves it to the correct
    story's assets/audio/ folder.

USAGE:
    python tools/generate_audio.py --story 001_witch_of_endor
    python tools/generate_audio.py --story 001_witch_of_endor --voice af_sarah
    python tools/generate_audio.py --story 001_witch_of_endor --preview

PIPELINE POSITION:
    [generate_audio.py] → generate_images.py → compile_video.py → publish.py

REQUIREMENTS:
    pip install kokoro soundfile numpy
"""

import argparse
import os
import re
import sys
import json
from pathlib import Path
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent  # storytelling/
STORIES_DIR = BASE_DIR / "stories"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PIPELINE_LOG = LOGS_DIR / "pipeline.json"

DEFAULT_VOICE = "am_michael"       # deep, authoritative narrator
DEFAULT_SPEED = 0.92               # slightly slower for drama
SAMPLE_RATE   = 24000              # Kokoro native sample rate

AVAILABLE_VOICES = {
    "am_michael": "Deep male — authoritative narrator (recommended for biblical)",
    "af_sarah":   "Female — eerie, haunting (good for supernatural stories)",
    "am_adam":    "Male — warm, conversational",
    "af_bella":   "Female — warm, clear",
}

# ── SCRIPT PARSER ─────────────────────────────────────────────────────────────

def parse_tts_script(script_path: Path) -> str:
    """
    Extracts only speakable lines from a Kokoro-optimized TikTok script.
    Strips: markdown headers, director notes, hashtags, code blocks,
            text-on-screen markers, and blank lines.
    Converts: [pause] markers into actual silence tokens Kokoro respects (...)
    """
    raw = script_path.read_text(encoding="utf-8")
    lines = raw.splitlines()

    tts_lines = []
    in_code_block   = False
    in_director_block = False

    skip_patterns = [
        r"^#",                          # markdown headers
        r"^\*\*",                       # bold labels like **RUNTIME**
        r"^\[TEXT",                      # [TEXT ON SCREEN:] and [TEXT: "..."] markers
        r"^\[SILENCE:",                 # [SILENCE: X.0] silence injection markers
        r"^>",                          # blockquotes
        r"^---",                        # horizontal rules
        r"^```",                        # code fences (toggle)
        r"^\s*$",                       # blank lines
        r"^##\s",                       # section headers
        r"^\*\[",                       # italicized stage directions
        r"^RUNTIME|^WORD COUNT|^VOICE|^HOOK", # metadata lines
    ]

    for line in lines:
        stripped = line.strip()

        # Toggle code block
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Skip any ## section that isn't FULL SCRIPT; enter TTS-only mode on FULL SCRIPT
        if re.match(r"^## FULL SCRIPT", stripped, re.IGNORECASE):
            in_director_block = False
            continue
        if re.match(r"^## ", stripped, re.IGNORECASE):
            in_director_block = True
            continue
        if in_director_block:
            continue

        # Skip lines matching any pattern
        if any(re.match(pat, stripped) for pat in skip_patterns):
            continue

        # Clean inline markdown
        cleaned = re.sub(r"\*+([^*]+)\*+", r"\1", stripped)  # remove bold/italic
        cleaned = re.sub(r"`[^`]+`", "", cleaned)             # remove inline code
        cleaned = cleaned.strip()

        if not cleaned:
            continue

        # Convert [pause] to "..." for Kokoro natural pause
        cleaned = re.sub(r"\[pause\]", "...", cleaned, flags=re.IGNORECASE)

        tts_lines.append(cleaned)

    full_script = " ".join(tts_lines)

    # Clean up multiple spaces/periods
    full_script = re.sub(r"\.{4,}", "...", full_script)
    full_script = re.sub(r" {2,}", " ", full_script)

    return full_script.strip()


# ── AUDIO GENERATOR ───────────────────────────────────────────────────────────

def generate_audio(story_id: str, voice: str, speed: float, preview: bool = False):
    """
    Main generation function. Reads script, generates WAV, saves to assets/audio/.
    """

    # ── Resolve paths
    story_dir  = STORIES_DIR / story_id
    script_path = story_dir / "script_tiktok.md"
    audio_dir  = story_dir / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{story_id}_tiktok_{voice}_{timestamp}.wav"
    output_path = audio_dir / output_filename

    print(f"\n{'='*60}")
    print(f"  Biblical Storytelling — Audio Generator")
    print(f"{'='*60}")
    print(f"  Story   : {story_id}")
    print(f"  Voice   : {voice} — {AVAILABLE_VOICES.get(voice, 'custom')}")
    print(f"  Speed   : {speed}")
    print(f"  Script  : {script_path}")
    print(f"  Output  : {output_path}")
    print(f"{'='*60}\n")

    # ── Validate script exists
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        print(f"        Run scaffold first or check story ID spelling.")
        sys.exit(1)

    # ── Parse TTS-ready text
    print("[1/4] Parsing script...")
    tts_text = parse_tts_script(script_path)

    if not tts_text:
        print("[ERROR] No speakable text found in script. Check formatting.")
        sys.exit(1)

    word_count = len(tts_text.split())
    est_seconds = round(word_count / (185 * speed) * 60, 1)
    print(f"       Words: {word_count} | Est. runtime: {est_seconds}s")

    # ── Preview mode — just show what would be spoken
    if preview:
        print(f"\n[PREVIEW MODE] TTS text that would be generated:\n")
        print("-" * 60)
        print(tts_text)
        print("-" * 60)
        print("[PREVIEW] No audio generated. Remove --preview to generate.")
        return

    # ── Load Kokoro
    print("[2/4] Loading Kokoro TTS (RTX 4060 GPU acceleration)...")
    try:
        from kokoro import KPipeline
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"[ERROR] Missing dependency: {e}")
        print(f"        Run: pip install kokoro soundfile numpy")
        sys.exit(1)

    try:
        pipe = KPipeline(lang_code="a")  # 'a' = American English
    except Exception as e:
        print(f"[ERROR] Failed to load Kokoro pipeline: {e}")
        sys.exit(1)

    # ── Generate audio
    print("[3/4] Generating audio...")
    try:
        # Kokoro generator yields (graphemes, phonemes, audio) tuples
        audio_chunks = []
        for gs, ps, audio_chunk in pipe(tts_text, voice=voice, speed=speed):
            if audio_chunk is not None:
                audio_chunks.append(audio_chunk)

        if not audio_chunks:
            print("[ERROR] Kokoro returned no audio. Check voice name and input text.")
            sys.exit(1)

        audio = np.concatenate(audio_chunks)

    except Exception as e:
        print(f"[ERROR] Audio generation failed: {e}")
        sys.exit(1)

    # ── Save WAV
    print("[4/4] Saving WAV file...")
    try:
        import soundfile as sf
        sf.write(str(output_path), audio, SAMPLE_RATE)
    except Exception as e:
        print(f"[ERROR] Failed to save WAV: {e}")
        sys.exit(1)

    duration = len(audio) / SAMPLE_RATE
    size_kb = output_path.stat().st_size // 1024

    print(f"\n{'='*60}")
    print(f"  [SUCCESS] Audio generated")
    print(f"  File     : {output_filename}")
    print(f"  Duration : {duration:.1f} seconds")
    print(f"  Size     : {size_kb} KB")
    print(f"  Location : {audio_dir}")
    print(f"{'='*60}\n")

    # ── Log to pipeline.json
    log_entry = {
        "step":      "generate_audio",
        "story_id":  story_id,
        "timestamp": timestamp,
        "voice":     voice,
        "speed":     speed,
        "duration_sec": round(duration, 1),
        "word_count": word_count,
        "output_file": str(output_path),
        "status":    "success"
    }
    append_pipeline_log(log_entry)

    print(f"  Pipeline log updated: {PIPELINE_LOG}")
    print(f"\n  NEXT STEP: python tools/generate_images.py --story {story_id}\n")

    return str(output_path)


# ── PIPELINE LOG ──────────────────────────────────────────────────────────────

def append_pipeline_log(entry: dict):
    """Appends a step result to the shared pipeline log for orchestration tracking."""
    if PIPELINE_LOG.exists():
        try:
            log = json.loads(PIPELINE_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log = []
    else:
        log = []

    log.append(entry)
    PIPELINE_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate Kokoro TTS audio for a biblical storytelling TikTok.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/generate_audio.py --story 001_witch_of_endor
  python tools/generate_audio.py --story 001_witch_of_endor --voice af_sarah
  python tools/generate_audio.py --story 001_witch_of_endor --preview

Available voices:
  am_michael  Deep male narrator      (default — best for biblical)
  af_sarah    Female, eerie           (good for supernatural stories)
  am_adam     Male, warm
  af_bella    Female, warm and clear

Pipeline:
  generate_audio.py → generate_images.py → compile_video.py → publish.py
        """
    )

    parser.add_argument(
        "--story", required=True,
        help="Story folder name, e.g. 001_witch_of_endor"
    )
    parser.add_argument(
        "--voice", default=DEFAULT_VOICE,
        choices=list(AVAILABLE_VOICES.keys()),
        help=f"Kokoro voice model (default: {DEFAULT_VOICE})"
    )
    parser.add_argument(
        "--speed", type=float, default=DEFAULT_SPEED,
        help=f"Speech speed multiplier (default: {DEFAULT_SPEED})"
    )
    parser.add_argument(
        "--preview", action="store_true",
        help="Print parsed TTS text without generating audio"
    )
    parser.add_argument(
        "--list-voices", action="store_true",
        help="List all available voices and exit"
    )

    args = parser.parse_args()

    if args.list_voices:
        print("\nAvailable Kokoro voices:\n")
        for k, v in AVAILABLE_VOICES.items():
            marker = " ← default" if k == DEFAULT_VOICE else ""
            print(f"  {k:<15} {v}{marker}")
        print()
        sys.exit(0)

    generate_audio(
        story_id=args.story,
        voice=args.voice,
        speed=args.speed,
        preview=args.preview
    )


if __name__ == "__main__":
    main()