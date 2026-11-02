# Yutoriba (ゆとりば) content workspace

Future sessions should read this first. It records the brand, the reel style, how the first
reel was built, and what was learned.

## Brand
- **ゆとりば / Yutoriba**: "a place to slow down", "a place with room to breathe".
- Purpose: gentle moments that invite people to pause, connect, think about life, and become
  curious about reading the Bible.
- Audience: 18–30, primarily a contemporary **Japanese** audience. Themes: coffee, community,
  purpose, faith, Japan (see `master-prompt.md`).
- Tone: quiet, hospitable, thoughtful, sincere, curious rather than forceful. It should never
  feel like a church ad, a foreign missionary campaign or a debate.
- Never attack Buddhism, Shinto, atheism, secular life or Japanese culture. No fear, guilt,
  pressure, glowing Bibles, light beams, or crosses in clouds.
- Video text is in Japanese only, with no English. Never invent or paraphrase Scripture; use the
  approved wording exactly.

## Visual style (established by the first reel)
- An original nostalgic Japanese summer illustration that "has quietly begun to move":
  hand-inked charcoal-brown lines, softly painted cel colour, paper grain.
- An enormous cumulus cloud, a very low horizon (sky about 2/3 of the frame), and a small
  weathered coffee stand in a summer field: thatched roof, faded vermilion panel, glass jars,
  kettle, a teal mamachari bicycle, potted plants, and a ひとやすみ banner.
- Palette: muted summer blue, ivory clouds with blue-grey shadows, faded vermilion, tan wood,
  moss green, small touches of teal.
- Signs may carry only real, correct words (珈琲, 麦茶, 氷, ひとやすみ). Never random characters.
- Text: Zen Old Mincho (OFL, in `reel/fonts/`), warm ivory, soft shadow plus a feathered
  translucent backing, upper-middle and slightly left (x≈520). Keep it clear of the top bar, the
  right-hand buttons and the bottom 20%. Gentle left-to-right ink reveal; no bouncing or zooming.
- Do not copy or name any specific artist, studio, anime or film. The Pinterest reference
  (`inspiration/`) is a mood reference only; never trace it or repost it.

## Reel #1: "Room to Breathe" (finished, ready to post)
- Files: `reel/yutoriba_reel_15s.mp4` (1080×1920, 30 fps, exactly 15.000 s / 450 frames,
  AAC 48 kHz, about -16 LUFS), `reel/cover.jpg`, `reel/caption_ja.txt`,
  `reel/subtitles_ja.srt`, `reel/soundtrack.wav`. Full timeline in `reel/README.md`.
- Story beats and approved text:
  1. 0.5 s 毎日、急いでばかりいない？ (cloud, drift down to the stand)
  2. 3.3 s 少し立ち止まると、/ 見えてくるものがある。
  3. 6.7 s 「わたしは道であり、真理であり、いのちなのです。」 ヨハネの福音書 14:6
     (close-up: coffee and steam, a hand opens a small Bible marked 聖書)
  4. 9.85 s 人生について、/ 聖書と一緒に考えてみませんか。 (steam rises into the cloud)
  5. 12.85 s ゆっくり考える場所。/ **ゆとりば** / まずは、ヨハネの福音書から。
     (wide shot, held to the last frame)
- Transitions come from objects in the scene: banner cloth crossing the lens, grass passing the lens.
- Sound: wind, distant cicadas, one bird, one distant bicycle bell, wood creak, cup, page turn.
  Original felt-piano score at 72 BPM in F major (Fmaj9 → Am7 → B♭maj7 → Gm7/C7sus4 → Fadd9),
  resolving as ゆとりば appears. Ambience is mixed about 4 dB above the music.
- Still to do: the owner should listen once with sound before posting (the mix was balanced by
  measurement only). Track its status in `reel-ideas.md`.

## How reels are made here (no image-gen model in this environment)
- The illustration is procedural Python: `reel/src/scene.py` builds the static layers,
  `render.py` animates them (multiplane camera, swaying grass and banner, steam, book and hand,
  text), and `audio.py` synthesizes the soundtrack. Rebuild steps are in `reel/README.md`.
- Deps: `pip install numpy scipy pillow fonttools`; ffmpeg; about 2.5 min to render on 4 cores.
- `NOTEXT=1 python3 render.py stills <t>` gives text-free frames;
  `python3 render.py stills 7.2 14.9` gives single frames for checking.
- New reels in this style can reuse the code: change the camera, the text spec (`TEXT` in
  `render.py`) and the score.

## Lessons learned
- **vidIQ AI video** (`generate_video`, minimax-h3) cost **80 credits for 6 s**. The account has
  150 renewable credits per month (70 left after the test; renews around the 29th).
  Always confirm cost with the owner before generating.
- Its video-to-video repaint did **not** follow the source shot. It invented pseudo-Chinese
  writing on the banner ("龙大文茶茶"), garbled 珈琲, turned the grass yellow mid-shot and
  reshaped the bicycle. Rejected. If retrying, check every frame for invented writing and use
  only short clean stretches; `reel/src/composite_ai.py` can swap a clean clip into the opening.
- vidIQ start/end frames must be inline base64 (too large to send). Instead, pass a public MP4
  URL; this repo is **public**, so a raw.githubusercontent.com link works. Anything pushed is
  publicly visible.
- The cloud environment blocks `videogen.vidiq.com` downloads. Either the owner attaches the file
  in chat (save from the link → Share → Save Video → attach), or the domain is added under
  Allowed domains in the environment settings (applies to new sessions).
- The owner works from an iPhone. Give step-by-step phone instructions and send files with the
  file-sharing tool.

## Repo map
- `master-prompt.md`: content-strategist prompt (hook, script, shots, B-roll, caption, CTA, hashtags).
- `content-ideas.md`, `reel-ideas.md` (tracker: To Make / Filmed / Edited / Posted),
  `b-roll-needed.md`.
- `inspiration/moodboard.md`: reference notes and palette.
- `reel/`: finished reel #1, its source code and production notes.
- Work branch: `claude/new-session-x6pp8j` (not yet merged to `main`).

## Next reel candidates (same style, no credits needed)
"Why slowing down matters", "What loneliness teaches us", "The purpose of life in 20 seconds".
