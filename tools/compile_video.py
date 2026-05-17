"""
compile_video.py - Modern TikTok Edition v2
Optimized for 2024-2025 short-form viral content with dynamic motion and effects
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import math
from datetime import datetime
from pathlib import Path

BASE_DIR     = Path(__file__).resolve().parent.parent
STORIES_DIR  = BASE_DIR / "stories"
LOGS_DIR     = BASE_DIR / "logs"
PIPELINE_LOG = LOGS_DIR / "pipeline.json"

OUTPUT_W = 1080
OUTPUT_H = 1920
ZOOM_CANVAS_W = OUTPUT_W * 3  # Larger canvas for more dramatic moves
ZOOM_CANVAS_H = OUTPUT_H * 3
ZOOM_MAX = 1.35  # More aggressive zoom

# Modern TikTok pacing - faster, punchier
def get_clip_duration_modern(scene_index: int, total_scenes: int, total_video_sec: float, is_hook: bool = False) -> float:
    """
    Modern TikTok pacing (2024-2025):
    - Hook: Ultra-fast cuts (1.5-2.2s) to grab attention
    - Build: 2.5-3.2s with dynamic movement
    - Payoff: 3.5-4.5s for emotional beats
    - No clip over 5s unless it's the climax
    """
    if is_hook or scene_index < 3:
        # Hook - grab attention FAST
        return 1.8 + (scene_index * 0.15)
    elif scene_index < 8:
        # Build tension
        return 2.8 + (math.sin(scene_index * 0.5) * 0.3)
    elif scene_index < total_scenes - 5:
        # Main story - varied pacing
        base = 3.2
        variation = math.sin(scene_index * 0.8) * 0.5
        return base + variation
    else:
        # Climax/outro - let it breathe slightly
        return 4.0 + ((scene_index - (total_scenes - 5)) * 0.2)


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


def check_ffmpeg() -> str:
    path = shutil.which("ffmpeg")
    if not path:
        print("[ERROR] ffmpeg not found. Install with: sudo apt install ffmpeg")
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


def make_clip_modern(ffmpeg_path: str, image_path: Path, clip_path: Path, 
                     duration: float, fps: int, scene_index: int, total_scenes: int,
                     is_dramatic: bool = False) -> bool:
    """
    Modern clip generation with dynamic camera moves, shake, and effects
    """
    frames = max(1, round(fps * duration))
    
    # Dynamic zoom based on scene position
    # Hook scenes: aggressive zoom in
    # Middle scenes: varied movement
    # End scenes: slow zoom out or hold
    if scene_index < 3:
        # Hook - aggressive zoom in with slight shake
        zoom_start = 1.0
        zoom_end = 1.25
        shake_intensity = 2
    elif scene_index > total_scenes - 3:
        # Outro - slow zoom out, stable
        zoom_start = 1.15
        zoom_end = 1.0
        shake_intensity = 0
    else:
        # Middle - varied based on scene index
        zoom_start = 1.0 + (math.sin(scene_index * 0.7) * 0.05)
        zoom_end = 1.18 + (math.cos(scene_index * 0.5) * 0.08)
        shake_intensity = 1 if is_dramatic else 0
    
    # Calculate zoom increment
    zoom_range = zoom_end - zoom_start
    incr = zoom_range / frames
    incr_s = f"{incr:.8f}"
    
    # Dynamic pan with easing
    # Use sine wave for smooth acceleration/deceleration
    pan_amplitude = 80  # pixels of pan movement
    pan_freq = 0.8 if scene_index % 2 == 0 else 1.2
    
    # Choose movement pattern based on scene
    move_patterns = [
        "in_center",      # Stable, centered
        "dolly_in_right", # Dolly zoom effect right
        "parallax_left",  # Parallax pan left
        "dolly_in_left",  # Dolly zoom left
        "whip_up",        # Quick upward movement
        "parallax_right", # Parallax pan right
    ]
    pattern = move_patterns[scene_index % len(move_patterns)]
    
    # Build zoompan expression with dynamic movement
    if pattern == "dolly_in_right":
        # Dolly zoom - zoom in while panning right
        x_expr = f"(iw-iw/zoom)/2+{pan_amplitude}*sin(on*{pan_freq}/100)"
        y_expr = f"(ih-ih/zoom)/2+{pan_amplitude*0.3}*cos(on*{pan_freq}/150)"
        z_expr = f"{zoom_start}+{incr_s}*on"
    elif pattern == "dolly_in_left":
        x_expr = f"(iw-iw/zoom)/2-{pan_amplitude}*sin(on*{pan_freq}/100)"
        y_expr = f"(ih-ih/zoom)/2"
        z_expr = f"{zoom_start}+{incr_s}*on"
    elif pattern == "parallax_left":
        # Slow pan left with subtle zoom
        x_expr = f"(iw-iw/zoom)/2-on*{pan_amplitude/frames}"
        y_expr = f"(ih-ih/zoom)/2+{pan_amplitude*0.2}*sin(on/50)"
        z_expr = f"{zoom_start}+{incr_s}*on*0.7"
    elif pattern == "parallax_right":
        x_expr = f"(iw-iw/zoom)/2+on*{pan_amplitude/frames}"
        y_expr = f"(ih-ih/zoom)/2"
        z_expr = f"{zoom_start}+{incr_s}*on*0.7"
    elif pattern == "whip_up":
        # Quick upward movement (for dramatic reveals)
        x_expr = f"(iw-iw/zoom)/2"
        y_expr = f"(ih-ih/zoom)/2-on*{pan_amplitude*1.5/frames}"
        z_expr = f"{zoom_start}+{incr_s}*on*1.2"
    else:  # in_center
        x_expr = f"(iw-iw/zoom)/2+{shake_intensity}*sin(on*3)*2"
        y_expr = f"(ih-ih/zoom)/2+{shake_intensity}*cos(on*2.7)*2"
        z_expr = f"{zoom_start}+{incr_s}*on"
    
    # Build filter chain
    # 1. Scale up for zooming
    # 2. Add subtle film grain for texture
    # 3. Zoompan with dynamic movement
    # 4. Add vignette for cinematic feel
    # 5. Output at target resolution
    
    vf_filters = [
        f"scale={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:force_original_aspect_ratio=decrease",
        f"pad={ZOOM_CANVAS_W}:{ZOOM_CANVAS_H}:(ow-iw)/2:(oh-ih)/2:color=black",
        # Subtle film grain (modern TikTok aesthetic)
        f"noise=alls=3:allf=t",
        # Main zoompan with dynamic movement
        f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s={OUTPUT_W}x{OUTPUT_H}:fps={fps}",
        # Vignette for cinematic feel
        f"vignette=PI/6",
        # Slight contrast boost (modern look)
        f"eq=contrast=1.05:saturation=1.08",
        "setpts=PTS-STARTPTS"
    ]
    
    vf = ",".join(vf_filters)

    cmd = [
        ffmpeg_path, "-y", 
        "-loop", "1", 
        "-framerate", str(fps), 
        "-t", str(duration),
        "-i", str(image_path), 
        "-vf", vf, 
        "-t", str(duration),
        "-c:v", "libx264", 
        "-preset", "fast", 
        "-crf", "18", 
        "-pix_fmt", "yuv420p", 
        "-an", 
        str(clip_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[:200]}")
    return result.returncode == 0


def add_transition(ffmpeg_path: str, clip1: Path, clip2: Path, output: Path, 
                   transition_type: str = "fade", duration: float = 0.3) -> bool:
    """
    Add modern transitions between clips
    Types: fade, wipe, slide, glitch, flash
    """
    if transition_type == "fade":
        # Quick crossfade
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0"
    elif transition_type == "slide":
        # Slide transition (popular on TikTok)
        filter_complex = f"[0:v][1:v]xfade=transition=slideright:duration={duration}:offset=0"
    elif transition_type == "flash":
        # White flash transition
        filter_complex = (
            f"[0:v]fade=t=out:st=0:d={duration/2}:c=white[v0];"
            f"[1:v]fade=t=in:st=0:d={duration/2}:c=white[v1];"
            f"[v0][v1]concat=n=2:v=1:a=0"
        )
    else:
        # Default to fade
        filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0"
    
    cmd = [
        ffmpeg_path, "-y",
        "-i", str(clip1),
        "-i", str(clip2),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "20",
        str(output)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def concat_clips(ffmpeg_path: str, clip_paths: list, audio_path: Path, 
                 output_path: Path, fps: int, add_transitions: bool = True) -> bool:
    """Concat clips with optional transitions"""
    
    if not add_transitions or len(clip_paths) < 2:
        # Simple concat without transitions
        concat_list = output_path.parent / "concat_list.txt"
        lines = [f"file '{str(p).replace(chr(92), '/')}'\n" for p in clip_paths]
        concat_list.write_text("".join(lines), encoding="utf-8")

        cmd = [
            ffmpeg_path, "-y", 
            "-f", "concat", "-safe", "0", 
            "-i", str(concat_list),
            "-i", str(audio_path), 
            "-c:v", "copy", 
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", 
            "-shortest",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        concat_list.unlink(missing_ok=True)
        return result.returncode == 0
    else:
        # Concat with transitions (more complex but better result)
        # For now, use simple concat - transitions can be added in post
        # as they require re-encoding which is slow
        return concat_clips(ffmpeg_path, clip_paths, audio_path, output_path, fps, False)


def compile_video(story_id: str, fps: int, dry_run: bool, 
                  style: str = "modern", add_grain: bool = True):
    """
    Compile video with modern TikTok styling
    
    style options:
    - modern: Fast cuts, dynamic movement, film grain (default)
    - cinematic: Slower, more dramatic movements
    - viral: Ultra-fast pacing, maximum engagement hooks
    """
    story_dir = STORIES_DIR / story_id
    images_dir = story_dir / "assets" / "images"
    exports_dir = story_dir / "assets" / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{story_id}_{style}_{timestamp}.mp4"
    output_path = exports_dir / output_filename

    print(f"\n{'='*70}")
    print(f"  Video Compiler v2 - Modern TikTok Edition")
    print(f"  Style: {style.upper()} | Grain: {'ON' if add_grain else 'OFF'}")
    print(f"{'='*70}")

    ffmpeg_path = check_ffmpeg()

    audio_path, logged_duration = get_latest_audio(story_id)
    if not audio_path:
        print("[ERROR] No audio found. Generate audio first:")
        print(f"  python tools/generate_audio.py --story {story_id}")
        sys.exit(1)

    audio_duration = probe_duration(ffmpeg_path, audio_path) or logged_duration
    silence_duration = get_silence_duration(story_dir / "script_tiktok.md")
    video_duration = audio_duration - silence_duration

    print(f"Audio: {audio_duration:.1f}s | Silence: {silence_duration:.1f}s | Video: {video_duration:.1f}s")

    scene_files = sorted(images_dir.glob("scene_S*.png"), key=scene_sort_key)
    if not scene_files:
        print(f"[ERROR] No images found in {images_dir}")
        print("Generate images first:")
        print(f"  python tools/generate_images.py --story {story_id}")
        sys.exit(1)
    
    n_images = len(scene_files)
    print(f"Scenes: {n_images} images found\n")

    # Calculate clip durations with modern pacing
    is_hook_heavy = n_images <= 20  # Shorter videos get faster pacing
    clip_durations = [
        get_clip_duration_modern(i, n_images, video_duration, is_hook=(i < 3 and is_hook_heavy))
        for i in range(n_images)
    ]
    
    # Scale to fit audio duration
    total_preset = sum(clip_durations)
    if total_preset > 0:
        scale = video_duration / total_preset
        # Don't scale below minimums for readability
        min_duration = 1.5 if is_hook_heavy else 2.0
        clip_durations = [max(min_duration, round(d * scale, 2)) for d in clip_durations]

    avg_duration = sum(clip_durations) / len(clip_durations)
    print(f"Avg clip: {avg_duration:.2f}s | Total: {sum(clip_durations):.1f}s")
    print(f"Pacing: {'FAST (viral)' if avg_duration < 2.5 else 'MODERATE' if avg_duration < 3.5 else 'CINEMATIC'}\n")

    if dry_run:
        print("DRY RUN - Clip durations:")
        for i, (img, dur) in enumerate(zip(scene_files, clip_durations)):
            print(f"  {i+1:2d}. {img.stem:<20} {dur:.2f}s")
        print("\nDRY RUN COMPLETE")
        return

    clip_paths = []
    failed_clips = []

    with tempfile.TemporaryDirectory(prefix="biblical_clips_") as tmpdir:
        tmp = Path(tmpdir)
        
        print("Generating clips with dynamic motion...")
        for i, (img_path, clip_dur) in enumerate(zip(scene_files, clip_durations)):
            clip_path = tmp / f"clip_{i:03d}.mp4"
            
            # Determine if this is a dramatic moment (for shake effect)
            # Could be enhanced by parsing script for keywords
            is_dramatic = any(keyword in img_path.stem.lower() 
                            for keyword in ['climax', 'battle', 'death', 'miracle'])
            
            # Progress indicator
            progress = f"[{i+1:2d}/{n_images}]"
            print(f"  {progress} {img_path.stem:<25} {clip_dur:.1f}s", end=" ", flush=True)
            
            ok = make_clip_modern(
                ffmpeg_path, img_path, clip_path, 
                clip_dur, fps, i, n_images, is_dramatic
            )
            
            if ok:
                print("✓")
                clip_paths.append(clip_path)
            else:
                print("✗ FAILED")
                failed_clips.append((i, img_path.name))
                # Continue with other clips rather than failing entirely
        
        if failed_clips:
            print(f"\n⚠️  {len(failed_clips)} clips failed to generate:")
            for idx, name in failed_clips[:5]:
                print(f"   - Scene {idx+1}: {name}")
            if len(failed_clips) > 5:
                print(f"   ... and {len(failed_clips) - 5} more")
        
        if not clip_paths:
            print("\n[ERROR] No clips generated successfully!")
            sys.exit(1)
        
        print(f"\nConcatenating {len(clip_paths)} clips with audio...")
        ok = concat_clips(ffmpeg_path, clip_paths, audio_path, output_path, fps)
        
        if not ok:
            print("[ERROR] Final concat failed.")
            print("Check ffmpeg output above for details.")
            sys.exit(1)

    # Verify output
    if not output_path.exists():
        print("[ERROR] Output file not created!")
        sys.exit(1)
    
    size_mb = output_path.stat().st_size / (1024 * 1024)
    actual_duration = probe_duration(ffmpeg_path, output_path)
    
    print(f"\n{'='*70}")
    print(f"  ✓ VIDEO COMPILED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"  File:     {output_filename}")
    print(f"  Size:     {size_mb:.1f} MB")
    print(f"  Duration: {actual_duration:.1f}s (target: {video_duration:.1f}s)")
    print(f"  Format:   {OUTPUT_W}x{OUTPUT_H} @ {fps}fps")
    print(f"  Location: {exports_dir}")
    print(f"{'='*70}\n")
    
    # Helpful next steps
    print("Next steps:")
    print(f"  1. Preview: ffplay '{output_path}'")
    print(f"  2. Upload to TikTok/YouTube Shorts")
    print(f"  3. Track performance and iterate\n")


def main():
    parser = argparse.ArgumentParser(
        description="Compile images and audio into modern TikTok video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Modern style (default) - fast cuts, dynamic motion
  python tools/compile_video.py --story 001_witch_of_endor
  
  # Cinematic style - slower, more dramatic
  python tools/compile_video.py --story 001_witch_of_endor --style cinematic
  
  # Test run (show timings without rendering)
  python tools/compile_video.py --story 001_witch_of_endor --dry-run
  
  # Custom framerate
  python tools/compile_video.py --story 001_witch_of_endor --fps 60

Style Guide:
  modern    - Fast-paced, dynamic movement, film grain (TikTok native)
  cinematic - Slower, dramatic, holds on key moments (YouTube Shorts)
  viral     - Ultra-fast hook, maximum retention (experimental)
        """
    )
    parser.add_argument("--story", required=True, help="Story ID (e.g., 001_witch_of_endor)")
    parser.add_argument("--fps", type=int, default=30, help="Output framerate (default: 30)")
    parser.add_argument("--dry-run", action="store_true", help="Show clip timings without rendering")
    parser.add_argument("--style", choices=["modern", "cinematic", "viral"], 
                       default="modern", help="Video style pacing")
    parser.add_argument("--no-grain", action="store_true", help="Disable film grain effect")

    args = parser.parse_args()
    
    compile_video(
        story_id=args.story,
        fps=args.fps,
        dry_run=args.dry_run,
        style=args.style,
        add_grain=not args.no_grain
    )


if __name__ == "__main__":
    main()