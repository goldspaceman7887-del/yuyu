# ゆとりば — Three Bible Reels

Three Japanese Instagram Reels, each about 17 seconds long, made from the same four source pieces
(`sources/`). Each reel uses the sources in a different order and with different crops, and each
ends by gently asking whether the viewer would like to read more of the Bible.

| Reel | Theme | Shot order | Verse | Closing question |
|---|---|---|---|---|
| `01_kotoba/` ことばを、ひらく | Reading and discovering the Bible | Commuters → hand straps → café window → young man, pan to coffee + book | 詩篇 119:105 | 聖書を、もう少し読んでみませんか？ |
| `02_sonosaki/` いまの、その先 | Thinking beyond life right now | Café window → young man gazing → commuter → straps, pan to sunset window | 伝道者の書 3:11 | その答えを、聖書の中に探してみませんか？ |
| `03_konomachi/` この街で | Finding purpose in a big city | Sunset train window → commuters → young man → city from café window | イザヤ書 43:4 | あなたへのことばを、聖書で読んでみませんか？ |

Each folder contains `yutoriba_<name>.mp4` (1080×1920, 30 fps, H.264 + AAC, -16 LUFS),
`cover.jpg` (the last frame, with the closing question and the ゆとりば logo) and `caption_ja.txt`
(the post caption with hashtags). Verses are quoted from 新改訳2017.

## Look
- The 16:9 sources are cropped to 9:16, with slow push-ins and pans (no fast moves) and 0.7 s crossfades.
- Warm amber grade with slightly reduced saturation, coffee-brown lifted blacks, a soft vignette,
  a faint paper texture and film grain.
- Type: Zen Old Mincho in warm ivory, revealed with a soft left-to-right ink wipe over a feathered
  dark backing. Text stays out of the Reels UI areas.
- Sound: an original felt-piano score per reel (D major / A minor → F / E minor → G) that resolves
  as ゆとりば appears. Train rumble and rail joints play under the train shots; café room tone and a
  cup clink (and a page turn in reel 1) play under the café shots.

## Rebuild
```
pip install numpy scipy pillow fonttools
cd reels/src
python3 make_audio.py            # build/<name>_audio.wav
python3 make_video.py            # build/<name>_video.mp4  (about 3 min per reel on 4 cores)
python3 make_video.py 02_sonosaki stills 5.0 16.9   # check single frames
```
Then mux each reel (see the ffmpeg command in this commit's history, or):
```
ffmpeg -i build/N_video.mp4 -i build/N_audio.wav -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 \
  -maxrate 12M -bufsize 24M -tune grain -pix_fmt yuv420p -af loudnorm=I=-16:TP=-1.5:LRA=11 \
  -c:a aac -b:a 256k -shortest -movflags +faststart N/yutoriba_N.mp4
```
All timing, crops and text live in `src/reels.py`.
