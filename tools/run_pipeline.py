"""
run_pipeline.py
===============
Orchestrator for the Autonomous Biblical Storytelling Pipeline.

USAGE:
    python tools/run_pipeline.py --story 001_witch_of_endor
    python tools/run_pipeline.py --story 001_witch_of_endor --force
    python tools/run_pipeline.py --story 001_witch_of_endor --from generate_images

STEPS:
    [1/3] generate_audio.py   — Kokoro TTS -> WAV
    [2/3] generate_images.py  — ComfyUI SDXL -> PNGs
    [3/3] compile_video.py    — FFmpeg assembly (build that next)

Reads logs/pipeline.json to skip already-completed steps.
Use --force to re-run all steps regardless of log state.
Use --from <step_name> to start from a specific step.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR     = Path(__file__).resolve().parent.parent
LOGS_DIR     = BASE_DIR / "logs"
PIPELINE_LOG = LOGS_DIR / "pipeline.json"
TOOLS_DIR    = BASE_DIR / "tools"

STEPS = [
    {
        "name":    "generate_audio",
        "label":   "Audio (Kokoro TTS)",
        "script":  "generate_audio.py",
        "args":    [],
    },
    {
        "name":    "generate_images",
        "label":   "Images (ComfyUI SDXL)",
        "script":  "generate_images.py",
        "args":    [],
    },
    {
        "name":    "compile_video",
        "label":   "Video compile (FFmpeg)",
        "script":  "compile_video.py",
        "args":    [],
        "not_built": True,
    },
]

STEP_NAMES = [s["name"] for s in STEPS]


# ── LOG HELPERS ───────────────────────────────────────────────────────────────

def read_log() -> list:
    if PIPELINE_LOG.exists():
        try:
            return json.loads(PIPELINE_LOG.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def step_is_complete(story_id: str, step_name: str) -> bool:
    log = read_log()
    for entry in reversed(log):
        if entry.get("story_id") == story_id and entry.get("step") == step_name:
            return entry.get("status") in ("success", "partial")
    return False


def append_log(entry: dict):
    log = read_log()
    log.append(entry)
    PIPELINE_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")


# ── RUNNER ────────────────────────────────────────────────────────────────────

def run_step(step: dict, story_id: str, extra_args: list) -> bool:
    script_path = TOOLS_DIR / step["script"]

    if not script_path.exists():
        print(f"     [SKIP] {step['script']} not found — build it first.")
        return False

    cmd = [sys.executable, str(script_path), "--story", story_id] + extra_args + step["args"]
    print(f"     Running: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    return result.returncode == 0


def run_pipeline(story_id: str, force: bool, start_from: str | None, extra_args: list):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Biblical Storytelling -- Pipeline Orchestrator")
    print(f"{'='*60}")
    print(f"  Story    : {story_id}")
    print(f"  Log      : {PIPELINE_LOG}")
    if force:
        print(f"  Mode     : FORCE (re-running all steps)")
    if start_from:
        print(f"  Starting from: {start_from}")
    print(f"{'='*60}\n")

    # Determine which step to start at
    start_index = 0
    if start_from:
        if start_from not in STEP_NAMES:
            print(f"[ERROR] Unknown step '{start_from}'. Valid steps: {', '.join(STEP_NAMES)}")
            sys.exit(1)
        start_index = STEP_NAMES.index(start_from)

    total = len(STEPS)
    results = []

    for i, step in enumerate(STEPS):
        step_num = i + 1
        label    = step["label"]
        name     = step["name"]

        if i < start_index:
            print(f"  [{step_num}/{total}] {label} — SKIPPED (before --from point)")
            results.append({"step": name, "status": "skipped_before_start"})
            continue

        print(f"  [{step_num}/{total}] {label}")

        if step.get("not_built"):
            print(f"     [NOT BUILT] {step['script']} does not exist yet.")
            print(f"     Run: python tools/{step['script']} when ready.")
            print()
            results.append({"step": name, "status": "not_built"})
            continue

        if not force and step_is_complete(story_id, name):
            print(f"     [DONE] Already completed (use --force to re-run).\n")
            results.append({"step": name, "status": "already_complete"})
            continue

        print()
        success = run_step(step, story_id, extra_args)

        if success:
            print(f"\n  [{step_num}/{total}] {label} -- COMPLETE\n")
            results.append({"step": name, "status": "success"})
        else:
            print(f"\n  [{step_num}/{total}] {label} -- FAILED\n")
            results.append({"step": name, "status": "failed"})
            print(f"{'='*60}")
            print(f"  [PIPELINE STOPPED] Step '{name}' failed.")
            print(f"  Fix the error above, then re-run:")
            print(f"  python tools/run_pipeline.py --story {story_id} --from {name}")
            print(f"{'='*60}\n")

            append_log({
                "step":      "run_pipeline",
                "story_id":  story_id,
                "timestamp": timestamp,
                "status":    "failed",
                "failed_at": name,
                "results":   results
            })
            sys.exit(1)

    success_count = sum(1 for r in results if r["status"] == "success")
    skipped_count = sum(1 for r in results if "skipped" in r["status"] or r["status"] == "already_complete")
    pending_count = sum(1 for r in results if r["status"] == "not_built")

    print(f"{'='*60}")
    print(f"  PIPELINE SUMMARY")
    print(f"  Complete : {success_count + skipped_count}")
    print(f"  Pending  : {pending_count}")
    print(f"{'='*60}")

    if pending_count > 0:
        print(f"\n  NEXT BUILD:")
        for r in results:
            if r["status"] == "not_built":
                step = next(s for s in STEPS if s["name"] == r["step"])
                print(f"  python tools/{step['script']} --story {story_id}")

    print()

    append_log({
        "step":      "run_pipeline",
        "story_id":  story_id,
        "timestamp": timestamp,
        "status":    "success",
        "results":   results
    })


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the full biblical storytelling video pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/run_pipeline.py --story 001_witch_of_endor
  python tools/run_pipeline.py --story 001_witch_of_endor --force
  python tools/run_pipeline.py --story 001_witch_of_endor --from generate_images

Steps:
  generate_audio    Kokoro TTS -> WAV
  generate_images   ComfyUI SDXL -> PNGs (requires ComfyUI running)
  compile_video     FFmpeg assembly (not built yet)
        """
    )
    parser.add_argument("--story",  required=True, help="Story folder name, e.g. 001_witch_of_endor")
    parser.add_argument("--force",  action="store_true", help="Re-run all steps even if already logged complete")
    parser.add_argument("--from",   dest="start_from", default=None,
                        metavar="STEP", help=f"Start from step: {', '.join(STEP_NAMES)}")
    parser.add_argument("--voice",  default=None, help="Override voice for audio step")
    parser.add_argument("--steps",  type=int, default=None, help="Override steps for image step")
    parser.add_argument("--cfg",    type=float, default=None, help="Override CFG for image step")

    args = parser.parse_args()

    # Build extra args to pass through to sub-scripts
    extra_args = []
    if args.voice:
        extra_args += ["--voice", args.voice]
    if args.steps:
        extra_args += ["--steps", str(args.steps)]
    if args.cfg:
        extra_args += ["--cfg", str(args.cfg)]

    run_pipeline(
        story_id=args.story,
        force=args.force,
        start_from=args.start_from,
        extra_args=extra_args
    )


if __name__ == "__main__":
    main()
