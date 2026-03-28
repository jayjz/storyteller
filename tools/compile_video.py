"""
compile_video.py
================
Step 3 of the Autonomous Biblical Storytelling Pipeline

PURPOSE:
    Reads the latest audio path from logs/pipeline.json, sorts scene PNGs
    from assets/images/ in scene order (S01, S02A, S02B...), and produces
    a 1080x1920 vertical TikTok MP4 with Ken Burns zoom on each image.

    Features:
    - Variable clip timing: fast cuts (hook), medium (build), slow (climax)
    - [SILENCE: X.0] injection: pauses in audio are baked into pacing
    - Clean output for CapCut caption workflow

USAGE:
    python tools/compile_video.py --story 001_witch_of_endor
    python tools/compile_video.py --story 001_witch_of_endor --fps 30
    python tools/compile_video.py --story 001_witch_of_endor --dry-run

PIPELINE POSITION:
    add_sfx.py -> generate_images.py -> [compile_video.py]

REQUIREMENTS:
    ffmpeg must be on PATH (Windows: winget install ffmpeg or via gyan.dev)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parent.parent
STORIES_DIR  = BASE_DIR / "stories"
LOGS_DIR     = BASE_DIR / "logs"
PIPELINE_LOG = LOGS_DIR / "pipeline.json"

OUTPUT_W = 1080
OUTPUT_H = 1920
ZOOM_CANVAS_W = OUTPUT_W * 2   # 2160
ZOOM_CANVAS_H = OUTPUT_H * 2   # 3840
ZOOM_MAX = 1.18


# ── SCENE SORT KEY ─────────────────────────────────────────────────────────────

def scene_sort_key(path: Path) -> tuple:
    """
    Sorts scene_S01.png < scene_S02A.png < scene_S02B.png < scene_S03.png
    Returns (numeric_part, letter_part) e.g. (1,''), (2,'A'), (2,'B'), (3,'')
    """
    m = re.search(r"S(\d+)([A-Z]?)", path.stem, re.IGNORECASE)
    if not m:
        return (9999, "")
    return (int(m.group(1)), m.group(2).upper())


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


def get_latest_audio(story_id: str) -> tuple[Path, float] | tuple[None, None]:
    """
    Prefers the most recent successful add_sfx (mixed) output for this story.
    Falls back to the most recent successful generate_audio (raw Kokoro) output.
    Returns (audio_path, duration_sec) or (None, None).
    """
    log = read_log()
    for step_name in ("add_sfx", "generate_audio"):
        for entry in reversed(log):
            if (entry.get("step") == step_name
                    and entry.get("story_id") == story_id
                    and entry.get("status") == "success"
                    and entry.get("output_file")):
                p = Path(entry["output_file"])
                if p.exists():
                    return p, float(entry.get("duration_sec", 0))
    return None, None


# ── SCRIPT PARSING HELPERS ────────────────────────────────────────────────────

def parse_silence_markers(script_path: Path) -> list[dict]:
    """
    Parse [SILENCE: X.0] markers from script. Returns chronological list.
    Each marker is {"duration_sec": float, "index": n} (0-indexed order).
    """
    markers = []
    if not script_path.exists():
        return markers

    text = script_path.read_text(encoding="utf-8")
    pattern = r'\[SILENCE:\s*([\d.]+)\]'
    for match in re.finditer(pattern, text):
        markers.append({
            "duration_sec": float(match.group(1)),
            "index": len(markers)
        })
    return markers


def get_silence_duration(script_path: Path) -> float:
    """Returns total silence duration (sum of all [SILENCE: X.0] markers)."""
    markers = parse_silence_markers(script_path)
    return sum(m["duration_sec"] for m in markers)


def get_clip_duration(scene_index: int, total_scenes: int,
                      total_audio_sec: float) -> float:
    """
    Variable timing per scene: fast cuts (hook), medium (build), slow (climax).
    Durations are scaled proportionally to fit audio.
    """
    if scene_index < 5:
        return 2.5        # hook — fast cuts
    elif scene_index < 20:
        return 4.5        # build — medium
    else:
        return 7.0        # climax — slow, earned weight


# ── FFMPEG HELPERS ────────────────────────────────────────────────────────────

def check_ffmpeg() -> str:
    """Returns ffmpeg path or exits with instructions."""
    path = shutil.which("ffmpeg")
    if not path:
        print("[ERROR] ffmpeg not found on PATH.\n")
        print("  INSTALL FFMPEG (Windows):")
        print("  Option A: winget install --id Gyan.FFmpeg")
        print("  Option B: Download from https://www.gyan.dev/ffmpeg/builds/")
        print("            Extract and add the bin/ folder to your PATH.\n")
        sys.exit(1)
    return path


def probe_duration(ffmpeg_path: str, audio_path: Path) -> float:
    """Uses ffprobe to get the exact audio duration in seconds."""
    ffprobe = ffmpeg_path.replace("ffmpeg", "ffprobe")
    if not Path(ffprobe).exists():
        ffprobe = shutil.which("ffprobe") or ffprobe

    try:
        result = subprocess.run(
            [ffprobe, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=15
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def make_clip(ffmpeg_path: str, image_path: Path, clip_path: Path,
              duration: float, fps: int, zoom_direction: str) -> bool:
    """
    Generates a single Ken Burns clip from a static image.
    zoom_direction: "in_center" | "in_right" | "in_left" | "in_up"
    """
    frames = max(1, round(fps * duration))
    incr   = round(ZOOM_MAX - 1.0, 6) / frames
    incr_s = f"{incr:.8f}"

    z_expr = f"min(zoom+{incr_s},{ZOOM_MAX})"

    pan_speed = 0.3

    if zoom_direction == "in_right":
        x_expr = f"iw/2-(iw/zoom/2)+on*{pan_speed}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif zoom_direction == "in_left":
        x_expr = f"iw/2-(iw/zoom/2)-on*{pan_speed}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif zoom_direction == "in_up":
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)-on*{pan_speed}"
    else:
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    vf = (
        f"scale={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:force_original_aspect_ratio=decrease,"
        f"pad={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"zoompan="
        f"z='{z_expr}':"
        f"x='{x_expr}':"
        f"y='{y_expr}':"
        f"d={frames}:"
        f"s={OUTPUT_W}x{OUTPUT_H}:"
        f"fps={fps},"
        f"setpts=PTS-STARTPTS"
    )

    cmd = [
        ffmpeg_path,
        "-y",
        "-loop", "1",
        "-framerate", str(fps),
        "-t", str(duration),
        "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",
        str(clip_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def concat_clips(ffmpeg_path: str, clip_paths: list[Path], audio_path: Path,
                 output_path: Path, fps: int) -> bool:
    """
    Concatenates clip files using the concat demuxer, then mixes in audio.
    """
    concat_list = output_path.parent / "concat_list.txt"
    lines = [f"file '{str(p).replace(chr(92), '/')}'\n" for p in clip_paths]
    concat_list.write_text("".join(lines), encoding="utf-8")

    audio_str       = str(audio_path).replace("\\", "/")
    concat_list_str = str(concat_list).replace("\\", "/")

    cmd = [
        ffmpeg_path,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_str,
        "-i", audio_str,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    concat_list.unlink(missing_ok=True)
    return result.returncode == 0


# ── MAIN ──────────────────────────────────────────────────────────────────────

def compile_video(story_id: str, fps: int, dry_run: bool):

    story_dir   = STORIES_DIR / story_id
    images_dir  = story_dir / "assets" / "images"
    exports_dir = story_dir / "assets" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{story_id}_tiktok_{timestamp}.mp4"
    output_path = exports_dir / output_filename

    print(f"\n{'='*60}")
    print(f"  Biblical Storytelling -- Video Compiler")
    print(f"{'='*60}")
    print(f"  Story    : {story_id}")
    print(f"  Output   : {OUTPUT_W}x{OUTPUT_H} @ {fps}fps  (TikTok 9:16)")
    if dry_run:
        print(f"  Mode     : DRY RUN")
    print(f"{'='*60}\n")

    # ── Validate ffmpeg
    ffmpeg_path = check_ffmpeg()
    print(f"[1/4] ffmpeg: {ffmpeg_path}")

    # ── Find audio
    print("[2/4] Locating audio from pipeline log...")
    audio_path, logged_duration = get_latest_audio(story_id)
    if not audio_path:
        print("[ERROR] No successful generate_audio entry found in pipeline log.")
        print(f"        Run: python tools/generate_audio.py --story {story_id}")
        sys.exit(1)

    probed = probe_duration(ffmpeg_path, audio_path)
    audio_duration = probed if probed > 0 else logged_duration

    print(f"       Audio  : {audio_path.name}")
    print(f"       Duration: {audio_duration:.2f}s")

    # ── Parse silence markers for timing
    script_path = story_dir / "script_tiktok.md"
    silence_duration = get_silence_duration(script_path)

    if silence_duration > 0:
        print(f"       Silence: {silence_duration:.2f}s (subtracted from timing)")

    video_duration = audio_duration - silence_duration
    if video_duration < 0:
        print("[ERROR] Total silence duration exceeds audio duration.")
        sys.exit(1)

    # ── Collect and sort scene images
    print("[3/4] Collecting scene images...")
    scene_files = sorted(
        [p for p in images_dir.glob("scene_S*.png")],
        key=scene_sort_key
    )

    if not scene_files:
        print(f"[ERROR] No scene_S*.png files found in {images_dir}")
        print(f"        Run: python tools/generate_images.py --story {story_id}")
        sys.exit(1)

    n_images = len(scene_files)

    # Variable durations scaled to fit audio
    clip_durations = []
    total_preset_duration = 0.0
    for i in range(n_images):
        dur = get_clip_duration(i, n_images, video_duration)
        clip_durations.append(dur)
        total_preset_duration += dur

    if total_preset_duration > 0:
        scale_factor = video_duration / total_preset_duration
        clip_durations = [d * scale_factor for d in clip_durations]
    else:
        clip_durations = [video_duration / n_images] * n_images

    print(f"       Scenes  : {n_images}")
    print(f"       Video duration: {video_duration:.2f}s\n")

    for i, p in enumerate(scene_files, 1):
        print(f"       {i:02d}. {p.name} ({clip_durations[i-1]:.2f}s)")

    if dry_run:
        print(f"\n[DRY RUN] Would generate {n_images} clips -> concat -> {output_filename}")
        print(f"          Total video duration: ~{video_duration:.1f}s")
        print(f"          Output: {output_path}")
        return

    # ── Generate clips
    print(f"\n[4/4] Generating {n_images} Ken Burns clips + final compile...")
    pan_cycle = ["in_center", "in_right", "in_center", "in_left",
                 "in_center", "in_up",    "in_center", "in_right"]

    clip_paths = []

    with tempfile.TemporaryDirectory(prefix="biblical_clips_") as tmpdir:
        tmp = Path(tmpdir)

        for i, img_path in enumerate(scene_files):
            clip_path  = tmp / f"clip_{i:02d}.mp4"
            zoom_dir   = pan_cycle[i % len(pan_cycle)]
            key        = scene_sort_key(img_path)
            scene_label = f"S{key[0]:02d}{key[1]}"
            clip_dur   = clip_durations[i]

            print(f"  [{i+1:02d}/{n_images}] {scene_label} ({zoom_dir}, {clip_dur:.2f}s) — {img_path.name}")

            ok = make_clip(
                ffmpeg_path=ffmpeg_path,
                image_path=img_path,
                clip_path=clip_path,
                duration=clip_dur,
                fps=fps,
                zoom_direction=zoom_dir
            )

            if not ok:
                print(f"          [ERROR] ffmpeg failed on clip {i+1}.")
                sys.exit(1)

            size_kb = clip_path.stat().st_size // 1024
            print(f"          [OK] {clip_path.name} ({size_kb} KB)")
            clip_paths.append(clip_path)

        # ── Concat + audio — final output
        print(f"\n  Concatenating clips and adding audio...")
        ok = concat_clips(
            ffmpeg_path=ffmpeg_path,
            clip_paths=clip_paths,
            audio_path=audio_path,
            output_path=output_path,
            fps=fps
        )

        if not ok:
            print("[ERROR] ffmpeg concat failed.")
            sys.exit(1)

    # ── Done
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"  [SUCCESS] Video compiled")
    print(f"  File     : {output_filename}")
    print(f"  Size     : {size_mb:.1f} MB")
    print(f"  Duration : ~{audio_duration:.1f}s")
    print(f"  Location : {exports_dir}")
    print(f"{'='*60}\n")
    print(f"  NEXT STEP: Import into CapCut for captions.")
    print(f"             Then upload {output_filename} to TikTok.")
    print(f"             Caption draft + hashtags in script_tiktok.md\n")

    log_entry = {
        "step":              "compile_video",
        "story_id":          story_id,
        "timestamp":         timestamp,
        "audio_file":        str(audio_path),
        "scene_count":       n_images,
        "duration_sec":      round(audio_duration, 1),
        "video_duration_sec": round(video_duration, 1),
        "silence_duration_sec": round(silence_duration, 2),
        "resolution":        f"{OUTPUT_W}x{OUTPUT_H}",
        "fps":               fps,
        "output_file":       str(output_path),
        "size_mb":           round(size_mb, 1),
        "status":            "success"
    }
    append_pipeline_log(log_entry)

    print(f"  Pipeline log updated: {PIPELINE_LOG}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compile Ken Burns TikTok MP4 from scenes + audio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/compile_video.py --story 001_witch_of_endor
  python tools/compile_video.py --story 001_witch_of_endor --dry-run
  python tools/compile_video.py --story 001_witch_of_endor --fps 24

Pipeline:
  generate_audio.py -> add_sfx.py -> generate_images.py -> [compile_video.py]
  Then: CapCut (captions) -> TikTok
        """
    )
    parser.add_argument("--story",   required=True, help="Story folder name, e.g. 001_witch_of_endor")
    parser.add_argument("--fps",     type=int, default=30, help="Output frame rate (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running ffmpeg")

    args = parser.parse_args()
    compile_video(story_id=args.story, fps=args.fps, dry_run=args.dry_run)


if __name__ == "__main__":
    main()