"""
add_sfx.py
==========
Step 2 of the Autonomous Biblical Storytelling Pipeline

PURPOSE:
    Takes the raw Kokoro TTS WAV and produces a mixed WAV with:
    - [SILENCE: X.0] markers from script_tiktok.md injected as silence gaps
    - Optional music bed at volume 0.15, fading in/out over 3 seconds
    Output is what compile_video.py uses as its audio source.

USAGE:
    python tools/add_sfx.py --story 001_witch_of_endor
    python tools/add_sfx.py --story 001_witch_of_endor --music assets/music/drone.mp3
    python tools/add_sfx.py --story 001_witch_of_endor --no-music

PIPELINE POSITION:
    generate_audio.py -> [add_sfx.py] -> generate_images.py -> compile_video.py

REQUIREMENTS:
    pip install pydub
    ffmpeg on PATH (pydub uses it for MP3 decode)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parent.parent
STORIES_DIR  = BASE_DIR / "stories"
LOGS_DIR     = BASE_DIR / "logs"
PIPELINE_LOG = LOGS_DIR / "pipeline.json"

MUSIC_VOLUME     = 0.15    # music bed level relative to full
FADE_DURATION_MS = 3000    # 3 second fade in/out on music bed


# ── LOG HELPERS ────────────────────────────────────────────────────────────────

def read_log() -> list:
    if PIPELINE_LOG.exists():
        try:
            return json.loads(PIPELINE_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def append_pipeline_log(entry: dict):
    log = read_log()
    log.append(entry)
    PIPELINE_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


def get_latest_raw_audio(story_id: str) -> Path | None:
    """Returns the most recent successful generate_audio output path."""
    log = read_log()
    for entry in reversed(log):
        if (entry.get("step") == "generate_audio"
                and entry.get("story_id") == story_id
                and entry.get("status") == "success"
                and entry.get("output_file")):
            p = Path(entry["output_file"])
            if p.exists():
                return p
    return None


# ── SCRIPT PARSER ─────────────────────────────────────────────────────────────

def parse_silence_markers(script_path: Path) -> list[dict]:
    """
    Parses [SILENCE: X.0] markers from script_tiktok.md in order.
    Returns list of {"duration_ms": int, "position": n} dicts.
    Position is 0-indexed order of appearance in the script.
    """
    if not script_path.exists():
        return []
    text = script_path.read_text(encoding="utf-8")
    markers = []
    for match in re.finditer(r'\[SILENCE:\s*([\d.]+)\]', text):
        markers.append({
            "duration_ms": int(float(match.group(1)) * 1000),
            "position":    len(markers)
        })
    return markers


# ── AUDIO PROCESSING ──────────────────────────────────────────────────────────

def inject_silences(narration, silence_markers: list[dict]):
    """
    Distributes silence gaps evenly through the narration audio.
    Each marker inserts its duration of silence at an evenly-spaced position.
    Returns the modified AudioSegment.
    """
    from pydub import AudioSegment

    if not silence_markers:
        return narration

    n = len(silence_markers)
    total_ms = len(narration)
    # Evenly space insertion points across the original narration
    segment_ms = total_ms // (n + 1)

    result = AudioSegment.empty()
    prev_end = 0

    for i, marker in enumerate(silence_markers):
        cut_point = segment_ms * (i + 1)
        cut_point = min(cut_point, total_ms)
        result += narration[prev_end:cut_point]
        result += AudioSegment.silent(duration=marker["duration_ms"])
        prev_end = cut_point

    result += narration[prev_end:]
    return result


def apply_music_bed(narration, music_path: Path):
    """
    Layers a music bed under narration:
    - Music looped/trimmed to match narration length
    - Volume reduced to MUSIC_VOLUME (15%)
    - Fade in over FADE_DURATION_MS, fade out over FADE_DURATION_MS
    Returns the mixed AudioSegment.
    """
    from pydub import AudioSegment

    music_raw = AudioSegment.from_file(str(music_path))
    target_ms = len(narration)

    # Loop music until it's long enough
    loops_needed = (target_ms // len(music_raw)) + 2
    music_looped = music_raw * loops_needed
    music_trimmed = music_looped[:target_ms]

    # Reduce volume
    music_bed = music_trimmed - (20 * (1 - MUSIC_VOLUME))   # dB reduction

    # Fade in/out — cap fade to half the track length
    actual_fade = min(FADE_DURATION_MS, target_ms // 2)
    music_bed = music_bed.fade_in(actual_fade).fade_out(actual_fade)

    # Mix: narration stays full volume, music underneath
    return narration.overlay(music_bed)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def add_sfx(story_id: str, music_override: str | None, no_music: bool):
    from pydub import AudioSegment

    story_dir  = STORIES_DIR / story_id
    audio_dir  = story_dir / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    script_path = story_dir / "script_tiktok.md"
    timestamp   = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = audio_dir / f"{story_id}_mixed_{timestamp}.wav"

    print(f"\n{'='*60}")
    print(f"  Biblical Storytelling -- SFX / Music Mixer")
    print(f"{'='*60}")
    print(f"  Story  : {story_id}")
    print(f"  Output : {output_path.name}")
    print(f"{'='*60}\n")

    # ── Locate raw narration
    print("[1/4] Locating raw narration from pipeline log...")
    raw_path = get_latest_raw_audio(story_id)
    if not raw_path:
        print("[ERROR] No successful generate_audio entry found.")
        print(f"        Run: python tools/generate_audio.py --story {story_id}")
        sys.exit(1)
    print(f"       Narration: {raw_path.name}")

    # ── Parse silence markers
    print("[2/4] Parsing silence markers from script...")
    silence_markers = parse_silence_markers(script_path)
    total_silence_ms = sum(m["duration_ms"] for m in silence_markers)
    if silence_markers:
        print(f"       {len(silence_markers)} markers — {total_silence_ms/1000:.1f}s total silence")
    else:
        print(f"       No [SILENCE: X.0] markers found — skipping injection")

    # ── Resolve music file
    music_path = None
    if not no_music:
        if music_override:
            p = Path(music_override)
            if not p.is_absolute():
                p = BASE_DIR / p
            if p.exists():
                music_path = p
            else:
                print(f"[WARN] Music file not found: {p}")
        else:
            # Auto-detect: first MP3/WAV in assets/music/
            music_dir = story_dir / "assets" / "music"
            if not music_dir.exists():
                music_dir = BASE_DIR / "assets" / "music"
            candidates = sorted(music_dir.glob("*.mp3")) + sorted(music_dir.glob("*.wav")) if music_dir.exists() else []
            if candidates:
                music_path = candidates[0]

    if music_path:
        print(f"       Music: {music_path.name} (volume {int(MUSIC_VOLUME*100)}%)")
    else:
        print(f"\n[MUSIC] No music file found at assets/music/")
        print(f"[MUSIC] Add an MP3 there and re-run, or use --music path/to/file.mp3")
        print(f"[MUSIC] Continuing without music bed.\n")

    # ── Load and process audio
    print("[3/4] Processing audio...")
    narration = AudioSegment.from_file(str(raw_path))
    print(f"       Raw narration: {len(narration)/1000:.1f}s")

    if silence_markers:
        narration = inject_silences(narration, silence_markers)
        print(f"       After silence injection: {len(narration)/1000:.1f}s")

    if music_path:
        narration = apply_music_bed(narration, music_path)
        print(f"       Music bed applied")

    # ── Export
    print("[4/4] Exporting mixed WAV...")
    narration.export(str(output_path), format="wav")

    duration_sec = len(narration) / 1000.0
    size_kb = output_path.stat().st_size // 1024

    print(f"\n{'='*60}")
    print(f"  [SUCCESS] Mixed audio exported")
    print(f"  File     : {output_path.name}")
    print(f"  Duration : {duration_sec:.1f}s")
    print(f"  Size     : {size_kb} KB")
    print(f"  Location : {audio_dir}")
    print(f"{'='*60}\n")

    append_pipeline_log({
        "step":           "add_sfx",
        "story_id":       story_id,
        "timestamp":      timestamp,
        "input_file":     str(raw_path),
        "music_file":     str(music_path) if music_path else None,
        "silence_count":  len(silence_markers),
        "silence_sec":    round(total_silence_ms / 1000, 1),
        "duration_sec":   round(duration_sec, 1),
        "output_file":    str(output_path),
        "status":         "success"
    })

    print(f"  Pipeline log updated: {PIPELINE_LOG}")
    print(f"\n  NEXT STEP: python tools/generate_images.py --story {story_id}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Mix music bed and silence gaps into Kokoro TTS narration.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/add_sfx.py --story 001_witch_of_endor
  python tools/add_sfx.py --story 001_witch_of_endor --music assets/music/drone.mp3
  python tools/add_sfx.py --story 001_witch_of_endor --no-music

Pipeline:
  generate_audio.py -> [add_sfx.py] -> generate_images.py -> compile_video.py
        """
    )
    parser.add_argument("--story",    required=True, help="Story folder name, e.g. 001_witch_of_endor")
    parser.add_argument("--music",    default=None,  help="Path to music MP3/WAV (overrides auto-detect)")
    parser.add_argument("--no-music", action="store_true", help="Skip music bed, only inject silences")

    args = parser.parse_args()
    add_sfx(story_id=args.story, music_override=args.music, no_music=args.no_music)


if __name__ == "__main__":
    main()
