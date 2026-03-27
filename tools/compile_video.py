"""
compile_video.py
================
Step 3 of the Autonomous Biblical Storytelling Pipeline

PURPOSE:
    Reads the latest audio path from logs/pipeline.json, sorts scene PNGs
    from assets/images/ in scene order (S01, S02A, S02B...), and produces
    a 1080x1920 vertical TikTok MP4 with Ken Burns zoom on each image.

USAGE:
    python tools/compile_video.py --story 001_witch_of_endor
    python tools/compile_video.py --story 001_witch_of_endor --fps 30
    python tools/compile_video.py --story 001_witch_of_endor --dry-run

PIPELINE POSITION:
    generate_audio.py -> generate_images.py -> [compile_video.py]

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
# Oversample source images for zoompan headroom (2x gives room for ~1.5x zoom without pixelation)
ZOOM_CANVAS_W = OUTPUT_W * 2   # 2160
ZOOM_CANVAS_H = OUTPUT_H * 2   # 3840
# Ken Burns: zoom from 1.0 to this value over the clip duration
ZOOM_MAX = 1.18


# ── SCENE SORT KEY ─────────────────────────────────────────────────────────────

def scene_sort_key(path: Path) -> tuple:
    """
    Sorts scene_S01.png < scene_S02A.png < scene_S02B.png < scene_S03.png ...
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
    Finds the most recent successful generate_audio entry for this story.
    Returns (audio_path, duration_sec) or (None, None).
    """
    log = read_log()
    for entry in reversed(log):
        if (entry.get("step") == "generate_audio"
                and entry.get("story_id") == story_id
                and entry.get("status") == "success"
                and entry.get("output_file")):
            p = Path(entry["output_file"])
            if p.exists():
                return p, float(entry.get("duration_sec", 0))
    return None, None


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
    Each produces a slow zoom-in with a subtle pan variation.
    """
    frames = max(1, round(fps * duration))
    incr   = round(ZOOM_MAX - 1.0, 6) / frames   # per-frame zoom increment
    incr_s = f"{incr:.8f}"

    # Base zoom expression (identical for all — zoom in from 1.0 to ZOOM_MAX)
    z_expr = f"min(zoom+{incr_s},{ZOOM_MAX})"

    # Pan expression varies per direction — moves the viewport slightly
    # iw/ih here refer to the oversized canvas (ZOOM_CANVAS), not the output
    pan_speed = 0.3  # pixels per frame

    if zoom_direction == "in_right":
        # Pan slightly right while zooming in
        x_expr = f"iw/2-(iw/zoom/2)+on*{pan_speed}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif zoom_direction == "in_left":
        # Pan slightly left
        x_expr = f"iw/2-(iw/zoom/2)-on*{pan_speed}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif zoom_direction == "in_up":
        # Pan slightly upward
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = f"ih/2-(ih/zoom/2)-on*{pan_speed}"
    else:
        # Default: zoom in, hold center
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    # Filter chain:
    # 1. Scale source image to oversized canvas (letterbox → no distortion)
    # 2. Pad to exact canvas size with black bars
    # 3. zoompan produces OUTPUT_W x OUTPUT_H Ken Burns video at fps
    # 4. setpts normalises timestamps for concat
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
        "-t", str(duration),            # cap to exact duration (zoompan can overshoot)
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-an",                           # no audio in clips
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

    audio_str      = str(audio_path).replace("\\", "/")
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
        "-movflags", "+faststart",       # web-optimized atom placement
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
    print(f"[1/5] ffmpeg: {ffmpeg_path}")

    # ── Find audio
    print("[2/5] Locating audio from pipeline log...")
    audio_path, logged_duration = get_latest_audio(story_id)
    if not audio_path:
        print("[ERROR] No successful generate_audio entry found in pipeline log.")
        print(f"        Run: python tools/generate_audio.py --story {story_id}")
        sys.exit(1)

    # Probe exact duration (more accurate than the logged estimate)
    probed = probe_duration(ffmpeg_path, audio_path)
    audio_duration = probed if probed > 0 else logged_duration

    print(f"       Audio  : {audio_path.name}")
    print(f"       Duration: {audio_duration:.2f}s")

    # ── Collect and sort scene images
    print("[3/5] Collecting scene images...")
    scene_files = sorted(
        [p for p in images_dir.glob("scene_S*.png")],
        key=scene_sort_key
    )

    if not scene_files:
        print(f"[ERROR] No scene_S*.png files found in {images_dir}")
        print(f"        Run: python tools/generate_images.py --story {story_id}")
        sys.exit(1)

    n_images       = len(scene_files)
    duration_each  = audio_duration / n_images

    print(f"       Scenes  : {n_images}")
    print(f"       Per clip: {duration_each:.2f}s\n")

    for i, p in enumerate(scene_files, 1):
        print(f"       {i:02d}. {p.name}")

    if dry_run:
        print(f"\n[DRY RUN] Would generate {n_images} clips -> concat -> {output_filename}")
        print(f"          Total duration: ~{audio_duration:.1f}s")
        print(f"          Output: {output_path}")
        return

    # ── Generate clips in temp dir
    print(f"\n[4/5] Generating {n_images} Ken Burns clips...")
    pan_cycle = ["in_center", "in_right", "in_center", "in_left",
                 "in_center", "in_up",    "in_center", "in_right"]

    clip_paths = []

    with tempfile.TemporaryDirectory(prefix="biblical_clips_") as tmpdir:
        tmp = Path(tmpdir)

        for i, img_path in enumerate(scene_files):
            clip_path     = tmp / f"clip_{i:02d}.mp4"
            zoom_dir      = pan_cycle[i % len(pan_cycle)]
            key            = scene_sort_key(img_path)
            scene_label    = f"S{key[0]:02d}{key[1]}"

            print(f"  [{i+1:02d}/{n_images}] {scene_label} ({zoom_dir}) — {img_path.name}")

            ok = make_clip(
                ffmpeg_path=ffmpeg_path,
                image_path=img_path,
                clip_path=clip_path,
                duration=duration_each,
                fps=fps,
                zoom_direction=zoom_dir
            )

            if not ok:
                print(f"          [ERROR] ffmpeg failed on clip {i+1}.")
                print(f"          Check image file and ffmpeg installation.")
                sys.exit(1)

            size_kb = clip_path.stat().st_size // 1024
            print(f"          [OK] {clip_path.name} ({size_kb} KB)")
            clip_paths.append(clip_path)

        # ── Concat + audio
        print(f"\n[5/5] Concatenating clips and adding audio...")
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

    log_entry = {
        "step":          "compile_video",
        "story_id":      story_id,
        "timestamp":     timestamp,
        "audio_file":    str(audio_path),
        "scene_count":   n_images,
        "duration_sec":  round(audio_duration, 1),
        "resolution":    f"{OUTPUT_W}x{OUTPUT_H}",
        "fps":           fps,
        "output_file":   str(output_path),
        "size_mb":       round(size_mb, 1),
        "status":        "success"
    }
    append_pipeline_log(log_entry)

    print(f"  Pipeline log updated: {PIPELINE_LOG}")
    print(f"\n  NEXT STEP: Upload {output_filename} to TikTok.")
    print(f"             Caption draft is in script_tiktok.md -> HASHTAG SET\n")


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
  generate_audio.py -> generate_images.py -> [compile_video.py]
        """
    )
    parser.add_argument("--story",   required=True, help="Story folder name, e.g. 001_witch_of_endor")
    parser.add_argument("--fps",     type=int, default=30, help="Output frame rate (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without running ffmpeg")

    args = parser.parse_args()
    compile_video(story_id=args.story, fps=args.fps, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
