# Yutoriba — 15s vertical teaser

1080×1920, 30 fps, 15 s. Every frame is painted in code: the scenes are drawn on an HTML canvas, captured in headless Chromium, and encoded with ffmpeg. The soundtrack is synthesized in Python with numpy (soft piano, a few koto plucks, a distant train, café murmur, a spoon against a cup, city hush).

Output: `yutoriba-teaser.mp4`

| Time | Shot | Text |
|---|---|---|
| 0–3s | Empty station platform at golden hour, slow push-in, lens flare | "Is this everything?" |
| 3–6s | Café interior, cup steam, reader silhouette by window, parallax drift left | none |
| 6–9s | Bookstore under sakura, petals, tilt up to sky | "There may be more." |
| 9–12s | Two friends seen through café glass, amber, shallow focus | "Let's find out together." |
| 12–15s | Dusk street pull-back, windows light one by one, then the "Yutoriba" wordmark on cream | Yutoriba |

## Rebuild

```bash
cd video/yutoriba-teaser
node render.js /tmp/silent.mp4            # ~7 min, needs playwright + chromium
python3 audio.py /tmp/audio.wav           # needs numpy
ffmpeg -i /tmp/silent.mp4 -i /tmp/audio.wav -c:v copy -c:a aac -b:a 192k -shortest yutoriba-teaser.mp4
```

Preview a few frames: `node render.js --stills 1.5,4.5,7.8 ./stills`

- `scenes.js`: all the scenes, the timeline, and the captions (edit `caption(...)` calls in `renderFrame` to change the wording or timing)
- `audio.py`: chord progression, melody and ambience
- `fonts/`: Cormorant Garamond (SIL Open Font License)
