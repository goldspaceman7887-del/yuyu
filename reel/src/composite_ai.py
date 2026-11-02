"""Prepares an AI-repainted opening clip for the reel.

Usage: python3 composite_ai.py ../gen/ai_A_raw.mp4
The clip is cropped/scaled to fill 1080x1920 and retimed so it lines up with the
procedural source (src_A_notext.mp4 = 0-5.733 s), then written as frames to
build/ai_A/. render.py uses those frames for 0-5.75 s and draws everything else
(the cloth transition, shots B and C, all Japanese text, paper grain) as before.
"""
import os
import shutil
import subprocess
import sys

from common import BUILD, FPS

SRC_DUR = 172 / 30  # length of src_A_notext.mp4
src = sys.argv[1]
out = os.path.join(BUILD, "ai_A")
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                     "-of", "csv=p=0", src]).decode())
speed = SRC_DUR / dur
vf = (f"setpts={speed:.6f}*PTS,fps={FPS},"
      "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920")
subprocess.check_call(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-vf", vf,
                       "-frames:v", str(int(5.75 * FPS) + 1), os.path.join(out, "%04d.png")])
print(len(os.listdir(out)), "frames ->", out, f"(retimed x{speed:.3f})")
