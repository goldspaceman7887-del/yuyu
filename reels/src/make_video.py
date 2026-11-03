"""Renders the three Yutoriba Bible reels (video only) -> reels/build/<name>_video.mp4

Usage:
  python3 make_video.py                 # all reels
  python3 make_video.py 01_kotoba       # one reel
  python3 make_video.py 01_kotoba stills 2.0 15.5   # single frames -> build/still_*.jpg
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "reel", "src"))
from common import fnoise, smooth  # noqa: E402  (shared helpers from the first reel)
from render import make_line_img  # noqa: E402  (same ivory Mincho ink style as the first reel)

from reels import REELS, XF  # noqa: E402

W, H, FPS = 1080, 1920, 30
SRC_DIR = os.path.join(ROOT, "sources")
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)
TEXT_CX = 520  # slightly left of centre, clear of the Reels buttons on the right
SRC_FILES = {
    "T": "train_straps_sunset.jpg",
    "C": "cafe_dusk_window.mp4",
    "M": "cafe_man_book.mp4",
    "P": "train_commuters.mp4",
}

SRC = {}


def load_sources():
    for k, f in SRC_FILES.items():
        p = os.path.join(SRC_DIR, f)
        if f.endswith(".jpg"):
            SRC[k] = dict(still=True, frames=np.asarray(Image.open(p).convert("RGB"))[None], fps=24)
            continue
        info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                               "stream=width,height", "-of", "csv=p=0", p],
                              capture_output=True, text=True).stdout.strip().split(",")
        w, h = int(info[0]), int(info[1])
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
        SRC[k] = dict(still=False, frames=fr, fps=24)


def src_frame(k, ts):
    s = SRC[k]
    fr = s["frames"]
    if s["still"]:
        return fr[0]
    x = min(max(ts * s["fps"], 0), len(fr) - 1.001)
    i = int(x)
    a = x - i
    if a < 0.02:
        return fr[i]
    if a > 0.98:
        return fr[i + 1]
    return (fr[i].astype(np.float32) * (1 - a) + fr[i + 1].astype(np.float32) * a).astype(np.uint8)


def ease(p):
    p = min(max(p, 0.0), 1.0)
    return 0.45 * p + 0.55 * smooth(p)


def shot_image(sh, u):
    img = src_frame(sh["src"], sh.get("t0", 0.0) + u * sh.get("speed", 1.0))
    sh_h, sh_w = img.shape[:2]
    p = ease(u / sh["dur"])
    z = sh["z0"] + (sh["z1"] - sh["z0"]) * p
    ch = sh_h / z
    cw = ch * W / H
    cx = sh["cx0"] + (sh["cx1"] - sh["cx0"]) * p
    cx = min(max(cx, cw / 2), sh_w - cw / 2)
    cy = sh.get("cy", sh_h / 2)
    cy = min(max(cy, ch / 2), sh_h - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    out = Image.fromarray(img).transform((W, H), Image.EXTENT, box, Image.BICUBIC)
    return np.asarray(out).astype(np.float32)


# ------------------------------------------------------------------ look
LOOK = {}


def init_look():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.6)) ** 2)
    LOOK["vig"] = (1 - 0.22 * np.clip(d - 0.35, 0, 1) ** 1.6)[..., None]
    paper = fnoise(W // 2, H // 2, 3, 4, seed=77)
    paper = np.asarray(Image.fromarray((paper * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)) / 255.0
    LOOK["paper"] = (1 + 0.035 * (paper - 0.5))[..., None].astype(np.float32)


def grade(a):
    a = a / 255.0
    lum = (a @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    a = lum + (a - lum) * 0.9                                   # a touch less saturated
    a = a * np.array([1.025, 1.0, 0.965], np.float32)          # warm amber
    a = a + (1 - a) * 0.0 + np.array([0.035, 0.026, 0.018], np.float32) * (1 - a) ** 3  # coffee-brown lifted blacks
    a = 0.06 + a * 0.94 - 0.06 * a                              # soft film shoulder / toe
    a = a * LOOK["vig"] * LOOK["paper"]
    return np.clip(a * 255, 0, 255)


def grain(a, seed):
    r = np.random.default_rng(seed)
    g = r.standard_normal((H // 2, W // 2)).astype(np.float32)
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    lum = a.mean(axis=2, keepdims=True) / 255
    amp = 5.0 * (0.55 + 0.9 * lum * (1 - lum))
    return np.clip(a + g[..., None] * amp, 0, 255)


# ------------------------------------------------------------------ text
def build_text(spec):
    blocks = []
    for b in spec:
        imgs = [make_line_img(t, s, True) for (t, s) in b["lines"]]
        sizes = [s for (_, s) in b["lines"]]
        widths = [w for (_, _, w) in imgs]
        lines = []
        y = b["top"]
        kind = b["kind"]
        stagger = {"line": 0.5, "close": 0.55, "quote": 0.3, "brand": 0.5}[kind]
        if kind == "quote":
            body = widths[:-1]
            x_left = TEXT_CX - max(body) / 2
        for i, ((img, pad, w), s) in enumerate(zip(imgs, sizes)):
            if kind == "quote" and i < len(imgs) - 1:
                x = x_left + (0 if i == 0 else s * 0.5)
            elif kind == "quote":
                y += s * 0.55
                x = x_left + max(body) - w
            else:
                x = TEXT_CX - w / 2
            t0 = b["t"] + i * stagger
            if kind == "quote" and i == len(imgs) - 1:
                t0 += 0.3
            lines.append(dict(img=img, x=int(x - pad), y=int(y - pad), w=w, pad=pad, t0=t0))
            gap = 1.72
            if kind == "brand":
                gap = 1.5
            y += s * gap
        x0 = min(l["x"] + l["pad"] for l in lines) - 70
        x1 = max(l["x"] + l["pad"] + l["w"] for l in lines) + 70
        y0 = min(l["y"] + l["pad"] for l in lines) - 45
        y1 = max(l["y"] + l["img"].height - l["pad"] for l in lines) + 25
        bw, bh = x1 - x0 + 240, y1 - y0 + 240
        m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle([120, 120, bw - 120, bh - 120], radius=80, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(55))
        back = Image.new("RGBA", (bw, bh), (34, 30, 30, 0))
        back.putalpha(m.point(lambda v: int(v * 0.34)))
        blocks.append(dict(lines=lines, out=b["out"], back=back, bx=x0 - 120, by=y0 - 120))
    return blocks


def text_layer(frame, t, blocks):
    for b in blocks:
        fo = 1.0
        if b["out"] is not None:
            if t >= b["out"] + 0.4:
                continue
            fo = 1 - smooth((t - b["out"]) / 0.4)
        t_first = b["lines"][0]["t0"]
        if t <= t_first - 0.3:
            continue
        ob = smooth((t - t_first + 0.3) / 0.9) * fo
        if ob > 0.01:
            ba = np.asarray(b["back"]).astype(np.float32)
            ba[..., 3] *= ob
            frame.alpha_composite(Image.fromarray(ba.astype(np.uint8), "RGBA"), (b["bx"], b["by"]))
        for ln in b["lines"]:
            dt = t - ln["t0"]
            if dt <= 0:
                continue
            p = min(dt / 0.95, 1.0)
            img = ln["img"]
            a = np.asarray(img).astype(np.float32)
            xs = np.arange(img.width, dtype=np.float32) - ln["pad"]
            feather = 150.0
            front = p * (ln["w"] + feather + 40) - 20
            ramp = np.clip((front - xs) / feather, 0, 1)
            op = smooth(dt / 1.1) * fo
            a[..., 3] *= ramp[None, :] * op
            # rise 6 px while appearing
            frame.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"),
                                  (ln["x"], ln["y"] + int(round(6 * (1 - smooth(dt / 1.1))))))


# ------------------------------------------------------------------ timeline
CUR = {}


def setup(name):
    r = REELS[name]
    starts, s = [], 0.0
    for sh in r["shots"]:
        starts.append(s)
        s += sh["dur"] - XF
    total = s + XF
    CUR.update(name=name, shots=r["shots"], starts=starts, total=total, blocks=build_text(r["text"]))
    return total


def render_frame(i):
    t = i / FPS
    shots, starts = CUR["shots"], CUR["starts"]
    acc, wsum = None, 0.0
    for k, (sh, s0) in enumerate(zip(shots, starts)):
        u = t - s0
        if u < 0 or u >= sh["dur"] + 1e-6 and k < len(shots) - 1:
            continue
        w_in = 1.0 if k == 0 else smooth(u / XF)
        if acc is None:
            acc = shot_image(sh, u)
        else:
            acc = acc * (1 - w_in) + shot_image(sh, u) * w_in
    a = grade(acc)
    frame = Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.UnsharpMask(2, 45, 2)).convert("RGBA")
    text_layer(frame, t, CUR["blocks"])
    out = grain(np.asarray(frame.convert("RGB")).astype(np.float32), i * 7919 + len(CUR["name"]))
    return out.astype(np.uint8).tobytes()


def render(name):
    total = setup(name)
    n = int(round(total * FPS))
    out = os.path.join(BUILD, f"{name}_video.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                            "-crf", "16", "-pix_fmt", "yuv420p", "-tune", "film", out], stdin=subprocess.PIPE)
    with Pool(4) as pool:
        for j, buf in enumerate(pool.imap(render_frame, range(n), chunksize=4)):
            enc.stdin.write(buf)
            if j % 60 == 0:
                print(f"  {name} {j}/{n}", flush=True)
    enc.stdin.close()
    enc.wait()
    print("wrote", out, f"{n} frames, {n / FPS:.2f} s")
    return n / FPS


def stills(name, times):
    setup(name)
    for t in times:
        buf = render_frame(int(round(t * FPS)))
        img = Image.frombytes("RGB", (W, H), buf)
        p = os.path.join(BUILD, f"still_{name}_{t:05.2f}.jpg")
        img.save(p, quality=90)
        print(p)


if __name__ == "__main__":
    load_sources()
    init_look()
    args = sys.argv[1:]
    if len(args) >= 2 and args[1] == "stills":
        stills(args[0], [float(x) for x in args[2:]])
    else:
        for nm in (args or list(REELS)):
            render(nm)
