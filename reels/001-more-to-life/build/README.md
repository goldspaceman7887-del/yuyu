# Reel 001 build

The reel is drawn entirely in code (canvas in headless Chromium) and its audio is synthesized with numpy.

| File | Purpose |
|---|---|
| `engine.js` | Ink brush, screentones, paper/grain, typography helpers |
| `characters.js` | Sora / Aoi faces, Ren, back views, hands |
| `scenes.js` | Scenes 1–5, transitions, text track (timings = production-package.md §2/§4) |
| `audio.py` | Soundtrack per §12 |
| `render.js` | Frames → ffmpeg |

## Rebuild
```bash
# font (Shippori Mincho B1, SIL OFL) — fetched from npm, ignored by git
npm pack @fontsource/shippori-mincho-b1 && tar xzf fontsource-shippori-mincho-b1-*.tgz
mkdir -p fonts && cp package/500.css package/600.css fonts/ && cp -r package/files fonts/

python3 audio.py soundtrack_raw.wav
ffmpeg -i soundtrack_raw.wav -af loudnorm=I=-14:TP=-1:LRA=11 -ar 48000 soundtrack.wav   # two-pass recommended
node render.js stills 0,100,230,350          # preview frames into stills/
node render.js video master.mp4 soundtrack.wav
```
