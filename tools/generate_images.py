"""
generate_images.py
==================
Step 2 of the Autonomous Biblical Storytelling Pipeline

PURPOSE:
    Reads image_prompts.md, parses each scene prompt, and submits them to
    a locally running ComfyUI instance via HTTP API. Saves outputs to
    assets/images/scene_XX.png. RTX 4060 optimized (768x768 SDXL).

USAGE:
    python tools/generate_images.py --story 001_witch_of_endor
    python tools/generate_images.py --story 001_witch_of_endor --dry-run
    python tools/generate_images.py --story 001_witch_of_endor --scene S03

COMFYUI SETUP (if not running):
    1. cd ComfyUI && python main.py --listen 0.0.0.0 --port 8188
    2. Ensure SDXL checkpoint is loaded (e.g. juggernautXL_ragnarokBy.safetensors)

PIPELINE POSITION:
    generate_audio.py → [generate_images.py] → compile_video.py
"""

import argparse
import json
import re
import sys
import time
import uuid
from pathlib import Path
from datetime import datetime

BASE_DIR    = Path(__file__).resolve().parent.parent
STORIES_DIR = BASE_DIR / "stories"
LOGS_DIR    = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

PIPELINE_LOG = LOGS_DIR / "pipeline.json"

COMFYUI_HOST   = "http://127.0.0.1:8188"
POLL_INTERVAL  = 3      # seconds between status checks
POLL_TIMEOUT   = 300    # seconds before giving up on a single image

# RTX 4060 8GB VRAM — safe SDXL settings
DEFAULT_WIDTH     = 768
DEFAULT_HEIGHT    = 768
DEFAULT_STEPS     = 28
DEFAULT_CFG       = 7.5
DEFAULT_SAMPLER   = "dpm_2"          # DPM++ 2M in ComfyUI node naming
DEFAULT_SCHEDULER = "karras"
DEFAULT_NEGATIVE  = (
    "modern clothing, cars, electricity, neon, anime, cartoon, watercolor, "
    "flat art, text, watermark, signature, low quality, blurry, extra limbs, "
    "deformed hands, ugly, disfigured"
)


# ── PROMPT PARSER ─────────────────────────────────────────────────────────────

def parse_image_prompts(prompts_path: Path) -> list[dict]:
    """
    Parses image_prompts.md into a list of scene dicts.

    Expected format in the file:
        ## S01 — Scene Title
        ```
        positive prompt text here
        ```
        **Shot:** ...
        **Mood:** ...

    Returns list of:
        {"scene_id": "S01", "title": "...", "prompt": "...", "shot": "...", "mood": "..."}
    """
    raw = prompts_path.read_text(encoding="utf-8")
    scenes = []

    # Split on ## headings that look like scene IDs (S01, S02, etc.) or THUMBNAIL
    blocks = re.split(r"\n(?=## [ST])", raw)

    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        header = lines[0].strip()
        # Match ## S01 — Title  OR  ## Thumbnail A — Title
        scene_match = re.match(r"^## (S\d+[A-Z]?|Thumbnail [A-Z])\s*[—-]+\s*(.+)$", header)
        if not scene_match:
            continue

        scene_id = scene_match.group(1).replace(" ", "_")
        title    = scene_match.group(2).strip()

        # Extract prompt from first ```...``` block
        code_match = re.search(r"```\s*\n([\s\S]+?)\n```", block)
        if not code_match:
            continue
        prompt = code_match.group(1).strip()

        # Extract Shot and Mood
        shot_match = re.search(r"\*\*Shot:\*\*\s*(.+)", block)
        mood_match = re.search(r"\*\*Mood:\*\*\s*(.+)", block)

        scenes.append({
            "scene_id": scene_id,
            "title":    title,
            "prompt":   prompt,
            "shot":     shot_match.group(1).strip() if shot_match else "",
            "mood":     mood_match.group(1).strip() if mood_match else "",
        })

    return scenes


# ── COMFYUI CLIENT ────────────────────────────────────────────────────────────

def check_comfyui_running() -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"{COMFYUI_HOST}/system_stats", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def build_sdxl_workflow(prompt: str, negative: str, width: int, height: int,
                         steps: int, cfg: float, sampler: str, scheduler: str,
                         filename_prefix: str) -> dict:
    """
    Returns a minimal ComfyUI API workflow dict for SDXL text-to-image.
    Uses node IDs as strings (ComfyUI API format).
    Checkpoint node expects the model to already be loaded in ComfyUI,
    or uses the default loaded checkpoint.
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "juggernautXL_ragnarokBy.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative,
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width":   width,
                "height":  height,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model":       ["1", 0],
                "positive":    ["2", 0],
                "negative":    ["3", 0],
                "latent_image": ["4", 0],
                "seed":        int(time.time() * 1000) % (2**32),
                "steps":       steps,
                "cfg":         cfg,
                "sampler_name": sampler,
                "scheduler":   scheduler,
                "denoise":     1.0
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae":     ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images":          ["6", 0],
                "filename_prefix": filename_prefix
            }
        }
    }


def submit_prompt(workflow: dict) -> str:
    """Posts workflow to ComfyUI /prompt, returns prompt_id."""
    import urllib.request
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_HOST}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["prompt_id"]


def poll_until_done(prompt_id: str) -> bool:
    """Polls /history/{prompt_id} until the job completes or times out."""
    import urllib.request
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                f"{COMFYUI_HOST}/history/{prompt_id}", timeout=10
            ) as r:
                history = json.loads(r.read().decode())
            if prompt_id in history:
                return True
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)
    return False


def fetch_output_image(prompt_id: str, output_path: Path) -> bool:
    """
    Fetches the generated image from ComfyUI's output via /view API and saves it.
    Returns True on success.
    """
    import urllib.request
    try:
        with urllib.request.urlopen(
            f"{COMFYUI_HOST}/history/{prompt_id}", timeout=10
        ) as r:
            history = json.loads(r.read().decode())

        outputs = history.get(prompt_id, {}).get("outputs", {})
        # Find the SaveImage node output (node "7" in our workflow)
        for node_id, node_out in outputs.items():
            images = node_out.get("images", [])
            if images:
                img = images[0]
                view_url = (
                    f"{COMFYUI_HOST}/view"
                    f"?filename={img['filename']}"
                    f"&subfolder={img.get('subfolder', '')}"
                    f"&type={img.get('type', 'output')}"
                )
                with urllib.request.urlopen(view_url, timeout=30) as r:
                    output_path.write_bytes(r.read())
                return True
    except Exception as e:
        print(f"         [WARN] Could not fetch image: {e}")
    return False


# ── MAIN GENERATOR ────────────────────────────────────────────────────────────

def generate_images(story_id: str, only_scene: str | None, dry_run: bool,
                    width: int, height: int, steps: int, cfg: float):

    story_dir    = STORIES_DIR / story_id
    prompts_path = story_dir / "image_prompts.md"
    images_dir   = story_dir / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Biblical Storytelling -- Image Generator")
    print(f"{'='*60}")
    print(f"  Story    : {story_id}")
    print(f"  ComfyUI  : {COMFYUI_HOST}")
    print(f"  Size     : {width}x{height}  Steps: {steps}  CFG: {cfg}")
    print(f"  Output   : {images_dir}")
    if dry_run:
        print(f"  Mode     : DRY RUN (no images generated)")
    print(f"{'='*60}\n")

    if not prompts_path.exists():
        print(f"[ERROR] Prompts file not found: {prompts_path}")
        sys.exit(1)

    print("[1/3] Parsing image prompts...")
    scenes = parse_image_prompts(prompts_path)

    if not scenes:
        print("[ERROR] No scenes parsed from image_prompts.md. Check formatting.")
        sys.exit(1)

    if only_scene:
        scenes = [s for s in scenes if s["scene_id"] == only_scene]
        if not scenes:
            print(f"[ERROR] Scene '{only_scene}' not found in prompts file.")
            sys.exit(1)

    print(f"       Found {len(scenes)} prompts to generate.\n")

    if not dry_run:
        print("[2/3] Checking ComfyUI connection...")
        if not check_comfyui_running():
            print("[ERROR] ComfyUI is not running or not reachable at:")
            print(f"        {COMFYUI_HOST}\n")
            print("  HOW TO START COMFYUI:")
            print("  1. Open a terminal in your ComfyUI directory")
            print("  2. Run: python main.py --listen 0.0.0.0 --port 8188")
            print("  3. Wait for 'Starting server' message")
            print("  4. Re-run this script\n")
            print("  If ComfyUI is on a different port, edit COMFYUI_HOST in this file.")
            sys.exit(1)
        print("       ComfyUI is running.\n")

    results = []
    success_count = 0
    fail_count = 0

    print("[3/3] Generating images...\n")

    for i, scene in enumerate(scenes, 1):
        sid   = scene["scene_id"]
        title = scene["title"]
        # Output filename: scene_S01.png, scene_S02.png, etc.
        out_filename = f"scene_{sid}.png"
        out_path = images_dir / out_filename

        print(f"  [{i:02d}/{len(scenes):02d}] {sid} — {title}")
        print(f"          Mood: {scene['mood']}")

        if dry_run:
            print(f"          [DRY RUN] Would generate -> {out_filename}\n")
            results.append({"scene_id": sid, "status": "dry_run", "file": out_filename})
            continue

        if out_path.exists():
            print(f"          [SKIP] Already exists: {out_filename}\n")
            results.append({"scene_id": sid, "status": "skipped", "file": out_filename})
            success_count += 1
            continue

        try:
            filename_prefix = f"biblical_{story_id}_{sid}"
            workflow = build_sdxl_workflow(
                prompt=scene["prompt"],
                negative=DEFAULT_NEGATIVE,
                width=width, height=height,
                steps=steps, cfg=cfg,
                sampler=DEFAULT_SAMPLER,
                scheduler=DEFAULT_SCHEDULER,
                filename_prefix=filename_prefix
            )

            prompt_id = submit_prompt(workflow)
            print(f"          Queued (id: {prompt_id[:8]}...) — waiting...")

            done = poll_until_done(prompt_id)
            if not done:
                print(f"          [FAIL] Timed out after {POLL_TIMEOUT}s\n")
                fail_count += 1
                results.append({"scene_id": sid, "status": "timeout", "file": None})
                continue

            saved = fetch_output_image(prompt_id, out_path)
            if saved:
                size_kb = out_path.stat().st_size // 1024
                print(f"          [OK] Saved {out_filename} ({size_kb} KB)\n")
                success_count += 1
                results.append({"scene_id": sid, "status": "success", "file": str(out_path)})
            else:
                print(f"          [FAIL] Could not retrieve image from ComfyUI\n")
                fail_count += 1
                results.append({"scene_id": sid, "status": "fetch_failed", "file": None})

        except Exception as e:
            print(f"          [ERROR] {e}\n")
            fail_count += 1
            results.append({"scene_id": sid, "status": "error", "error": str(e), "file": None})

    print(f"{'='*60}")
    if dry_run:
        print(f"  [DRY RUN COMPLETE] {len(scenes)} prompts validated.")
    else:
        print(f"  [DONE] Success: {success_count}  Failed: {fail_count}")
    print(f"  Output dir: {images_dir}")
    print(f"{'='*60}\n")

    if not dry_run:
        log_entry = {
            "step":        "generate_images",
            "story_id":    story_id,
            "timestamp":   timestamp,
            "total":       len(scenes),
            "success":     success_count,
            "failed":      fail_count,
            "width":       width,
            "height":      height,
            "steps":       steps,
            "cfg":         cfg,
            "results":     results,
            "status":      "success" if fail_count == 0 else "partial"
        }
        append_pipeline_log(log_entry)
        print(f"  Pipeline log updated: {PIPELINE_LOG}")

        if success_count > 0:
            print(f"\n  NEXT STEP: python tools/compile_video.py --story {story_id}\n")


# ── PIPELINE LOG ──────────────────────────────────────────────────────────────

def append_pipeline_log(entry: dict):
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
        description="Generate SDXL images via ComfyUI for a biblical storytelling video.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/generate_images.py --story 001_witch_of_endor
  python tools/generate_images.py --story 001_witch_of_endor --dry-run
  python tools/generate_images.py --story 001_witch_of_endor --scene S03

Pipeline:
  generate_audio.py -> [generate_images.py] -> compile_video.py
        """
    )
    parser.add_argument("--story",   required=True, help="Story folder name, e.g. 001_witch_of_endor")
    parser.add_argument("--scene",   default=None,  help="Generate only one scene by ID, e.g. S03")
    parser.add_argument("--dry-run", action="store_true", help="Parse prompts and print plan without generating")
    parser.add_argument("--width",   type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height",  type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--steps",   type=int, default=DEFAULT_STEPS)
    parser.add_argument("--cfg",     type=float, default=DEFAULT_CFG)

    args = parser.parse_args()
    generate_images(
        story_id=args.story,
        only_scene=args.scene,
        dry_run=args.dry_run,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg=args.cfg
    )


if __name__ == "__main__":
    main()
