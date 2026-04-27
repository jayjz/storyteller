"""
compile_video.py - Optimized for 55-65s viral TikTok
"""

import argparse
import json
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
ZOOM_CANVAS_W = OUTPUT_W * 2
ZOOM_CANVAS_H = OUTPUT_H * 2
ZOOM_MAX = 1.18


def scene_sort_key(path: Path) -> tuple:
    m = re.search(r"S(\d+)([A-Z]?)", path.stem, re.IGNORECASE)
    if not m:
        return (9999, "")
    return (int(m.group(1)), m.group(2).upper())


def read_log() -> list:
    if PIPELINE_LOG.exists():
        try:
            return json.loads(PIPELINE_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def get_latest_audio(story_id: str):
    log = read_log()
    for step_name in ("add_sfx", "generate_audio"):
        for entry in reversed(log):
            if (entry.get("step") == step_name and entry.get("story_id") == story_id and entry.get("status") == "success"):
                p = Path(entry["output_file"])
                if p.exists():
                    return p, float(entry.get("duration_sec", 0))
    return None, None


def parse_silence_markers(script_path: Path):
    markers = []
    if not script_path.exists():
        return markers
    text = script_path.read_text(encoding="utf-8")
    for match in re.finditer(r'\[SILENCE:\s*([\d.]+)\]', text):
        markers.append({"duration_sec": float(match.group(1))})
    return markers


def get_silence_duration(script_path: Path) -> float:
    return sum(m["duration_sec"] for m in parse_silence_markers(script_path))


def get_clip_duration(scene_index: int, total_scenes: int, total_video_sec: float) -> float:
    """Optimized for 55-65 second viral storytelling"""
    if scene_index < 5:           # Hook - punchy
        return 2.8
    elif scene_index < 12:        # Build / March
        return 4.0
    elif scene_index < 16:        # Siege & Battle
        return 5.2
    else:                         # Climax & Reflection
        return 6.8


def check_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        print("[ERROR] ffmpeg not found.")
        sys.exit(1)
    return path


def probe_duration(ffmpeg_path: str, audio_path: Path) -> float:
    ffprobe = ffmpeg_path.replace("ffmpeg", "ffprobe")
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
                                capture_output=True, text=True, timeout=15)
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def make_clip(ffmpeg_path: str, image_path: Path, clip_path: Path, duration: float, fps: int, zoom_direction: str) -> bool:
    frames = max(1, round(fps * duration))
    incr = round(ZOOM_MAX - 1.0, 6) / frames
    incr_s = f"{incr:.8f}"

    z_expr = f"min(zoom+{incr_s},{ZOOM_MAX})"
    pan_speed = 0.35

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

    vf = f"scale={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:force_original_aspect_ratio=decrease," \
         f"pad={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:(ow-iw)/2:(oh-ih)/2:color=black," \
         f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:" \
         f"s={OUTPUT_W}x{OUTPUT_H}:fps={fps},setpts=PTS-STARTPTS"

    cmd = [
        ffmpeg_path, "-y", "-loop", "1", "-framerate", str(fps), "-t", str(duration),
        "-i", str(image_path), "-vf", vf, "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(clip_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def concat_clips(ffmpeg_path: str, clip_paths: list, audio_path: Path, output_path: Path, fps: int) -> bool:
    concat_list = output_path.parent / "concat_list.txt"
    lines = [f"file '{str(p).replace(chr(92), '/')}'\n" for p in clip_paths]
    concat_list.write_text("".join(lines), encoding="utf-8")

    cmd = [
        ffmpeg_path, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(audio_path), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    concat_list.unlink(missing_ok=True)
    return result.returncode == 0


def compile_video(story_id: str, fps: int, dry_run: bool):
    story_dir = STORIES_DIR / story_id
    images_dir = story_dir / "assets" / "images"
    exports_dir = story_dir / "assets" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{story_id}_tiktok_{timestamp}.mp4"
    output_path = exports_dir / output_filename

    print(f"\n{'='*70}")
    print(f"  Video Compiler - Short Form Viral Mode")
    print(f"{'='*70}")

    ffmpeg_path = check_ffmpeg()

    audio_path, logged_duration = get_latest_audio(story_id)
    if not audio_path:
        print("[ERROR] No audio found.")
        sys.exit(1)

    audio_duration = probe_duration(ffmpeg_path, audio_path) or logged_duration
    silence_duration = get_silence_duration(story_dir / "script_tiktok.md")
    video_duration = audio_duration - silence_duration

    print(f"Audio     : {audio_duration:.1f}s")
    print(f"Silence   : {silence_duration:.1f}s")
    print(f"Target    : {video_duration:.1f}s\n")

    scene_files = sorted(images_dir.glob("scene_S*.png"), key=scene_sort_key)
    n_images = len(scene_files)

    clip_durations = [get_clip_duration(i, n_images, video_duration) for i in range(n_images)]
    total_preset = sum(clip_durations)
    if total_preset > 0:
        scale = video_duration / total_preset
        clip_durations = [max(2.5, round(d * scale, 2)) for d in clip_durations]

    print(f"Scenes    : {n_images}")
    print(f"Avg clip  : {video_duration/n_images:.2f}s\n")

    if dry_run:
        print("DRY RUN COMPLETE")
        return

    pan_cycle = ["in_center", "in_right", "in_center", "in_left", "in_center", "in_up"]
    clip_paths = []

    with tempfile.TemporaryDirectory(prefix="biblical_clips_") as tmpdir:
        tmp = Path(tmpdir)
        for i, img_path in enumerate(scene_files):
            clip_path = tmp / f"clip_{i:02d}.mp4"
            zoom_dir = pan_cycle[i % len(pan_cycle)]
            clip_dur = clip_durations[i]

            ok = make_clip(ffmpeg_path, img_path, clip_path, clip_dur, fps, zoom_dir)
            if not ok:
                print(f"[ERROR] Failed on clip {i+1}")
                sys.exit(1)
            clip_paths.append(clip_path)

        ok = concat_clips(ffmpeg_path, clip_paths, audio_path, output_path, fps)
        if not ok:
            print("[ERROR] Final concat failed.")
            sys.exit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] Video compiled!")
    print(f"File     : {output_filename}")
    print(f"Size     : {size_mb:.1f} MB")
    print(f"Duration : ~{audio_duration:.1f}s")
    print(f"Location : {exports_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", required=True)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    compile_video(args.story, args.fps, args.dry_run)


if __name__ == "__main__":
    main()