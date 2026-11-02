# ゆとりば — 15-second Reel ("Room to Breathe")

**Final file:** `yutoriba_reel_15s.mp4`, 1080×1920 (9:16), 30 fps, H.264 + AAC 48 kHz stereo,
exactly **15.000 s / 450 frames**, about -16 LUFS. `cover.jpg` is the last frame, for use as the Reel cover.

Everything here is original. The illustration is drawn by code (ink lines, painted cumulus,
paper grain), the music and sound effects are synthesized, and the typeface is Zen Old Mincho
(SIL Open Font License, `fonts/`). Nothing from the reference image is traced or reused.

## Timeline (as rendered)

| Time | Picture | On-screen Japanese | Sound |
|---|---|---|---|
| 0.0–6.25 | Giant cumulus against blue sky, grass at the bottom edge. Slow downward drift and push-in until the coffee stand appears (bicycle, pots, menu cards, jars, ひとやすみ banner). Two distant birds. | 0.5 s 毎日、急いでばかりいない？ / 3.3 s 少し立ち止まると、/ 3.95 s 見えてくるものがある。 | Wind, distant cicadas, felt piano starts; bird 2.15 s; distant bicycle bell 4.25 s (once); wood creak 5.15 s |
| 5.75–6.8 | **Transition:** the banner cloth blows across the lens | — | Cloth flutter |
| 6.25–9.5 | Close-up of the counter: coffee with rising steam, a small Bible marked 聖書. A hand comes in and opens it (6.3–7.95); a ribbon bookmark and a page lifting in the breeze. Sunlight slides across the wood. | 6.7 s 「わたしは道であり、/ 真理であり、/ いのちなのです。」 7.75 s ヨハネの福音書 14:6 | Ceramic touch 6.32 s, page turn 6.95 s |
| 9.5–12.55 | Steam grows and rises into the cloud while the camera tilts up and pulls back, bringing the hanging cards and the sky back into frame | 9.85 s 人生について、/ 10.3 s 聖書と一緒に考えてみませんか。 | A breath of air; leaves |
| 12.1–13.0 | **Transition:** foreground grass passes the lens, with a short dissolve | — | Leaves |
| 12.55–15.0 | Calm wide shot, almost still (grass, banner and steam keep moving). Held to the last frame, no fade. | 12.85 s ゆっくり考える場所。 / 13.3 s **ゆとりば** / 13.85 s まずは、ヨハネの福音書から。 | Music resolves on Fadd9 at 13.3 s (vibraphone note) |

Text sits in the upper-middle, centred slightly left (x≈520), between about 430 and 960 px down
the frame. That keeps it clear of the top bar, the right-hand buttons and the bottom 20%.
It is warm ivory Mincho with a soft charcoal shadow and a feathered translucent backing so it
stays readable over the bright cloud. Each line appears with a soft left-to-right ink reveal.

The signs in the scene use only real, correct words: 珈琲, 麦茶, 氷 and ひとやすみ.

## Music
The music is original, at 72 BPM in F major: Fmaj9 → Am7 → B♭maj7 → Gm7 / C7sus4 → Fadd9.
It uses felt piano, light guitar harmonics, a warm pad and one vibraphone note. There are no
vocals, no percussion and no crescendo. The environmental sounds are mixed about 4 dB above the music.

## Rebuild
```
pip install numpy scipy pillow fonttools
cd reel/src
python3 scene.py      # static illustration layers -> reel/build/
python3 audio.py      # soundtrack -> reel/build/audio.wav
python3 render.py     # video -> reel/build/video.mp4
cd .. && ffmpeg -y -i build/video.mp4 -i build/audio.wav -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 256k -t 15.0 -movflags +faststart yutoriba_reel_15s.mp4
```
`python3 render.py stills 7.2 14.9` renders single frames, useful for checking changes.

## Painted version (AI repaint of this reel)
The procedural render acts as the **layout and timing master**. Each shot is exported without
text and sent to a video model as a video-to-video "repaint". Composition, camera move, timing
and object placement stay locked, and only the rendering style changes. The Japanese text and
`soundtrack.wav` are then composited back on top, so the wording stays exact.

1. Export a clean shot: `NOTEXT=1 python3 render.py stills <t>` for single frames. For a clip,
   see the snippet used for `gen/src_A_notext.mp4` (frames 0–171 = 0–5.73 s, opening shot).
2. Make it reachable at a public MP4 URL (this repo is public, so the raw GitHub URL works).
3. Repaint it. Used here: vidIQ `generate_video`, model `minimax-h3`, 768p, 9:16, with the
   source clip passed as `videoUrls`. **Cost: 80 credits for 6 s.** Prompt:

> Repaint this exact video as a lovingly hand-painted nostalgic Japanese summer background
> illustration that has quietly begun to move. Keep the same composition, the same slow
> downward camera drift and gentle push-in, the same timing, and the same objects in the same
> places (cumulus cloud, low horizon, coffee cart with thatched roof and faded vermilion panel,
> jars, kettle, cups, potted plants, teal step-through bicycle, cream banner on a bamboo pole).
> Fine imperfect charcoal-brown linework, softly painted cel colour, ivory clouds with pale
> blue-grey shadows, wood grain, individual grass blades, paper texture, amber light from the
> upper left. Subtle motion only. No people, faces, text, letters, writing, watermarks or new
> objects. Not photoreal, not 3D, no neon, no lens flares.

4. Upscale the result to 1080×1920, cut it into the timeline in place of the procedural shot,
   then re-apply the text layers and soundtrack (`render.py` text code, or `subtitles_ja.srt`
   in any editor).

**Test result (opening shot, minimax-h3, 80 credits): not used.** The clip did not follow the
source. It started on the stand instead of the sky, then pushed in. From about 2.5 s the banner
filled with invented pseudo-Chinese characters ("龙大文茶茶"), and the menu card 珈琲 became
nonsense. After about 3.5 s the grass turned yellow, the light went golden and the bicycle
changed shape. Only the first ~2 s were clean. If you retry, check every frame for invented
writing, and expect to use only short clean stretches. `composite_ai.py` + `render.py` will
take any clip that passes.

Shots and source ranges: **A** 0.0–6.25 s (opening wide), **B** 6.25–12.55 s (counter close-up
and Bible), **C** 12.55–15.0 s (closing wide; the model needs at least 4 s, so repaint 11.0–15.0
or reuse the last seconds of A). If the model redraws the hand or the 聖書 cover badly, keep
the procedural version of that part of shot B.
