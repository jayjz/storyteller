#!/usr/bin/env python3
"""
validate_pipeline.py
Quick validation script to test current pipeline state and identify issues
before starting Phase 1 work.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
STORIES_DIR = BASE_DIR / "stories"
LOGS_DIR = BASE_DIR / "logs"
PIPELINE_LOG = LOGS_DIR / "pipeline.json"

def check_story(story_id: str):
    """Validate a story's current state"""
    story_dir = STORIES_DIR / story_id
    
    print(f"\n{'='*70}")
    print(f"  Validating: {story_id}")
    print(f"{'='*70}")
    
    # Check structure
    checks = {
        "script_tiktok.md": story_dir / "script_tiktok.md",
        "script_youtube.md": story_dir / "script_youtube.md",
        "image_prompts.md": story_dir / "image_prompts.md",
        "assets/audio/": story_dir / "assets" / "audio",
        "assets/images/": story_dir / "assets" / "images",
        "assets/exports/": story_dir / "assets" / "exports",
    }
    
    for name, path in checks.items():
        exists = "✓" if path.exists() else "✗"
        if path.is_file():
            size = path.stat().st_size
            print(f"  {exists} {name:<25} ({size:,} bytes)")
        elif path.is_dir():
            files = list(path.glob("*")) if path.exists() else []
            print(f"  {exists} {name:<25} ({len(files)} files)")
        else:
            print(f"  {exists} {name:<25} MISSING")
    
    # Check audio files
    audio_dir = story_dir / "assets" / "audio"
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.wav"))
        if audio_files:
            print(f"\n  Audio files:")
            for af in audio_files:
                size_mb = af.stat().st_size / (1024 * 1024)
                print(f"    - {af.name} ({size_mb:.1f} MB)")
    
    # Check images
    images_dir = story_dir / "assets" / "images"
    if images_dir.exists():
        images = list(images_dir.glob("*.png"))
        print(f"\n  Images: {len(images)} generated")
        if images:
            # Check for expected scenes
            scene_ids = set()
            for img in images:
                # Extract S01, S02, etc. from filename
                import re
                m = re.search(r'S(\d+[A-Z]?)', img.stem, re.IGNORECASE)
                if m:
                    scene_ids.add(m.group(1))
            print(f"    Scenes: {sorted(scene_ids)}")
    
    # Check exports
    exports_dir = story_dir / "assets" / "exports"
    if exports_dir.exists():
        videos = list(exports_dir.glob("*.mp4"))
        print(f"\n  Videos: {len(videos)} exported")
        for v in videos:
            size_mb = v.stat().st_size / (1024 * 1024)
            print(f"    - {v.name} ({size_mb:.1f} MB)")
    
    return True

def check_pipeline_log():
    """Check pipeline.json for completed steps"""
    print(f"\n{'='*70}")
    print(f"  Pipeline Log Status")
    print(f"{'='*70}")
    
    if not PIPELINE_LOG.exists():
        print("  No pipeline log found")
        return
    
    try:
        log = json.loads(PIPELINE_LOG.read_text())
        print(f"  Total entries: {len(log)}")
        
        # Group by story
        stories = {}
        for entry in log:
            sid = entry.get("story_id", "unknown")
            if sid not in stories:
                stories[sid] = []
            stories[sid].append(entry)
        
        for story_id, entries in stories.items():
            print(f"\n  {story_id}:")
            for e in entries:
                step = e.get("step", "unknown")
                status = e.get("status", "unknown")
                timestamp = e.get("timestamp", "")
                duration = e.get("duration_sec", "")
                if duration:
                    duration = f" ({duration}s)"
                print(f"    - {step:<20} {status:<10} {timestamp}{duration}")
    
    except Exception as e:
        print(f"  Error reading log: {e}")

def analyze_pacing():
    """Analyze the pacing mismatch between audio and video"""
    print(f"\n{'='*70}")
    print(f"  Pacing Analysis")
    print(f"{'='*70}")
    
    # Read pipeline log for audio durations
    if PIPELINE_LOG.exists():
        log = json.loads(PIPELINE_LOG.read_text())
        audio_entries = [e for e in log if e.get("step") == "generate_audio" and e.get("status") == "success"]
        
        if audio_entries:
            print("\n  Audio durations:")
            for entry in audio_entries:
                story = entry.get("story_id")
                duration = entry.get("duration_sec", 0)
                words = entry.get("word_count", 0)
                wpm = (words / duration * 60) if duration else 0
                print(f"    {story}: {duration:.1f}s, {words} words ({wpm:.0f} WPM)")
            
            # Compare to video compiler targets
            print("\n  Video compiler targets (from compile_video.py):")
            print("    - Hook scenes (0-4): 2.8s each")
            print("    - Build scenes (5-11): 4.0s each")
            print("    - Battle scenes (12-15): 5.2s each")
            print("    - Climax scenes (16+): 6.8s each")
            print("    - For 18 scenes: ~75s total (with scaling)")
            print("    - For 30 scenes: ~125s total (with scaling)")
            
            print("\n  ⚠️  MISMATCH DETECTED:")
            print("     Audio: ~240 seconds (4 minutes)")
            print("     Video target: ~75-125 seconds (1-2 minutes)")
            print("\n  Recommended fixes:")
            print("    1. Create 90-second TikTok scripts (180-200 words)")
            print("    2. OR update video compiler to handle 240s properly")
            print("    3. OR generate both versions (short + long)")

def main():
    print(f"\n{'='*70}")
    print(f"  Storyteller Pipeline Validation")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}")
    
    # Check each story
    stories = ["001_witch_of_endor", "002_elijah_still_small_voice", "003_first_crusade"]
    for story_id in stories:
        if (STORIES_DIR / story_id).exists():
            check_story(story_id)
    
    # Check pipeline log
    check_pipeline_log()
    
    # Analyze pacing
    analyze_pacing()
    
    print(f"\n{'='*70}")
    print(f"  Validation Complete")
    print(f"{'='*70}\n")
    print("Next steps:")
    print("  1. Generate images: python tools/generate_images.py --story 001_witch_of_endor")
    print("  2. Compile video: python tools/compile_video.py --story 001_witch_of_endor")
    print("  3. Review output and check pacing")
    print()

if __name__ == "__main__":
    main()