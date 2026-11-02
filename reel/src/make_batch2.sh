#!/bin/bash
# Mux each batch-2 reel (video + soundtrack), normalise to about -16 LUFS, export the cover frame.
set -e
cd "$(dirname "$0")"
OUT=../batch2
mkdir -p "$OUT"
names=(x hajimemashite yasundeii hanabi amayadori sakuhin)
for n in "${@:-1 2 3 4 5}"; do
  for k in $n; do
    b=../build/b2_$k
    f="$OUT/0${k}_${names[$k]}.mp4"
    ffmpeg -y -loglevel error -i $b/video.mp4 -i $b/audio.wav -map 0:v -map 1:a -c:v copy \
      -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k -ar 48000 \
      -t 15.0 -movflags +faststart "$f"
    ffmpeg -y -loglevel error -sseof -0.04 -i $b/video.mp4 -frames:v 1 -q:v 2 "${f%.mp4}_cover.jpg"
    echo "wrote $f"
  done
done
