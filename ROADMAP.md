# Storyteller Roadmap - TikTok Bible Stories Platform

**Project:** Autonomous biblical storytelling pipeline for viral TikTok content  
**Target:** 60-90 second cinematic Bible stories with consistent characters and mobile-first pacing  
**Current Status:** Phase 1 - Foundation (Audio pipeline validated, image/video generation pending)

---

## Phase 1: Foundation & End-to-End Validation (Weeks 1-2)

**Goal:** Get a complete story from script → published video, validate all systems work together

### 1.1 Pipeline Validation
- [ ] **Generate images for Story 001** (Witch of Endor)
  - Test Flux Schnell with current 1024×1024 settings
  - Validate 30 scenes generate without ComfyUI crashes
  - Check RTX 4060 VRAM usage (target: <7GB)
  - Document generation time per image
  - **Success criteria:** All 30 images generated, visually consistent style

- [ ] **Compile video for Story 001**
  - Run compile_video.py with 240s audio file
  - Validate FFmpeg zoompan works with generated images
  - Check output: 1080×1920, ~4 minute duration, proper audio sync
  - **Success criteria:** Complete MP4 exported, audio/video in sync

- [ ] **Pacing analysis & fix**
  - **Issue identified:** Audio is 240s but video compiler targets 55-65s
  - Audit script_tiktok.md word count vs. target duration
  - Decide: Truncate scripts to 90s OR expand video compiler to handle 3-4min
  - Update `get_clip_duration()` to distribute 240s across scenes properly
  - **Success criteria:** Video duration matches audio duration exactly

- [ ] **Quality validation checkpoint**
  - Watch complete video on mobile device
  - Check: Text readability, image clarity, pacing feels right
  - Document: What works, what feels slow/boring
  - **Success criteria:** Video is watchable start-to-finish without skipping

### 1.2 Technical Debt & Stability
- [ ] **Fix ComfyUI memory leaks**
  - Add explicit cleanup after each image generation
  - Implement retry logic for failed generations
  - Add VRAM monitoring to prevent OOM crashes

- [ ] **Pipeline error handling**
  - Add validation: Check all assets exist before starting each step
  - Add resume capability: If image 15/30 fails, resume at 15 not 1
  - Improve logging: Track which specific scenes fail and why

- [ ] **Documentation**
  - Document exact setup: ComfyUI version, model files required, VRAM requirements
  - Create quick-start guide for generating a new story
  - Document common failure modes and fixes

**Phase 1 Deliverable:** One complete, publishable Story 001 video (3-4 min version) with validated pipeline

---

## Phase 2: TikTok Optimization & Engagement (Weeks 3-5)

**Goal:** Transform 3-minute videos into 60-90 second viral TikToks with hooks, pacing, and mobile optimization

### 2.1 Image Generation Upgrade
- [ ] **Migrate Flux Schnell → Flux Dev**
  - Download `flux1-dev.safetensors` (~23GB)
  - Update `generate_images.py`: Change model, increase steps 10→24
  - Test quality improvement: Faces, hands, text rendering
  - Benchmark: Generation time increase (expect 2.5-3x slower)
  - **Trade-off:** Quality vs. speed - validate if RTX 4060 can handle it

- [ ] **Native 9:16 aspect ratio**
  - Change from 1024×1024 → 832×1216 (FLUX native portrait)
  - Update all image prompts to specify "portrait orientation, vertical composition"
  - Regenerate Story 001 images in new format
  - Update `compile_video.py` to remove cropping logic
  - **Benefit:** Better mobile composition, no awkward cropping

- [ ] **Character consistency system**
  - Create `characters/` directory with reference descriptions
  - Define Saul: Age, features, clothing, distinguishing marks
  - Update all prompts to include character reference block
  - Test: Generate S01, S15, S30 - verify same person appears
  - **Stretch goal:** Train LoRA for main characters (Saul, Samuel, David)

### 2.2 Video Assembly Overhaul
- [ ] **Dynamic motion system**
  - Replace static zoompan with parallax layers
  - Implement: Background (slow zoom), midground (medium), foreground (fast)
  - Add depth maps via MiDaS for automatic layer separation
  - Result: 3D-like movement from 2D images

- [ ] **TikTok pacing engine**
  - Create `tiktok_pacing.py`: Analyze audio, detect emphasis points
  - Hook (0-3s): Fast cuts, 1.5-2s per image, punchy motion
  - Build (3-30s): 2.5-3s per image, moderate movement
  - Climax (30-60s): 4-5s per image, dramatic camera moves
  - Outro (60-90s): 3s per image, resolve to end card

- [ ] **Audio-reactive effects**
  - Analyze audio amplitude envelope
  - On loud words: Increase zoom speed + add subtle shake
  - On pauses: Hold frame, slow zoom to create tension
  - Sync visual beats to speech rhythm

- [ ] **Transitions library**
  - Implement 5 transition types: Cut, dissolve, push, zoom blur, morph
  - Morph transitions for same-character scene changes (S01 → S01B)
  - Hard cuts for time/location jumps (S04 → S05)
  - Dissolves for emotional beats (S11 → S12)

### 2.3 Text & Captions System
- [ ] **Auto-caption generation**
  - Integrate Whisper to generate SRT from audio
  - Create `add_captions.py`: Burn captions into video
  - Style: Bold white text, black stroke, bottom-safe area
  - Timing: Word-level sync for karaoke-style highlighting

- [ ] **Hook text overlays**
  - Extract first 3 seconds of script
  - Generate bold text overlay: "A king who talked to the DEAD"
  - Animate: Scale up + bounce on key words
  - Position: Top third (doesn't obscure main action)

- [ ] **Emphasis effects**
  - Detect keywords: "REJECTED", "SILENCE", "TERRIFIED"
  - On these words: Text pops in large, screen shakes slightly
  - Color pulse: White → yellow → white over 0.3s
  - Adds visual punch to match vocal emphasis

### 2.4 Script Optimization
- [ ] **Create 90-second TikTok scripts**
  - Current scripts are 3-4 minutes (YouTube length)
  - Extract core narrative: Hook → Conflict → Climax → Resolution
  - Target: 180-200 words @ 130 WPM = 90 seconds
  - Preserve: Emotional beats, key dialogue, dramatic tension
  - Cut: Extended descriptions, secondary details

- [ ] **A/B test script structures**
  - Version A: Chronological (current)
  - Version B: Start with climax, then flashback
  - Version C: Mystery hook ("He did the unthinkable...")
  - Test all 3 with same story, measure retention

**Phase 2 Deliverable:** Story 001 reprocessed as 75-second TikTok with dynamic motion, captions, and optimized pacing. Target: 50%+ average watch time.

---

## Phase 3: Scale, Automation & Publishing (Weeks 6-8)

**Goal:** Generate 3 stories per week with minimal manual intervention, auto-publish to TikTok

### 3.1 Batch Processing System
- [ ] **Parallel generation queue**
  - Refactor `run_pipeline.py` to support multiple stories
  - Implement job queue: Stories wait for ComfyUI, process sequentially
  - Add: `python tools/batch_generate.py --stories 001,002,003 --step images`
  - Overnight processing: Queue 5 stories, wake up to completed images

- [ ] **Template system**
  - Create story template: Folder structure, placeholder scripts
  - Command: `python tools/scaffold_story.py --title "David and Goliath" --passage "1 Samuel 17"`
  - Auto-generates: Folder, script template, image prompt template
  - Reduces setup time from 30 min → 2 min

- [ ] **Smart regeneration**
  - Track which images are "good" vs "needs redo"
  - Command: `python tools/regenerate.py --story 001 --scenes S07,S12,S18 --reason "character inconsistent"`
  - Only regenerates specific scenes, preserves good ones
  - Maintains scene numbering and pipeline state

### 3.2 Quality Assurance Pipeline
- [ ] **Automated quality checks**
  - Image check: Detect blurry images, malformed hands, off-model faces
  - Audio check: Verify duration matches script, detect clipping
  - Video check: Validate output resolution, frame rate, audio sync
  - Flag issues before human review

- [ ] **Human review interface**
  - Simple web UI: Shows each scene, allows approve/reject/regenerate
  - Keyboard shortcuts: ← → navigate, A approve, R reject, Space play/pause
  - Export: Generates report of what needs fixing

- [ ] **Version control for assets**
  - Git LFS for images/videos (or separate storage)
  - Track: `story_001_v1/`, `story_001_v2/` for iterations
  - Ability to rollback to previous version if new one is worse

### 3.3 Publishing Automation
- [ ] **TikTok API integration**
  - Research: TikTok Business API for video uploads
  - Implement: `python tools/publish.py --story 001 --platform tiktok`
  - Auto-fill: Title, description, hashtags, schedule time
  - Handle: Authentication, rate limits, error retries

- [ ] **Multi-platform export**
  - TikTok: 1080×1920, 75s, with captions
  - YouTube Shorts: Same as TikTok (reupload)
  - Instagram Reels: 1080×1920, add safe-zone guides
  - YouTube Long: 1920×1080, 8-12 min version with extended script

- [ ] **Analytics tracking**
  - Scrape TikTok analytics: Views, watch time, completion rate
  - Log to: `analytics/story_001_tiktok.csv`
  - Track: Which stories perform best, optimal posting times
  - Use data to inform future story selection

### 3.4 Advanced Features (Stretch Goals)
- [ ] **Voice cloning for characters**
  - Train voice models: Saul (authoritative), Samuel (aged prophet), Narrator
  - Use Supertonic voice cloning or F5-TTS
  - Generate dialogue with character-appropriate voices

- [ ] **Dynamic thumbnail generation**
  - Auto-generate 3 thumbnail variants per story
  - A/B test via TikTok's thumbnail selector
  - Track which style gets better CTR

- [ ] **Community features**
  - Allow viewers to request next story via comments
  - Parse comments, tally requests, auto-prioritize queue
  - "You asked for it: Story 007 - Balaam's Donkey"

**Phase 3 Deliverable:** Automated pipeline generating 3 stories/week with <2 hours human time per story. Publishing directly to TikTok with analytics tracking.

---

## Success Metrics

### Phase 1 (Validation)
- [ ] 1 complete story published
- [ ] Pipeline runs end-to-end without manual intervention
- [ ] Video quality: 1080×1920, clear audio, in sync

### Phase 2 (Optimization)
- [ ] Average watch time: 50%+ (TikTok benchmark: 40% is good)
- [ ] Completion rate: 30%+ viewers watch to end
- [ ] Character consistency: Same character recognizable across all scenes

### Phase 3 (Scale)
- [ ] Production rate: 3 stories per week
- [ ] Human time per story: <2 hours (review + tweaks only)
- [ ] Publishing: Zero-touch auto-upload to TikTok

---

## Technical Requirements

### Hardware
- **Current:** RTX 4060 8GB, 32GB RAM
- **Phase 1:** Sufficient for Flux Schnell
- **Phase 2:** May need upgrade for Flux Dev (12GB+ VRAM recommended)
- **Alternative:** RunPod/ Vast.ai for heavy generation ($0.50-1.00/hr)

### Software Dependencies
- ComfyUI with Flux models
- FFmpeg 6.0+
- Python 3.10+
- Supertonic TTS (installed)
- Whisper (for captions)
- MiDaS (for depth maps - Phase 2)

### Storage
- Per story: ~2GB (30 images @ 2MB + audio @ 20MB + video @ 50MB)
- 100 stories: ~200GB
- Recommendation: External SSD or cloud storage

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| ComfyUI crashes mid-generation | High | Implement checkpointing, resume from last success |
| Flux Dev too slow on 4060 | Medium | Keep Schnell as fallback, or use cloud GPU |
| TikTok API changes | Medium | Maintain manual upload as backup |
| Character inconsistency | High | Strict prompt engineering + LoRA training |
| Audio/video sync drift | Medium | Use FFmpeg concat demuxer, validate durations |

---

## Next Actions (This Week)

1. **Generate images for Story 001** - Test current pipeline, identify bottlenecks
2. **Compile test video** - Validate pacing, measure actual vs. target duration
3. **Decide: 90s vs 4min format** - Determines all future script writing
4. **Document findings** - Update this roadmap with real-world timings

---

*Last updated: 2026-05-17*  
*Status: Phase 1 in progress - Audio complete, images pending*  
*Owner: @jayjz*  
*Repository: github.com/jayjz/storyteller*