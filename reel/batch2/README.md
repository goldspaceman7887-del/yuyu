# ゆとり場 — Reel batch 2 (five 15-second reels)

| # | File | Look | Message | Verse |
|---|---|---|---|---|
| 1 | `01_hajimemashite.mp4` | Afternoon; a bicycle arrives, coffee is poured | Introduces ゆとり場 | — |
| 2 | `02_yasundeii.mp4` | Sunset into dusk; a Bible is opened, a lantern switches on | 休んでいい | マタイ 11:28 |
| 3 | `03_hanabi.mp4` | Summer night, fireworks, wind chime, stars | もののあわれ → eternity | 伝道者の書 3:11 |
| 4 | `04_amayadori.mp4` | Summer shower, two bicycles take shelter, rainbow | Connection, 縁 | 創世記 2:18 |
| 5 | `05_sakuhin.mp4` | Misty dawn; handmade cups, a potter's seal | Made with purpose | エペソ 2:10 |

All five use the same specs as reel 1:
- 1080×1920, 30 fps, H.264 + AAC 48 kHz, exactly 15.000 s, loudness about -16 LUFS
- the same painted world, Zen Old Mincho text, and felt-piano music
- `*_cover.jpg` is the last frame, for the Reel cover

Every reel ends on the brand card. It shows the ゆとり場 logo (ensō, indigo ゆ, rising steam), drawn from the profile logo, with **ゆとり場 / Yutoriba** and one or two closing lines underneath.

Captions and hashtags are in `captions.md`. The scripts are in `../../reel-scripts-batch-2.md`.

## Changes from the written scripts
- No people are drawn (same as reel 1). In reel 4 the "two strangers" are shown as two bicycles arriving and two cups side by side.
- Reel 5 has no shutter opening. The dawn is shown with mist lifting off the field instead.
- In reels 3–5 the closing line sits on the brand card, so it stays on screen and on the cover.

## Rebuild
```
pip install numpy scipy pillow fonttools
cd reel/src
python3 scene.py && python3 scene.py split bikes   # static layers
python3 batch2.py <n>        # video -> reel/build/b2_<n>/video.mp4
python3 audio2.py <n>        # sound -> reel/build/b2_<n>/audio.wav
./make_batch2.sh             # mux, loudness, cover -> reel/batch2/
```
`python3 batch2.py <n> stills 3.0 9.5` renders single frames.
