File to replace: stories/001_witch_of_endor/image_prompts.md

This single command rewrites the entire file with all 30 scenes (30 × 6s = 3 min) plus all 6 fixes baked in:
bash

python - << 'PYEOF'
content = """# Story 001: The Witch of Endor
## Image Prompts — v3 (3-min script, 30 scenes, 6s each)

### Style Foundation (apply to every prompt)
biblical epic oil painting, Rembrandt chiaroscuro lighting, cinematic composition, ancient Levant 11th century BCE, photorealistic painting, masterwork quality, deep shadows, warm amber and gold tones

### Negative Prompt (apply to all)
modern clothing, fantasy aesthetic, Halloween witch, cartoon, anime, watermark, text, logo, low quality, blurry, extra limbs, deformed hands, medieval European architecture, carved stone reliefs

---

## S01 — Hook / The Weight of What Is Coming
```
A vast ancient valley at dusk seen from a high rocky ridge, two hillsides visible in the far distance with tiny campfires beginning to light on both sides, the valley between them dark and empty and silent, a lone cloaked figure standing at the ridge edge with his back to the viewer looking down, the scale of what he faces dwarfing him completely, deep purple and amber sky, the last light dying on the horizon, sense of inevitable doom, biblical epic oil painting, Rembrandt lighting, cinematic wide establishing shot, ancient Levant, masterwork quality
```
**Shot:** Epic wide — lone figure vs impossible scale
**Mood:** Doom before we know the story

---

## S01B — Saul's Face / The Man Behind the Cloak
```
Extreme close-up portrait of a weathered bearded man in his fifties, strong jaw, dark exhausted eyes staring into the far distance, deep lines of suffering carved into his face, the remnants of former greatness still visible in his bearing, amber and purple dusk light on one side of his face, deep shadow on the other, the face of a man who has lost everything and knows it, no crown no armor just a man, biblical epic oil painting, Rembrandt extreme close-up lighting, cinematic portrait shot, ancient Levant, 11th century BCE, masterwork quality
```
**Shot:** Extreme close-up portrait
**Mood:** The human cost of what is coming

---

## S02 — Saul at His Peak / The Chosen King
```
A tall commanding Israelite king in his prime standing on a rock before a vast assembled army on an open plain, wearing ornate Iron Age bronze armor and a deep crimson robe, arms slightly raised in address, thousands of soldiers stretching to the horizon behind him, morning golden light pouring from the left illuminating his face and armor, his expression confident and powerful, the posture of a man chosen by God, dramatic clouds above, biblical epic oil painting, Rembrandt lighting, cinematic low-angle hero shot, ancient Levant, 11th century BCE, masterwork quality
```
**Shot:** Low angle hero — Saul at his greatest
**Mood:** Power, divine favor, the height before the fall

---

## S02B — The Army Cheers / The Kingdom at Full Strength
```
Thousands of Israelite soldiers raising spears and shields in a roaring cheer on an open plain, the crowd of warriors stretching from foreground to horizon, dust rising from the movement, morning golden light flashing off bronze weapons and helmets, the energy of a victorious people at their strongest, banners catching the wind, the scale communicating a nation at its peak, biblical epic oil painting, Rembrandt lighting, cinematic extreme wide shot looking along the length of the army, ancient Levant plain, 11th century BCE, masterwork quality
```
**Shot:** Extreme wide — the full power of Israel
**Mood:** Peak glory that makes the fall more devastating

---

## S03 — The Disobedience / Keeping the Spoils
```
An Israelite king in battle-worn bronze armor standing among the spoils of war on a dusty plain, large flocks of sheep and cattle being herded behind him by soldiers, his expression self-satisfied and proud, holding his spear loosely at his side, the sun harsh and high overhead, dust in the air, soldiers celebrating in the background, the image suggests triumph but carries a wrongness, biblical epic oil painting, Rembrandt harsh midday lighting, cinematic medium shot, ancient Levant desert plain, 11th century BCE, masterwork quality
```
**Shot:** Medium — the moment of disobedience made visible
**Mood:** False triumph, the pride that breaks everything

---

## S03B — Agag in Chains / The Trophy King
```
A foreign king in once-fine robes now torn and dirty kneeling in chains on dusty ground, his head bowed, his crown removed and discarded beside him in the dirt, Israelite soldiers standing guard on both sides, the captured king communicating humiliation and defeat, harsh afternoon light, the image represents Saul keeping what God said to destroy, biblical epic oil painting, Rembrandt harsh lighting, cinematic medium shot, ancient Levant, 11th century BCE, masterwork quality
```
**Shot:** Medium — the captured king Saul should have killed
**Mood:** The specific act of disobedience that ended everything

---

## S04 — Samuel Confronts Saul / The Verdict
```
An elderly white-haired prophet in rough dark robes standing face to face with a tall armored king on a completely empty dusty road between rocky hills, no crowd no city no gates, only two men and open land, the prophet's expression grave and unflinching and utterly certain, his right hand raised in pronouncement, the king's face showing dawning horror, the loneliness of the scene amplifying the weight of the verdict, late afternoon golden light casting long shadows, dust in the still air, biblical epic oil painting, Rembrandt chiaroscuro, cinematic tight two-shot, ancient Levant open road, 11th century BCE, masterwork quality
```
**Shot:** Tight two-shot — just prophet and king, empty road
**Mood:** Divine judgment in total isolation

---

## S04B — Samuel Walks Away / The Final Silence
```
An elderly white-haired prophet in dark rough robes walking away down a dusty road, his back to the viewer, not looking back, his posture deliberate and final, a tall figure in armor visible in the background watching him go, frozen in place unable to follow, the prophet growing smaller as the road stretches ahead, the space between the two figures communicating permanent separation, late afternoon harsh light, long shadows, biblical epic oil painting, Rembrandt lighting, cinematic over-shoulder shot from behind the king watching Samuel leave, ancient Levant road, masterwork quality
```
**Shot:** Over-shoulder — watching Samuel leave, not looking back
**Mood:** Irreversible, the last moment of contact with God

---

## S05 — The Robe Tears / The Kingdom Lost
```
Extreme close-up on two pairs of hands, one large desperate hand gripping dark rough prophet's fabric, the fabric visibly mid-tear between the two hands, a long ragged strip of dark cloth separating under the tension, dust particles in the harsh light, the physical tear is the entire subject of the image, nothing else in frame except hands and tearing cloth, the metaphor of a kingdom being torn away made viscerally physical, biblical epic oil painting, Rembrandt extreme close-up lighting, macro cinematic composition, ancient rough-woven fabric, 11th century BCE, masterwork quality
```
**Shot:** Extreme macro — hands and tearing fabric only
**Mood:** The physical moment the kingdom was torn away

---

## S05B — Saul Watching / The Fabric in His Hand
```
Close-up on a tall armored king's face, his eyes devastated and hollow, looking down at something in his hand, in the lower portion of the frame a torn strip of dark rough fabric hanging from his clenched fist, the prophet no longer present, just the king and the fragment of what he destroyed, harsh afternoon light, deep shadows under his eyes, the face of a man who has just understood what he has done, biblical epic oil painting, Rembrandt close-up lighting, cinematic tight portrait, ancient Levant, 11th century BCE, masterwork quality
```
**Shot:** Close-up portrait — the torn fabric in his hand
**Mood:** The moment of full understanding, too late

---

## S06 — The Divine Silence / Saul Prays Alone
```
A king alone inside a large dark war tent at night, kneeling on bare ground with his head bowed and hands pressed together, wearing simple robes not armor, a single clay oil lamp burning low casting a small circle of warm light in the overwhelming darkness, the entrance of the tent slightly open showing only darkness outside, no one else present, the emptiness of the tent emphasized, his posture one of complete desperation and exhaustion, the silence of the image is total, biblical epic oil painting, Rembrandt chiaroscuro, cinematic tight medium shot, ancient Levant interior, 11th century BCE, masterwork quality
```
**Shot:** Tight medium — king alone, swallowed by darkness
**Mood:** Complete desolation, unanswered prayer

---

## S06B — The Priests Shake Their Heads / No Answer
```
Three Israelite priests in white linen robes standing together inside a tent at night, their expressions troubled and helpless, one shaking his head slowly, another looking at the ground, the third with his hands open in a gesture of having nothing to give, an altar with unlit incense behind them, the absence of divine fire or sign implicit, a figure in shadow in the foreground waiting for an answer that does not come, warm lamp light, deep shadows, biblical epic oil painting, Rembrandt lighting, cinematic medium shot, ancient Levant tent interior, masterwork quality
```
**Shot:** Medium — priests with nothing to offer
**Mood:** The silence made institutional, even the priests have nothing

---

## S07 — The Philistine Army / The Valley of Dread
```
An enormous army assembled in a valley at golden hour, thousands of soldiers with iron weapons and patterned shields stretching from foreground to horizon in both directions, military banners catching the wind, the sheer number of soldiers making the viewer feel the impossibility of what faces Saul, the scale is overwhelming and terrifying, dramatic golden afternoon light with deep shadows in the valley, dust rising from thousands of feet, biblical epic oil painting, Rembrandt lighting, cinematic extreme wide shot from a high hillside looking down at the full army, ancient Levant valley, 11th century BCE, masterwork quality
```
**Shot:** Extreme wide — the full impossible scale of the enemy
**Mood:** Dread, military inevitability

---

## S07B — Saul Sees the Army / The Terror
```
Close-up on a weathered bearded king's face in profile at the edge of a ridge, his eyes fixed on something below in absolute terror, his jaw set, the color drained from his face, the muscles of his neck rigid, behind him dark sky and the edge of rocky ground, below and ahead of him only implied by the direction of his gaze and his expression, the face of a man who knows he cannot win, biblical epic oil painting, Rembrandt side lighting, cinematic extreme close-up profile, ancient Levant hilltop, 11th century BCE, masterwork quality
```
**Shot:** Close profile — the terror on his face
**Mood:** The moment he knows it is over

---

## S08 — Saul Removes His Crown / The Disguise
```
A tall broad-shouldered king standing alone inside a dark tent at night, in the act of lifting his royal crown from his head with both hands and looking at it one final time, his expression complicated grief and shame and desperation, plain rough travelling robes laid out beside him replacing the royal garments, the crown catching the last of the lamplight as it leaves his head, the image communicating the profound humiliation of what he is about to do, a single oil lamp, deep shadows, biblical epic oil painting, Rembrandt intimate lighting, cinematic medium shot, ancient Levant tent interior, masterwork quality
```
**Shot:** Medium — crown lifted from head, the last look
**Mood:** Humiliation, desperation, the king becoming a fugitive

---

## S08B — Crossing Enemy Lines / The Night Road
```
A lone cloaked figure moving through deep darkness on a narrow dirt road between rocky hills at deep night, the figure hunched and furtive in plain rough robes deliberately concealing himself, only a sliver of crescent moon lighting the road, distant campfires of an enemy army visible on the hillside to the right, the figure's posture communicating both urgency and terror, the profound humiliation of a disguised king on foot in enemy territory, the road ahead disappearing into impenetrable darkness, biblical epic oil painting, Rembrandt nocturnal lighting, cinematic medium shot from behind, ancient Levant night road, masterwork quality
```
**Shot:** Behind and above — lone figure in enemy darkness
**Mood:** Furtive, terrified, a king reduced to a shadow

---

## S09 — The Woman of En-dor / The Door in the Dark
```
A gaunt hollow-cheeked Israelite woman of middle age standing squarely in a low ancient stone doorway at deep night facing outward, holding a clay oil lamp at chest height lighting her face from below with warm orange light, wild silver-gray hair loose around her face, deep-set dark suspicious eyes staring directly outward, strong nose, age-lined face, worn dark rough linen robes, her body filling and blocking the doorway protectively, two cloaked figures visible in the outer darkness whose faces are completely hidden in shadow and hood, the void of darkness behind the visitors absolute and threatening, biblical epic oil painting, Rembrandt chiaroscuro, cinematic shot from outside looking in at her in the doorway, ancient Levant stone dwelling, 11th century BCE, masterwork quality
```
**Shot:** From outside — her lit face, visitors in shadow
**Mood:** Suspicion, fear, the forbidden meeting

---

## S09B — Inside / The Recognition
```
The gaunt silver-gray-haired woman of En-dor inside her low stone room, her face in sudden horrified recognition, eyes wide and hand going to her mouth, staring at a tall cloaked figure whose hood has slipped slightly revealing enough of a strong jaw and bearing to be unmistakable, the lamp between them casting warm light on both faces, her expression communicating that she knows exactly who is standing in her home and what that means for her life, biblical epic oil painting, Rembrandt intimate lighting, cinematic tight two-shot, ancient Levant stone interior, masterwork quality
```
**Shot:** Tight two-shot — the moment of recognition
**Mood:** Horror, the trap she is in

---

## S10 — The Summoning Ritual
```
The gaunt hollow-cheeked silver-gray-haired woman of En-dor performing a ritual in a low ancient stone room, both arms raised with palms up, eyes closed and face strained with fierce concentration, small fire burning very low before her casting red and orange light upward onto her face, deep black shadows filling the room, ritual objects arranged on the stone floor around the fire, a cloaked figure pressed back against the far stone wall watching, the air feels charged and wrong, a cold pale quality beginning to enter the light at the edges of the frame, biblical epic oil painting, Rembrandt chiaroscuro, cinematic close-up on the woman, ancient Levant stone interior, masterwork quality
```
**Shot:** Close-up on the woman mid-ritual
**Mood:** The moment before the supernatural rupture

---

## S10B — The Fire Goes Cold / The Light Changes
```
A low stone room interior, a small ritual fire in the foreground whose orange flames are visibly changing color at the edges from warm orange to a cold unnatural pale blue-white, the warm amber light of the room being slowly invaded by the cold light from an unseen source, ritual objects on the stone floor casting two kinds of shadow warm and cold simultaneously, the stone walls showing the shift from firelight to something else entirely, no figures visible only the changing light itself, biblical epic oil painting, cinematic detail shot, ancient Levant stone interior, the visual moment the supernatural enters, masterwork quality
```
**Shot:** Detail — the fire changing, the room changing
**Mood:** The threshold crossing, the world shifting

---

## S11 — The Woman Screams / Recognition
```
The gaunt silver-gray-haired woman of En-dor violently recoiling backward away from the left side of the frame, her body weight thrown backward, mouth wide open in a raw scream, eyes wide with genuine animal terror staring at the left side where a cold pale silver-white light emanates from just outside the frame, one arm thrown up defensively palm outward, her warm orange lamplight overwhelmed by the invading cold light, the contrast between warm firelight and cold supernatural light splitting the image, a cloaked figure pressed flat against the back wall in absolute stillness, biblical epic oil painting, Rembrandt chiaroscuro with cold supernatural light intrusion, cinematic tight medium shot, ancient Levant stone interior, 11th century BCE, masterwork quality
```
**Shot:** Tight medium — screaming, recoiling from cold light
**Mood:** Raw animal terror, the real and impossible

---

## S12 — Samuel Rises / The Apparition
```
The luminous apparition of an ancient white-bearded prophet emerging upward from the bare stone floor of a low room, wrapped in a rough dark prophet's mantle, his face ancient and grave and completely calm with eyes open and aware, cold silver-white ethereal light emanating from within and around him, partially transparent at the edges fading into shadow, the light is sacred not horror, in the foreground a tall broad-shouldered man in plain rough robes prostrating himself completely face-down on the flat undecorated stone floor, the gaunt silver-haired woman pressing her back flat against the far plain stone wall, plain flat-cut ancient Levant stone blocks with absolutely NO carvings NO reliefs NO decorations, biblical epic oil painting, Rembrandt chiaroscuro with cold supernatural glow, cinematic wide shot showing all three presences, ancient Levant plain stone interior, masterwork quality
```
**Shot:** Wide — all three presences in the room
**Mood:** Sacred dread, the impossible made real

---

## S13 — Samuel Delivers the Prophecy / The Sentence
```
Close-up on the face and upper body of an ancient white-bearded prophet apparition, his edges semi-transparent and dissolving into cold silver-white light, clearly not a living man but a presence from beyond death, his expression carrying absolute gravity and prophetic authority without anger, his eyes aware and certain and final, cold ethereal silver-white light emanating from within his face and robes making him the only light source in the darkness, one aged translucent hand slightly raised in the posture of final pronouncement, the darkness of the plain stone room absolute around him, the image communicates that what is spoken cannot be changed, biblical epic oil painting, Rembrandt chiaroscuro, tight cinematic close-up on the supernatural face, cold silver-white unearthly glow, ancient Levant stone interior, masterwork quality
```
**Shot:** Tight close-up — Samuel's face, supernatural glow
**Mood:** Final judgment, unchangeable, prophetic authority

---

## S13B — Saul's Hands on the Stone / The Weight of the Words
```
Extreme close-up on two large hands pressed flat against cold bare ancient stone floor, the knuckles white with the force of gripping the stone, the hands of a once-powerful king now pressing themselves into the ground in total prostration, the stone floor rough and old and indifferent, cold pale light falling across the hands from above, the image communicating the complete physical collapse of a man under the weight of what he has just heard, nothing else in frame except hands and stone, biblical epic oil painting, Rembrandt extreme close-up lighting, macro cinematic shot, ancient Levant stone floor, masterwork quality
```
**Shot:** Macro — hands gripping stone floor
**Mood:** Total collapse made physical

---

## S14 — Saul Prostrate / The Woman Beside Him
```
A tall man in rough plain robes collapsed completely face-down on bare stone floor in a low dark room, his full body prostrate and motionless, arms outstretched, the posture of total collapse not prayer, the cold pale light from the apparition fading at the edge of the frame, the gaunt silver-haired woman of En-dor crouching beside him with one hand on his shoulder, her expression changed from terror to something like grief and human compassion, a small oil lamp the only remaining warm light, the two figures small in the overwhelming dark room, biblical epic oil painting, Rembrandt chiaroscuro, cinematic wide shot from above, ancient Levant stone interior, masterwork quality
```
**Shot:** Wide from above — two small figures in darkness
**Mood:** Total collapse, unexpected human compassion

---

## S14B — The Woman's Face / Grief and Compassion
```
Close-up on the gaunt hollow-cheeked silver-haired woman of En-dor's face as she looks down at the prostrate man, her expression one of profound and complicated grief, the terror gone and replaced by something human and sorrowful, her deep-set eyes wet, her strong-nosed age-lined face communicating that she understands exactly who this man is and what is coming for him tomorrow, the warm lamplight soft on her face, the cold supernatural light entirely gone now, just an old woman in the dark with a broken king, biblical epic oil painting, Rembrandt intimate close-up lighting, cinematic portrait shot, ancient Levant, masterwork quality
```
**Shot:** Close portrait — her face, grief and compassion
**Mood:** The human moment at the center of the supernatural story

---

## S15 — The Woman Feeds the King / The Last Mercy
```
The gaunt hollow-cheeked silver-haired woman of En-dor kneeling beside a seated broken man in plain robes inside her low stone dwelling, offering him flat bread and a clay bowl with both hands, her expression quiet grave compassion, the man's head slightly bowed accepting the food, a simple meal on a low stone surface behind her, a single lamp burning warm between them, the profound irony of an outcast criminal by his own law feeding the broken king, the last human kindness before everything ends, no grandeur no drama just two people in lamplight, biblical epic oil painting, Rembrandt intimate lighting, cinematic tight two-shot, ancient Levant stone interior, masterwork quality
```
**Shot:** Intimate tight two-shot — bread, lamplight, the last mercy
**Mood:** Human compassion from the most unexpected source

---

## S15B — Saul at Dawn / Walking Toward the Valley
```
A lone figure in plain rough robes walking away from a small stone dwelling at the cold blue hour just before dawn, the path leading down toward a vast dark valley below, the figure's posture heavy and slow and deliberate, the walk of a man going to meet what he cannot escape, the sky the cold grey-blue of earliest morning, the valley below still dark, distant campfires still burning on the far hillside, no hope in the image only the inevitability of the next few hours, biblical epic oil painting, Rembrandt cold pre-dawn lighting, cinematic medium shot from behind and above, ancient Levant hillside, masterwork quality
```
**Shot:** Medium from behind — walking toward his death
**Mood:** Inevitable, the prophecy already in motion

---

## S16 — The Battle of Gilboa / Every Word Came True
```
The aftermath of a catastrophic ancient battle on an open hillside at harsh midday, Iron Age weapons and broken shields scattered across rocky ground, distant figures of a victorious army moving across the hillside in the background, the hill strewn with the evidence of total defeat, the light harsh and unforgiving without warmth, dust settling in the still air, a broken piece of deep crimson cloth caught on a rock in the foreground the only indication of who fell here, the emptiness communicating that it is over and was always going to be over, biblical epic oil painting, harsh Rembrandt midday light, cinematic wide desolate shot, ancient Levant battlefield, masterwork quality
```
**Shot:** Wide desolate — aftermath, consequence, silence
**Mood:** Somber, inevitable, the prophecy fulfilled exactly

---

## S16B — The Empty Hillside / The End
```
A single broken iron spear lying on bare rocky hillside ground, its shaft snapped, the iron point half-buried in dust, no figures anywhere in the frame, the hillside empty and silent, harsh midday light casting short hard shadows, in the far distance the shapes of a victorious army departing, the foreground completely still and empty, the image communicating the absolute finality of what has happened here, biblical epic oil painting, harsh midday Rembrandt lighting, cinematic extreme close-up on the broken spear with wide landscape beyond, ancient Levant battlefield hillside, masterwork quality
```
**Shot:** Close on broken spear, empty landscape beyond
**Mood:** The final image, silence after everything

---

## THUMBNAIL A — The Seance Confrontation
```
Split composition: left half shows the luminous cold silver-white apparition of an ancient robed prophet, right half shows the gaunt silver-haired woman screaming in genuine terror, center of frame dark and empty between them, extreme contrast between cold supernatural light and warm firelight, TEXT SAFE ZONE at top and bottom thirds, maximum visual drama, biblical epic oil painting, Rembrandt chiaroscuro, masterwork quality
```

## THUMBNAIL B — The Disguised King
```
Extreme close-up portrait of a haggard bearded man pulling a rough hood over his face in darkness, only his desperate exhausted eyes visible between hood and beard, the face of a once-great king in hiding, dramatic underlighting, deep blacks, TEXT SAFE ZONE at bottom third, biblical epic oil painting, Rembrandt chiaroscuro, masterwork quality
```
"""

with open("stories/001_witch_of_endor/image_prompts.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Done. stories/001_witch_of_endor/image_prompts.md replaced with 30-scene v3.")