"""
generate_images.py - SDXL Edition (with Flux support)
Supports both SDXL and Flux models via ComfyUI
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
COMFYUI_HOST = "http://127.0.0.1:8188"

POLL_INTERVAL = 3
POLL_TIMEOUT  = 300

# SDXL Defaults (optimized for RTX 4060 8GB)
DEFAULT_WIDTH     = 832
DEFAULT_HEIGHT    = 1216  # 9:16 portrait for TikTok
DEFAULT_STEPS     = 24
DEFAULT_CFG       = 6.0
DEFAULT_SAMPLER   = "dpmpp_2m"
DEFAULT_SCHEDULER = "karras"

# Model configurations
MODEL_CONFIGS = {
    "sdxl": {
        "checkpoint": "juggernautXL_ragnarokBy.safetensors",  # User's available model
        "vae": "sdxl_vae.safetensors",
        "width": 832,
        "height": 1216,
        "steps": 24,
        "cfg": 6.0,
    },
    "flux_schnell": {
        "unet": "flux1-schnell.safetensors",
        "clip1": "t5xxl_fp8_e4m3fn.safetensors",
        "clip2": "clip_l.safetensors",
        "vae": "ae.safetensors",
        "width": 1024,
        "height": 1024,
        "steps": 10,
        "cfg": 1.0,
    }
}

DEFAULT_NEGATIVE = (
    "fantasy armor, plate armor too advanced, anachronistic clothing, modern faces, "
    "anime, cartoon, illustration, low quality, blurry, deformed hands, extra limbs, "
    "text, watermark, signature, overexposed, underexposed, Hollywood armor, glowing weapons, "
    "bad anatomy, distorted, deformed, disfigured, duplicate, mutation, ugly"
)

# ── IMPROVED PARSER ───────────────────────────────────────────────────────
def parse_image_prompts(prompts_path: Path) -> list[dict]:
    raw = prompts_path.read_text(encoding="utf-8")
    scenes = []
    
    blocks = re.split(r"\n(?=## S|\n## THUMBNAIL)", raw, flags=re.IGNORECASE)

    for block in blocks:
        if not block.strip():
            continue

        header = block.splitlines()[0].strip()
        scene_match = re.match(r"^## (S\d+[A-Z]?|THUMBNAIL)\s*[-—:]\s*(.+)$", header, re.IGNORECASE)
        if not scene_match:
            continue

        scene_id = scene_match.group(1).strip().upper().replace(" ", "_")
        title    = scene_match.group(2).strip()

        code_match = re.search(r"```\s*\n?([\s\S]+?)\n?```", block)
        if code_match:
            prompt = code_match.group(1).strip()
        else:
            prompt = "\n".join(block.splitlines()[1:]).strip()

        prompt = re.sub(r"(?m)^text\s*$", "", prompt)
        prompt = prompt.replace("text**", "**").strip()

        shot_match = re.search(r"\*\*Shot:\*\*\s*(.+)", block, re.IGNORECASE)
        mood_match = re.search(r"\*\*Mood:\*\*\s*(.+)", block, re.IGNORECASE)

        if prompt:
            scenes.append({
                "scene_id": scene_id,
                "title":    title,
                "prompt":   prompt,
                "shot":     shot_match.group(1).strip() if shot_match else "",
                "mood":     mood_match.group(1).strip() if mood_match else "",
            })

    print(f"Parsed {len(scenes)} scenes from {prompts_path.name}")
    return scenes


# ── SDXL WORKFLOW ───────────────────────────────────────────────────────
def build_sdxl_workflow(prompt: str, negative: str, width: int, height: int,
                       steps: int, cfg: float, seed: int, filename_prefix: str,
                       checkpoint: str = None) -> dict:
    """Build ComfyUI workflow for SDXL"""
    if checkpoint is None:
        checkpoint = MODEL_CONFIGS["sdxl"]["checkpoint"]
    
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint
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
                "width": width,
                "height": height,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": DEFAULT_SAMPLER,
                "scheduler": DEFAULT_SCHEDULER,
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": filename_prefix,
                "images": ["6", 0]
            }
        }
    }


# ── FLUX WORKFLOW (kept for compatibility) ──────────────────────────────
def build_flux_workflow(prompt: str, negative: str, width: int, height: int,
                       steps: int, cfg: float, filename_prefix: str) -> dict:
    """Build ComfyUI workflow for Flux"""
    config = MODEL_CONFIGS["flux_schnell"]
    return {
        "1": {"class_type": "DualCLIPLoader", "inputs": {
            "clip_name1": config["clip1"],
            "clip_name2": config["clip2"],
            "type": "flux"
        }},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["1", 0]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["1", 0]}},
        "4": {"class_type": "UNETLoader", "inputs": {
            "unet_name": config["unet"],
            "weight_dtype": "fp8_e4m3fn"
        }},
        "5": {"class_type": "EmptyLatentImage", "inputs": {
            "width": width, "height": height, "batch_size": 1
        }},
        "6": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["5", 0], "seed": int(time.time() * 1000) % (2**32),
            "steps": steps, "cfg": cfg, "sampler_name": "euler",
            "scheduler": "beta", "denoise": 1.0
        }},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["8", 0]}},
        "8": {"class_type": "VAELoader", "inputs": {"vae_name": config["vae"]}},
        "9": {"class_type": "SaveImage", "inputs": {
            "images": ["7", 0], "filename_prefix": filename_prefix
        }}
    }


# ── COMFYUI HELPERS ───────────────────────────────────────────────────────
def check_comfyui_running() -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"{COMFYUI_HOST}/system_stats", timeout=5) as r:
            return r.status == 200
    except Exception:
        return False


def get_available_models() -> dict:
    """Query ComfyUI for available models"""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{COMFYUI_HOST}/object_info", timeout=10) as r:
            info = json.loads(r.read().decode())
        
        models = {
            "checkpoints": [],
            "unet": [],
            "clip": [],
            "vae": []
        }
        
        if "CheckpointLoaderSimple" in info:
            models["checkpoints"] = info["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"][0]
        if "UNETLoader" in info:
            models["unet"] = info["UNETLoader"]["input"]["required"]["unet_name"][0]
        
        return models
    except Exception as e:
        print(f"Warning: Could not query models: {e}")
        return {}


def submit_prompt(workflow: dict) -> str:
    import urllib.request
    payload = json.dumps({"prompt": workflow, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(f"{COMFYUI_HOST}/prompt", data=payload,
                                headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())["prompt_id"]


def poll_until_done(prompt_id: str) -> bool:
    import urllib.request
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{COMFYUI_HOST}/history/{prompt_id}", timeout=10) as r:
                history = json.loads(r.read().decode())
            if prompt_id in history:
                return True
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)
    return False


def fetch_output_image(prompt_id: str, output_path: Path) -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen(f"{COMFYUI_HOST}/history/{prompt_id}", timeout=10) as r:
            history = json.loads(r.read().decode())
        outputs = history.get(prompt_id, {}).get("outputs", {})
        for node_out in outputs.values():
            images = node_out.get("images", [])
            if images:
                img = images[0]
                view_url = f"{COMFYUI_HOST}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type={img.get('type','output')}"
                with urllib.request.urlopen(view_url, timeout=30) as r:
                    output_path.write_bytes(r.read())
                return True
    except Exception as e:
        print(f"         [WARN] Could not fetch image: {e}")
    return False


# ── MAIN GENERATOR ─────────────────────────────────────────────────────────
def generate_images(story_id: str, only_scene: str | None, dry_run: bool,
                    width: int, height: int, steps: int, cfg: float, 
                    max_scenes: int | None, model_type: str = "sdxl",
                    checkpoint: str = None):

    story_dir    = STORIES_DIR / story_id
    prompts_path = story_dir / "image_prompts.md"
    images_dir   = story_dir / "assets" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get model config
    if model_type == "sdxl":
        config = MODEL_CONFIGS["sdxl"]
        if checkpoint:
            config["checkpoint"] = checkpoint
        model_name = config["checkpoint"]
    else:
        config = MODEL_CONFIGS["flux_schnell"]
        model_name = config["unet"]

    print(f"\n{'='*70}")
    print(f"  Biblical Storytelling — Image Generator")
    print(f"{'='*70}")
    print(f"  Story     : {story_id}")
    print(f"  Model     : {model_type.upper()} - {model_name}")
    print(f"  Size      : {width}x{height} | Steps: {steps} | CFG: {cfg}")
    if max_scenes:
        print(f"  Max Scenes: {max_scenes} (limiting output)")
    print(f"  Output    : {images_dir}")
    if dry_run:
        print(f"  Mode      : DRY RUN")
    print(f"{'='*70}\n")

    if not prompts_path.exists():
        print(f"[ERROR] Prompts file not found: {prompts_path}")
        sys.exit(1)

    scenes = parse_image_prompts(prompts_path)
    if not scenes:
        print("[ERROR] No scenes parsed.")
        sys.exit(1)

    if max_scenes:
        scenes = scenes[:max_scenes]

    if only_scene:
        scenes = [s for s in scenes if s["scene_id"] == only_scene.upper()]

    if not dry_run:
        if not check_comfyui_running():
            print("[ERROR] ComfyUI is not running!")
            print("Start it with: python main.py --listen 0.0.0.0 --port 8188")
            sys.exit(1)
        
        # Check available models
        models = get_available_models()
        if models.get("checkpoints"):
            print(f"Available checkpoints: {', '.join(models['checkpoints'][:3])}...")
            if model_type == "sdxl" and config["checkpoint"] not in models["checkpoints"]:
                print(f"\n[WARNING] Configured checkpoint '{config['checkpoint']}' not found!")
                print(f"Available: {models['checkpoints']}")
                print("Use --checkpoint to specify a different model\n")

    results = []
    success_count = fail_count = 0

    for i, scene in enumerate(scenes, 1):
        sid = scene["scene_id"]
        out_filename = f"scene_{sid}.png"
        out_path = images_dir / out_filename

        print(f"  [{i:02d}/{len(scenes):02d}] {sid} — {scene['title']}")

        if dry_run:
            print(f"          [DRY RUN] Would generate {out_filename}")
            success_count += 1
            continue
        
        if out_path.exists():
            print(f"          [SKIP] Already exists")
            success_count += 1
            continue

        try:
            filename_prefix = f"biblical_{story_id}_{sid}"
            seed = int(time.time() * 1000) % (2**32) + i
            
            # Build workflow based on model type
            if model_type == "sdxl":
                workflow = build_sdxl_workflow(
                    prompt=scene["prompt"] + ", " + scene.get("mood", ""),
                    negative=DEFAULT_NEGATIVE,
                    width=width, height=height,
                    steps=steps, cfg=cfg, seed=seed,
                    filename_prefix=filename_prefix,
                    checkpoint=config["checkpoint"]
                )
            else:
                workflow = build_flux_workflow(
                    prompt=scene["prompt"] + ", " + scene.get("mood", ""),
                    negative=DEFAULT_NEGATIVE,
                    width=width, height=height,
                    steps=steps,
                    filename_prefix=filename_prefix
                )

            prompt_id = submit_prompt(workflow)
            print(f"          Queued → waiting...")
            if poll_until_done(prompt_id):
                if fetch_output_image(prompt_id, out_path):
                    size_kb = out_path.stat().st_size // 1024
                    print(f"          ✓ Saved {out_filename} ({size_kb} KB)\n")
                    success_count += 1
                else:
                    print(f"          ✗ Failed to fetch image\n")
                    fail_count += 1
            else:
                print(f"          ✗ Timeout\n")
                fail_count += 1
                
            # Brief pause to avoid overwhelming ComfyUI
            time.sleep(1)
            
        except Exception as e:
            print(f"          ✗ ERROR: {e}\n")
            fail_count += 1

    print(f"{'='*70}")
    print(f"  DONE — Success: {success_count} | Failed: {fail_count}")
    print(f"{'='*70}\n")

    if success_count > 0:
        print(f"  NEXT: python tools/compile_video.py --story {story_id}\n")


# ── CLI ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate images via ComfyUI (SDXL or Flux)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # SDXL with default checkpoint
  python tools/generate_images.py --story 001_witch_of_endor
  
  # SDXL with specific checkpoint
  python tools/generate_images.py --story 001_witch_of_endor --checkpoint juggernautXL_ragnarokBy.safetensors
  
  # Flux Schnell
  python tools/generate_images.py --story 001_witch_of_endor --model flux_schnell
  
  # Test with 5 scenes only
  python tools/generate_images.py --story 001_witch_of_endor --max-scenes 5
  
  # Regenerate single scene
  python tools/generate_images.py --story 001_witch_of_endor --scene S07
        """
    )
    parser.add_argument("--story", required=True, help="Story folder name")
    parser.add_argument("--scene", default=None, help="Generate single scene (e.g., S07)")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, don't generate")
    parser.add_argument("--width", type=int, default=None, help="Image width")
    parser.add_argument("--height", type=int, default=None, help="Image height")
    parser.add_argument("--steps", type=int, default=None, help="Sampling steps")
    parser.add_argument("--cfg", type=float, default=None, help="CFG scale")
    parser.add_argument("--max-scenes", type=int, default=None, help="Limit to first N scenes")
    parser.add_argument("--model", choices=["sdxl", "flux_schnell"], default="sdxl",
                       help="Model type (default: sdxl)")
    parser.add_argument("--checkpoint", default=None,
                       help="SDXL checkpoint filename (overrides default)")

    args = parser.parse_args()

    # Use defaults from model config if not specified
    config = MODEL_CONFIGS[args.model]
    width = args.width or config["width"]
    height = args.height or config["height"]
    steps = args.steps or config["steps"]
    cfg = args.cfg or config["cfg"]

    generate_images(
        story_id=args.story,
        only_scene=args.scene,
        dry_run=args.dry_run,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        max_scenes=args.max_scenes,
        model_type=args.model,
        checkpoint=args.checkpoint
    )

if __name__ == "__main__":
    main()