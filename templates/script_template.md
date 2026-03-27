# Story NNN: [TITLE]
## TikTok Script — Kokoro TTS Optimized — [X] MIN VERSION
---
**RUNTIME TARGET:** X minutes
**WORD COUNT:** ~XXX words at 130 wpm
**VOICE MODEL:** Kokoro TTS — am_michael
**SPEED:** 0.92
**REFERENCE:** [Book Chapter:Verse]

---
## KOKORO DELIVERY NOTES
- Max 15 words per sentence
- Periods = natural pause. Use them aggressively.
- [pause] = hard 0.5 sec beat — use at dramatic turns
- Phonetics written inline for difficult biblical names
- Plain ASCII only — no em-dashes, semicolons, parentheses
- ALL CAPS = emphasis hint for Kokoro
- Ellipses (...) fine for trailing off

---

## PIPELINE MARKER REFERENCE

| Marker | Where it goes | Effect |
|--------|--------------|--------|
| `[pause]` | Inline in script body | Kokoro natural pause (~0.3s). Converted to `...` before TTS. |
| `[SILENCE: 1.0]` | Its own line in script body | Injects **1.0 seconds of actual silence** into the audio at that position (add_sfx.py). Also subtracted from video timing calculations (compile_video.py). Replace `1.0` with any decimal. |
| `[TEXT: "line here"]` | Its own line in script body | Burns text overlay onto the video frame for 2.5 seconds. Centered, white text, black shadow, semi-transparent box. Distributed evenly across video timeline. |
| `*[TEXT ON SCREEN: "..."]` | Stage directions (italic) | For the human editor / CapCut reference only — NOT parsed by any script. |

### Marker usage example
```
[SILENCE: 1.0]
[TEXT: "1 Kings 18 — Mount Carmel"]
It started with a challenge.
[pause]
Israel had abandoned God completely.
```
The `[SILENCE: 1.0]` creates 1 second of quiet in the audio.
The `[TEXT: ...]` burns a scripture reference onto the screen at that point in the video.
The `[pause]` tells Kokoro to breathe.

---
## FULL SCRIPT — TTS READY

*[TEXT ON SCREEN: "Opening hook text here."]*

[Hook line — 3 seconds max — must stop the scroll.]
[pause]
[Second hook line — complete the thought.]
[SILENCE: 1.0]
[TEXT: "Scripture reference"]

[ACT 1: Setup — fast sentences, short beats]
[pause]
[Keep each sentence under 15 words.]
[pause]
[SILENCE: 1.0]

[ACT 2: Rising action — medium pace]
[pause]
[TEXT: "Key quote or scripture"]
[The dramatic turn.]
[pause]
[SILENCE: 1.5]

[ACT 3: Climax — slowest section, most silence]
[pause]
[TEXT: "The line that lands hardest"]
[pause]
[Resolution line.]
[SILENCE: 1.0]
[pause]
[CTA — point to scripture, invite engagement.]

*[TEXT ON SCREEN: "Book Chapter — read it."]*

---
## COMMENT BAIT LINE
```
[One non-obvious detail that rewards viewers who comment — ask a question or drop a fact.]
```

---
## SERIES HOOK
```
Next: [One sentence teasing the next story — specific enough to create anticipation.]
```

---
## DIRECTOR NOTES
- **Hook [0:00–0:03]:** Text overlay appears BEFORE voice. Silence. Then speak.
- **Pacing:** Describe act-by-act pacing intent here.
- **Music:** Describe desired music bed character.
- **Visuals:** Describe key visual beats that need to sync to audio.
- **End card:** Channel name + subscribe CTA.
- **Captions:** Always on. Verify biblical names after auto-caption runs.

---
## KOKORO GENERATION SETTINGS
```
model: kokoro-v1.0
voice: am_michael
speed: 0.92
language: en-us
output: [story_slug]_tiktok.wav
```

---
## HASHTAG SET
```
#BibleStories #Christianity #OldTestament #FaithTok #ChristianTok
#HiddenHistory #BiblicalHistory #DidYouKnow #BibleFacts
#[StorySpecificTag1] #[StorySpecificTag2]
```
