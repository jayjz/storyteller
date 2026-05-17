# SDXL Migration Guide

## What Changed

`generate_images.py` now supports both SDXL and Flux models. SDXL is the default.

### Before (Flux Only)
```bash
python tools/generate_images.py --story 001_witch_of_endor
# Required: flux1-schnell.safetensors + CLIP models (~22GB)
```

### After (SDXL Default)
```bash
python tools/generate_images.py --story 001_witch_of_endor
# Uses: juggernautXL_ragnarokBy.safetensors (or your SDXL model)
# Default size: 832x1216 (9:16 portrait for TikTok)
```

## New Features

1. **Auto-detect models**: Queries ComfyUI for available checkpoints
2. **Native portrait**: 832x1216 instead of 1024x1024 (no cropping needed)
3. **Better defaults**: 24 steps, CFG 6.0, DPM++ 2M Karras (optimized for quality)
4. **Model switching**:
   ```bash
   # Use specific checkpoint
   --checkpoint your-model.safetensors
   
   # Use Flux instead
   --model flux_schnell
   ```

## For Windows Users

If you have ComfyUI on Windows with SDXL models:

1. Start ComfyUI: `python main.py --listen 0.0.0.0 --port 8188`
2. Update `COMFYUI_HOST` in `generate_images.py` if needed (default: localhost:8188)
3. Run from WSL/Linux: `python tools/generate_images.py --story 001_witch_of_endor`

The script will auto-detect your available models.

## Testing

Test with 5 scenes first:
```bash
python tools/generate_images.py --story 001_witch_of_endor --max-scenes 5
```

Check output: `stories/001_witch_of_endor/assets/images/`
