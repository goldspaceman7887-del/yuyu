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

## Optional: higher-fidelity version with an image/video model
This version is a procedural illustration. For a richer, hand-painted look, generate the plates
below with a model, keep **all text as overlays** (from `subtitles_ja.srt` and the positions
above), and reuse `soundtrack.wav` and the timeline.

*Style line for every prompt:* original nostalgic Japanese summer illustration, hand-inked
environmental background art, softly painted cel-animation colour, fine imperfect charcoal-brown
linework, subtle paper texture, muted summer blue, cream clouds with pale blue-grey shadows,
faded vermilion, weathered tan wood, moss green, small touches of muted teal, no text, no
people, no faces, no signage lettering, not photoreal, not 3D.

1. **Plate A (wide, extra tall, about 1240×3000):** a monumental cumulus cloud rising from a very
   low horizon over a flat summer field. A small weathered wooden coffee cart sits in the lower
   third: pale thatched roof, dark posts, faded red front panel with a lighter repaired plank,
   glass jars, a kettle, cups, potted plants at its feet, a teal Japanese step-through bicycle
   with a front basket leaning at the left, and a blank cream vertical banner on a bamboo pole
   at the right.
2. **Plate B (close-up):** the same cart's worn wooden counter seen from the front, with a
   butterfly-key repair. A pale ceramic mug with a teal drip glaze sits on a wooden saucer, and
   a small closed navy cloth-bound book lies beside it. A kettle and glass jars stand at the back,
   with the same cloud and field visible through the open back of the stand.
3. **Animation:** subtle motion only (grass, banner sway, steam, slow cloud drift), with
   multiplane parallax. Add the hand opening the book as a short 1.6 s insert. Add the 聖書
   cover title and all captions in compositing, never in generation.
