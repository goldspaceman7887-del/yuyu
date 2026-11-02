"""Batch 2: five more 15 s ゆとり場 reels in the same painted world as reel 1.

    python3 batch2.py <reel 1-5>                 -> build/b2_<n>/video.mp4
    python3 batch2.py <reel 1-5> stills 3.0 9.5  -> build/b2_<n>/still_*.png

Each reel reuses the layers from scene.py (wide field + close-up of the counter) and changes
the light and weather (afternoon, sunset, night with fireworks, summer shower, dawn), adds a few
props, and ends on a brand card with the ゆとり場 logo (ensō, indigo ゆ, rising steam).
Run `python3 scene.py` and `python3 scene.py split bikes` first.
"""
import math
import os
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import *  # noqa
import render as R0
from render import Cam, place, overlay_wide, make_line_img
from scene import draw_pot, draw_plant, BIKE_ORIGIN, A_HOR, B_HOR, AW, AH, BW, BH, G_OY

TEXT_CX = 520
INDIGO = (58, 66, 150)

# ================================================================== grading
DAY = dict(top=(1, 1, 1), bot=(1, 1, 1), add=(0, 0, 0), sat=1.0)
G = dict(
    day=(DAY, DAY),
    sunset=(dict(top=(0.92, 0.78, 0.80), bot=(1.22, 0.88, 0.62), add=(14, 0, -6), sat=0.95),
            dict(top=(1.08, 0.88, 0.68), bot=(1.0, 0.82, 0.64), add=(6, 0, 0), sat=0.92)),
    dusk=(dict(top=(0.40, 0.40, 0.62), bot=(0.98, 0.62, 0.56), add=(0, 0, 8), sat=0.8),
          dict(top=(0.56, 0.48, 0.54), bot=(0.46, 0.42, 0.50), add=(0, 0, 6), sat=0.72)),
    night=(dict(top=(0.15, 0.19, 0.36), bot=(0.30, 0.32, 0.50), add=(2, 4, 12), sat=0.55),
           dict(top=(0.30, 0.32, 0.45), bot=(0.22, 0.25, 0.37), add=(0, 2, 8), sat=0.5)),
    storm=(dict(top=(0.60, 0.64, 0.70), bot=(0.78, 0.80, 0.84), add=(4, 6, 10), sat=0.28),
           dict(top=(0.62, 0.68, 0.70), bot=(0.56, 0.62, 0.64), add=(0, 2, 4), sat=0.55)),
    after=(dict(top=(0.98, 1.0, 1.05), bot=(1.03, 1.03, 1.02), add=(0, 0, 0), sat=1.12),
           dict(top=(1.0, 1.04, 1.0), bot=(1.0, 1.03, 1.0), add=(0, 0, 0), sat=1.15)),
    dawn=(dict(top=(0.86, 0.84, 0.98), bot=(1.16, 0.94, 0.86), add=(16, 10, 14), sat=0.68),
          dict(top=(0.90, 0.86, 0.90), bot=(0.86, 0.84, 0.88), add=(10, 8, 12), sat=0.7)),
    morning=(dict(top=(0.97, 0.97, 1.0), bot=(1.08, 1.0, 0.94), add=(8, 6, 4), sat=0.92),
             dict(top=(1.0, 0.98, 0.96), bot=(1.0, 0.98, 0.96), add=(6, 4, 2), sat=0.96)),
)
VRAMP = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]


def gmix(a, b, u):
    u = clamp(u)
    return {k: (tuple(lerp(x, y, u) for x, y in zip(a[k], b[k])) if isinstance(a[k], tuple) else lerp(a[k], b[k], u))
            for k in a}


def grade(rgb, g):
    """In-place colour grade of a float HxWx3 array (screen-space vertical tint)."""
    if g is DAY:
        return rgb
    lum = (rgb[..., 0:1] * 0.3 + rgb[..., 1:2] * 0.59 + rgb[..., 2:3] * 0.11)
    rgb[:] = lum + (rgb - lum) * g["sat"]
    top, bot = np.array(g["top"], np.float32), np.array(g["bot"], np.float32)
    rgb *= top + (bot - top) * VRAMP
    rgb += np.array(g["add"], np.float32)
    return rgb


def add_glow(rgb, x, y, r, col, k):
    """Additive soft radial light (screen px)."""
    if k <= 0.003:
        return
    x0, x1 = int(max(0, x - r)), int(min(W, x + r))
    y0, y1 = int(max(0, y - r)), int(min(H, y + r))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
    m = np.clip(1 - d, 0, 1) ** 2.2 * k
    rgb[y0:y1, x0:x1] += m[..., None] * np.array(col, np.float32)


# ================================================================== props
def cup(p, cx, ry, tw=170, bw=140, h=150, body=(232, 226, 210), glaze=TEAL_LIGHT, saucer=True,
        coffee=True, handle=True, stamp=False, speckle=0, rng=None):
    k = tw / 170
    if saucer:
        p.ellipse((cx - 130 * k, ry + 130 * k, cx + 130 * k, ry + 190 * k), (176, 140, 100), INK, 1.2, 0.2)
        p.ellipse((cx - 110 * k, ry + 136 * k, cx + 110 * k, ry + 180 * k), (190, 156, 116), None)
    p.poly([(cx - tw / 2, ry), (cx + tw / 2, ry), (cx + bw / 2, ry + h), (cx - bw / 2, ry + h)], body, INK, 1.4, 0.4)
    p.poly([(cx - bw / 2 - 4, ry + h * 0.68), (cx + bw / 2 + 4, ry + h * 0.68), (cx + bw / 2, ry + h),
            (cx - bw / 2, ry + h)], lerpc(body, INK, 0.12) + (200,), None)
    for i in range(6):
        x = cx + tw * 0.25 + i * 6 * k
        p.simple_line([(x, ry + 15 * k), (x - 4 * k, ry + h - 10 * k)], INK + (55,), 0.6)
    if rng and speckle:
        for _ in range(speckle):
            x, y = rng.uniform(cx - bw / 2 + 6, cx + bw / 2 - 6), rng.uniform(ry + 10, ry + h - 6)
            p.ellipse((x - 1.4, y - 1.4, x + 1.4, y + 1.4), lerpc(body, INK, 0.45) + (170,), None)
    if glaze:
        drip = [(-85, 0), (85, 0), (83, 25), (60, 38), (40, 28), (15, 44), (-15, 30), (-42, 41), (-65, 28), (-83, 26)]
        p.poly([(cx + x * tw / 170, ry + y * k) for x, y in drip], glaze, INK, 0.9, 0.2)
    p.ellipse((cx - tw / 2, ry - 14 * k, cx + tw / 2, ry + 14 * k), lerpc(body, (255, 255, 255), 0.1), INK, 1.3, 0.3)
    if coffee:
        p.ellipse((cx - tw / 2 + 9 * k, ry - 10 * k, cx + tw / 2 - 9 * k, ry + 11 * k), (74, 48, 34), None)
        p.ellipse((cx - 40 * k, ry - 7 * k, cx + 20 * k, ry), (120, 86, 60, 200), None)
    else:
        p.ellipse((cx - tw / 2 + 9 * k, ry - 10 * k, cx + tw / 2 - 9 * k, ry + 11 * k), lerpc(body, INK, 0.18), None)
    if handle:
        p.arc(cx + tw / 2 + 5 * k, ry + 60 * k, 34 * k, 40 * k, -1.5, 1.5, INK, 2.6, 0.2)
        p.arc(cx + tw / 2 + 5 * k, ry + 60 * k, 34 * k, 40 * k, -1.5, 1.5, body, 1.6, 0.2)
    if stamp:  # potter's seal, pressed near the foot
        sx, sy, s = cx - bw / 2 + 16 * k, ry + h - 40 * k, 24 * k
        p.rect(sx, sy, sx + s, sy + s, (176, 54, 42), (120, 40, 32), 0.7, 0.1)
        p.ellipse((sx + s * 0.25, sy + s * 0.25, sx + s * 0.75, sy + s * 0.75), None, (246, 230, 214), 1.0, 0.05)
        p.simple_line([(sx + s * 0.5, sy + s * 0.18), (sx + s * 0.5, sy + s * 0.82)], (246, 230, 214, 255), 0.9)


PROP_OY = 1500


def prop_pen(seed):
    return Pen((int(BW * S), int((BH - PROP_OY) * S)), S, (0, PROP_OY), seed=seed)


def build_props(kind):
    path = f"{BUILD}/props_{kind}.png"
    if os.path.exists(path):
        return
    p = prop_pen(sum(map(ord, kind)))
    rng = random.Random(len(kind))
    if kind == "cup2":
        cup(p, 500, 1985, 160, 128, 140, (226, 214, 196), (82, 98, 150), rng=rng, speckle=30)
    elif kind == "tea":
        x0, x1, top, bot = 940, 1066, 1995, 2195
        p.ellipse((x0 - 10, bot - 10, x1 + 10, bot + 14), (176, 140, 100), INK, 1.0, 0.2)
        p.poly([(x0, top), (x1, top), (x1 - 8, bot), (x0 + 8, bot)], TEAL_LIGHT + (60,), INK, 1.2, 0.3)
        p.poly([(x0 + 3, top + 40), (x1 - 3, top + 40), (x1 - 10, bot - 4), (x0 + 10, bot - 4)], (178, 112, 50, 205), None)
        for (ix, iy, s) in ((962, 2030, 34), (1004, 2022, 38), (1022, 2056, 30)):
            p.poly([(ix, iy), (ix + s, iy - 4), (ix + s + 4, iy + s - 6), (ix + 2, iy + s)], (236, 240, 238, 170), (150, 170, 170), 0.6, 0.2)
        p.ellipse((x0, top - 10, x1, top + 10), (220, 236, 236, 90), INK, 1.0, 0.2)
        p.simple_line([(x0 + 12, top + 14), (x0 + 18, bot - 14)], (255, 255, 250, 210), 2.4)
        for _ in range(26):
            x, y = rng.uniform(x0 + 8, x1 - 10), rng.uniform(top + 20, bot - 10)
            p.ellipse((x - 1.6, y - 2, x + 1.6, y + 2), (250, 250, 246, 150), None)
    elif kind == "phone":
        pts = [(430, 2088), (600, 2080), (624, 2204), (448, 2214)]
        p.poly([(x + 6, y + 8) for x, y in pts], (60, 40, 24, 70), None)
        p.poly(pts, (40, 40, 46), INK, 1.2, 0.2)
        scr = [(442, 2096), (590, 2089), (611, 2196), (459, 2204)]
        p.poly(scr, (172, 204, 232), None)
        for i, yy in enumerate((2110, 2134, 2158)):
            x0 = 452 + (yy - 2096) * 0.17
            p.rect(x0 + 8, yy, x0 + 140, yy + 16, (242, 246, 250), None)
            p.ellipse((x0 + 12, yy + 3, x0 + 22, yy + 13), (150, 180, 214), None)
    elif kind == "cups5":
        shapes = [  # cx, rim y, top w, bottom w, height, body, glaze, handle
            (175, 1880, 104, 70, 70, (214, 200, 176), (120, 86, 60), False),   # wide chawan, ame glaze
            (305, 1866, 70, 62, 104, (198, 206, 204), None, False),            # tall yunomi, celadon
            (420, 1884, 96, 74, 84, (236, 228, 212), (82, 98, 150), True),     # indigo drip mug
            (548, 1872, 78, 66, 92, (176, 112, 82), (226, 212, 186), False),   # red clay, white slip
        ]
        for (cx, ry, tw, bw, hh, body, glaze, hd) in shapes:
            cup(p, cx, ry, tw, bw, hh, body, glaze, saucer=False, coffee=False, handle=hd, rng=rng, speckle=12)
        cup(p, 430, 2052, 190, 150, 158, (214, 196, 168), (150, 98, 58), saucer=False, coffee=False,
            handle=False, stamp=True, rng=rng, speckle=40)
    down(p.result()).save(path)


def build_textures(reel):
    """Sky-aligned star and rainbow textures (A: wide sky, B: close-up background)."""
    out = {}
    cl = Image.open(f"{BUILD}/cloud.png").split()[3]
    mA = Image.new("L", (int(AW * K), int(AH * K)), 0)
    mA.paste(cl, (int(-60 * K), int(260 * K)))
    s = 0.9
    c2 = cl.resize((int(cl.width * s), int(cl.height * s)), Image.LANCZOS)
    mB = Image.new("L", (int(BW * K), int(BH * K)), 0)
    mB.paste(c2, (int((620 - 620 * s) * K), int(((B_HOR - 10) - 1990 * s) * K)))
    for name, m, hor in (("A", mA, A_HOR), ("B", mB, B_HOR)):
        w, h = m.size
        free = 1 - np.asarray(m.filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
        ys = np.arange(h, dtype=np.float32)[:, None] / K
        free *= np.clip((hor - 30 - ys) / 160, 0, 1)
        if reel in (2, 3):
            rng = random.Random(7)
            for g in range(3):
                st = Image.new("L", (w, h), 0)
                d = ImageDraw.Draw(st)
                n = (6, 120, 260)[g]
                for _ in range(n):
                    x, y = rng.uniform(0, w), rng.uniform(0, (hor - 100) * K)
                    r = (2.6, 1.5, 1.0)[g] * rng.uniform(0.8, 1.2)
                    d.ellipse([x - r, y - r, x + r, y + r], fill=int((255, 220, 170)[g] * rng.uniform(0.7, 1)))
                    if g == 0:
                        d.line([x - 7, y, x + 7, y], fill=120)
                        d.line([x, y - 7, x, y + 7], fill=120)
                a = np.asarray(st.filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) * free
                rgba = np.zeros((h, w, 4), np.uint8)
                rgba[..., :3] = (250, 244, 226)
                rgba[..., 3] = np.clip(a * 1.4, 0, 255)
                out[f"stars{g}_{name}"] = Image.fromarray(rgba, "RGBA")
        if reel == 4:
            cx, cy, R = (900 * K, 2620 * K, 1250 * K) if name == "A" else (900 * K, 1840 * K, 1150 * K)
            yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
            bands = [(224, 120, 120), (232, 176, 110), (236, 222, 132), (150, 200, 140), (120, 170, 214), (130, 130, 200), (160, 120, 190)]
            bw_ = 13 * K
            rgb = np.zeros((h, w, 3), np.float32)
            a = np.zeros((h, w), np.float32)
            for i, col in enumerate(bands):
                r0 = R - i * bw_
                m_ = np.clip(1 - np.abs(d - r0) / bw_, 0, 1)
                rgb += m_[..., None] * np.array(col, np.float32)
                a = np.maximum(a, m_)
            rgb = rgb / np.maximum(a[..., None] + 1e-4, 1e-4) * np.minimum(a[..., None], 1) / np.maximum(a[..., None], 1e-4)
            fade = np.clip((ys - (hor - 900)) / 600, 0.25, 1)  # stronger near the ground
            alpha = np.clip(a * 1.4, 0, 1) * (0.25 + 0.75 * free) * 0.7 * fade
            img = Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), (alpha * 255)[..., None]], 2).astype(np.uint8), "RGBA")
            out[f"rainbow_{name}"] = img.filter(ImageFilter.GaussianBlur(5))
    return out


# ================================================================== logo
LS = 240  # logo size on screen (px)


def logo_frames():
    """Ensō (dry brush) drawn progressively, indigo ゆ, steam wisp; returns (draw_fn)."""
    ss = 3
    N = LS * ss
    c = N / 2
    Rr = 0.30 * N
    Wmax = 0.075 * N
    rng = np.random.default_rng(5)
    th0, sweep = -1.10, 5.55
    samples = 360
    nb = 16
    noise = rng.random((nb, samples // 6 + 2))
    ink = (38, 34, 32)

    def path(s):
        th = th0 + sweep * s
        r = Rr * (1 + 0.025 * math.sin(3 * th + 1) + 0.02 * s)
        return c + r * math.cos(th) * 1.02, c + r * math.sin(th), th

    def width(s):
        return Wmax * (0.30 + 0.70 * math.sin(math.pi * min(1, s * 1.05 + 0.04)) ** 0.5) * (1 - 0.30 * s)

    def enso(prog):
        im = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(im)
        n = int(samples * clamp(prog))
        for j in range(nb):
            o = (j / (nb - 1) - 0.5)
            prev = None
            for i in range(n):
                s = i / samples
                x, y, th = path(s)
                wv = width(s)
                nz = noise[j, i // 6] * 0.6 + noise[j, i // 6 + 1] * 0.4
                gap_th = 0.12 + 0.75 * clamp((s - 0.55) / 0.45) ** 1.3 + 0.25 * clamp((0.06 - s) / 0.06)
                vis = nz > gap_th or abs(o) < 0.12
                px, py = x + math.cos(th) * o * wv, y + math.sin(th) * o * wv
                if vis and prev:
                    d.line([prev, (px, py)], fill=235, width=max(2, int(wv / nb * 2.1)))
                prev = (px, py) if vis else None
        return im

    disc = Image.new("L", (N, N), 0)
    ImageDraw.Draw(disc).ellipse([0.03 * N, 0.03 * N, 0.97 * N, 0.97 * N], fill=255)
    paper = np.asarray(disc).astype(np.float32) / 255
    grain = fnoise(N, N, 3, 2, 77)
    f = ImageFont.truetype(FONT_B, int(0.36 * N))
    yu = Image.new("L", (N, N), 0)
    ImageDraw.Draw(yu).text((c - 0.01 * N, c + 0.005 * N), "ゆ", font=f, fill=255, anchor="mm")
    yu_a = np.asarray(yu).astype(np.float32) / 255 * (0.85 + 0.15 * fnoise(N, N, 5, 2, 78))
    gx, gy, _ = path(-0.045)

    def steam(prog, t):
        im = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(im)
        pts = []
        for i in range(40):
            u = i / 39
            if u > prog:
                break
            sway = 0.012 * N * math.sin(t * 1.4 + u * 3)
            pts.append((gx + 0.02 * N + 0.05 * N * math.sin(u * 5.2 - 0.6) * u + sway * u, gy - 0.03 * N - u * 0.26 * N))
        for i in range(len(pts) - 1):
            u = i / 39
            d.line([pts[i], pts[i + 1]], fill=int(230 * (1 - u * 0.8)), width=max(3, int((0.026 - 0.016 * u) * N)))
        return np.asarray(im).astype(np.float32) / 255

    cache = {}

    def draw(t, t0):
        """RGBA logo image for time t (brand card starts at t0)."""
        a_disc = smooth((t - t0) / 0.45)
        if a_disc <= 0:
            return None
        pe = round(clamp((t - t0 - 0.15) / 0.75) * 24) / 24
        if pe not in cache:
            cache[pe] = np.asarray(enso(pe)).astype(np.float32) / 255
        en = cache[pe]
        a_yu = smooth((t - t0 - 0.7) / 0.45)
        st = steam(clamp((t - t0 - 0.95) / 0.6), t)
        rgb = np.empty((N, N, 3), np.float32)
        rgb[:] = np.array((244, 239, 226), np.float32)
        rgb *= (0.96 + 0.06 * grain)[..., None]
        for (m, col) in ((en, ink), (yu_a * a_yu, INDIGO), (st * 0.85, (70, 78, 160))):
            rgb = rgb * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]
        al = paper * a_disc
        img = Image.fromarray(np.concatenate([np.clip(rgb, 0, 255), (al * 255)[..., None]], 2).astype(np.uint8), "RGBA")
        img = img.resize((LS, LS), Image.LANCZOS)
        sc = 0.94 + 0.06 * a_disc
        if sc < 0.999:
            n2 = int(LS * sc)
            img2 = Image.new("RGBA", (LS, LS), (0, 0, 0, 0))
            img2.alpha_composite(img.resize((n2, n2), Image.LANCZOS), ((LS - n2) // 2, (LS - n2) // 2))
            img = img2
        return img

    return draw


# ================================================================== text
def build_blocks(spec):
    blocks = []
    for b in spec:
        lines = []
        y = b["top"]
        imgs = [make_line_img(t, s, True, ln[2] if len(ln) > 2 else 0.06) for ln in b["lines"] for (t, s) in [ln[:2]]]
        widths = [w for (_, _, w) in imgs]
        quote = b.get("quote")
        nq = len(b["lines"]) - 1 if quote else 0
        if quote:
            inds = [0] + [1] * (nq - 1)
            span = max(widths[i] + inds[i] * b["lines"][i][1] for i in range(nq))
            x_left = TEXT_CX - span / 2
        gaps = b.get("gaps")
        for i, ((img, pad, w), ln) in enumerate(zip(imgs, b["lines"])):
            s = ln[1]
            if quote and i < nq:
                x = x_left + inds[i] * s
            elif quote:
                y += s * 0.5
                x = x_left + span - w
            else:
                x = TEXT_CX - w / 2
            lines.append(dict(img=img, x=int(x - pad), y=int(y - pad), w=w, pad=pad, t0=b["t_in"][i]))
            y += s * (gaps[i] if gaps else 1.75)
        x0 = min(l["x"] + l["pad"] for l in lines) - 70
        x1 = max(l["x"] + l["pad"] + l["w"] for l in lines) + 70
        y0 = min(l["y"] + l["pad"] for l in lines) - 50
        y1 = max(l["y"] + l["img"].height - l["pad"] for l in lines) + 30
        if b.get("logo_top"):
            y0 = min(y0, b["logo_top"] - 30)
            x0, x1 = min(x0, TEXT_CX - LS / 2 - 40), max(x1, TEXT_CX + LS / 2 + 40)
        bw, bh = int(x1 - x0 + 240), int(y1 - y0 + 240)
        m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle([120, 120, bw - 120, bh - 120], radius=80, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(55))
        back = Image.new("RGBA", (bw, bh), (30, 44, 62, 0))
        back.putalpha(m.point(lambda v: int(v * b.get("back", 0.36))))
        blocks.append(dict(lines=lines, t_out=b["t_out"], back=back, bx=int(x0 - 120), by=int(y0 - 120)))
    return blocks


def brand_spec(t0, tags):
    """Logo at the top, ゆとり場, Yutoriba, then one or two short lines."""
    lines = [("ゆとり場", 100, 0.10), ("Yutoriba", 26, 0.55)] + [(s, z) for (s, z) in tags]
    t_in = [t0 + 0.5, t0 + 0.85] + [t0 + 1.2 + 0.45 * i for i in range(len(tags))]
    gaps = [1.25, 2.0] + [1.65] * len(tags)
    return dict(lines=lines, top=600, t_in=t_in, t_out=None, gaps=gaps, logo_top=600 - 22 - LS)


# ================================================================== motion helpers
def cam_wide(t, t0, t1, top0, top1, z0, z1, xc0=620, xc1=620):
    u = 0.22 * clamp((t - t0) / (t1 - t0)) + 0.78 * ease_io((t - t0) / (t1 - t0))
    return Cam(lerp(top0, top1, u), lerp(z0, z1, u), lerp(xc0, xc1, u))


def cam_close(t, focus, keys, tilt=None):
    """Close-up camera. keys: [(time, zoom, focus screen x, focus screen y)], eased between.
    tilt=(t_start, t_end): ease to the tilted-up view (top 300, zoom 1, centred)."""
    def at(tt):
        if tt <= keys[0][0]:
            k = keys[0][1:]
        elif tt >= keys[-1][0]:
            k = keys[-1][1:]
        else:
            for a, b in zip(keys[:-1], keys[1:]):
                if a[0] <= tt <= b[0]:
                    u = ease_io((tt - a[0]) / (b[0] - a[0]))
                    k = tuple(lerp(x, y, u) for x, y in zip(a[1:], b[1:]))
                    break
        z, sx, sy = k
        return Cam(focus[1] - sy / z, z, left=focus[0] - sx / z)
    if tilt is None or t < tilt[0]:
        return at(t)
    c1 = at(tilt[0])
    u = ease_io((t - tilt[0]) / (tilt[1] - tilt[0]))
    z = lerp(c1.z, 1.0, u)
    xc1 = c1.left + (W / 2) / c1.z
    return Cam(lerp(c1.top, 300, u), z, lerp(xc1, 620, u))


class Rain:
    def __init__(self, seed=3, n=900):
        r = random.Random(seed)
        self.d = [(r.uniform(-200, W + 100), r.uniform(0, H + 300), r.uniform(2100, 2900), r.uniform(28, 64),
                   r.uniform(0.18, 0.5)) for _ in range(n)]

    def draw(self, frame, t, k):
        if k <= 0.01:
            return
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        n = int(len(self.d) * clamp(k))
        for (x, y0, v, L, a) in self.d[:n]:
            y = (y0 + v * t) % (H + 300) - 150
            xx = x + 0.2 * (y + 150)
            d.line([(xx, y), (xx + 0.2 * L, y + L)], fill=(214, 224, 234, int(255 * a * min(1, k * 1.3))), width=2)
        frame.alpha_composite(ov)


class Fireworks:
    COLS = [(255, 200, 130), (255, 156, 146), (172, 226, 204), (206, 186, 255)]

    def __init__(self, bursts):
        self.b = []
        for i, (t0, x, y, R, ci, life) in enumerate(bursts):
            r = random.Random(i * 13 + 1)
            parts = [(r.uniform(0, 2 * math.pi), r.uniform(0.82, 1.0)) for _ in range(72)]
            self.b.append((t0, x, y, R, self.COLS[ci], life, parts))

    def draw(self, rgb, t, scale=1.0):
        lo = 2
        im = Image.new("RGB", (W // lo, H // lo), (0, 0, 0))
        d = ImageDraw.Draw(im)
        flash = 0.0
        any_ = False
        for (t0, x, y, R, col, life, parts) in self.b:
            if t0 - 0.55 < t < t0:  # rising shell
                u = (t - t0 + 0.55) / 0.55
                yy = y + (1 - u) * 340
                d.line([(x / lo, yy / lo), (x / lo, (yy + 40) / lo)], fill=tuple(int(c * 0.6) for c in col), width=1)
                any_ = True
            a = t - t0
            if a < 0 or a > life:
                continue
            any_ = True
            br = math.exp(-a * 2.6 / life) * (1 - a / life) ** 0.5
            flash = max(flash, math.exp(-a * 7))
            for (ang, sp) in parts:
                def pos(aa):
                    rr = R * sp * (1 - math.exp(-aa * 4.5)) * scale
                    return (x + rr * math.cos(ang)) / lo, (y + rr * math.sin(ang) + 70 * aa * aa * scale) / lo
                p1, p0 = pos(a), pos(max(0, a - 0.14))
                tw = 0.75 + 0.25 * math.sin(a * 40 + ang * 9)
                c = tuple(int(cc * br * tw) for cc in col)
                d.line([p0, p1], fill=c, width=2)
        if not any_:
            return 0.0
        arr = np.asarray(im).astype(np.float32)
        glow = np.asarray(im.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)
        add = np.asarray(Image.fromarray(np.clip(arr + glow * 1.6, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)).astype(np.float32)
        rgb += add
        return flash


def draw_lantern(d, cam, lit, ss=2):
    cx, cy = 394, 2358
    X, Y = cam.ws(cx, cy)
    w, h = 15 * cam.z, 21 * cam.z
    body = lerpc((232, 222, 196), (255, 214, 140), lit)
    d.line([(X * ss, (Y - h - 22 * cam.z) * ss), (X * ss, (Y - h) * ss)], fill=INK + (255,), width=2)
    d.ellipse([(X - w) * ss, (Y - h) * ss, (X + w) * ss, (Y + h) * ss], fill=body + (255,), outline=INK + (255,), width=2)
    for k in (-0.55, 0, 0.55):
        yy = Y + k * h
        hw = w * math.sqrt(max(0, 1 - k * k)) * 0.98
        d.line([((X - hw) * ss, yy * ss), ((X + hw) * ss, yy * ss)], fill=lerpc(body, INK, 0.35) + (255,), width=1)
    d.rectangle([(X - w * 0.55) * ss, (Y - h - 3 * cam.z) * ss, (X + w * 0.55) * ss, (Y - h + 2 * cam.z) * ss], fill=(54, 42, 36, 255))
    d.rectangle([(X - w * 0.55) * ss, (Y + h - 2 * cam.z) * ss, (X + w * 0.55) * ss, (Y + h + 3 * cam.z) * ss], fill=(54, 42, 36, 255))
    d.line([((X - w * 0.35) * ss, (Y - h * 0.3) * ss), ((X + w * 0.35) * ss, (Y - h * 0.3) * ss)], fill=(176, 60, 46, 255), width=3)
    return X, Y


def draw_chime(d, cam, t, ss=2):
    hx, hy = 1010.0, 276.0
    th = 0.07 * math.sin(1.6 * t) + 0.035 * math.sin(3.3 * t + 1)
    th2 = th * 2.2 + 0.06 * math.sin(2.4 * t + 0.5)

    def R(x, y, a=th, ox=hx, oy=hy):
        dx, dy = x - ox, y - oy
        return ox + dx * math.cos(a) - dy * math.sin(a), oy + dx * math.sin(a) + dy * math.cos(a)

    def S(p):
        X, Y = cam.ws(*p)
        return X * ss, Y * ss
    top = 800.0
    d.line([S(R(hx, hy)), S(R(hx, top))], fill=INK + (255,), width=2)
    bell = [R(hx + 46 * math.cos(a), top + 48 - 48 * math.sin(a)) for a in np.linspace(0, math.pi, 24)]
    bell = [R(hx + 46, top + 52)] + bell + [R(hx - 46, top + 52)]
    d.polygon([S(p) for p in bell], fill=(206, 230, 238, 215), outline=INK + (255,))
    for a0 in (0.5, 2.3):
        arc = [R(hx + 34 * math.cos(a), top + 40 - 30 * math.sin(a)) for a in np.linspace(a0, a0 + 0.5, 6)]
        d.line([S(p) for p in arc], fill=(196, 64, 54, 255), width=max(2, int(4 * cam.z)), joint="curve")
    d.line([S(R(hx, top + 10)), S(R(hx, top + 70))], fill=INK + (255,), width=2)
    cl = R(hx, top + 66)
    strip_top = cl
    corners = [(-16, 0), (16, 0), (16, 150), (-16, 150)]
    pts = [R(strip_top[0] + x, strip_top[1] + y, th2 - th, strip_top[0], strip_top[1]) for x, y in corners]
    d.polygon([S(p) for p in pts], fill=(236, 226, 200, 255), outline=INK + (255,))
    d.line([S(R(strip_top[0], strip_top[1] + 30, th2 - th, *strip_top)), S(R(strip_top[0], strip_top[1] + 120, th2 - th, *strip_top))],
           fill=(110, 120, 160, 255), width=max(1, int(2 * cam.z)))


def draw_spout(d, cam, t, t_in, t_out, ss=2):
    if t < t_in - 0.4 or t > t_out + 0.5:
        return False
    e = ease_io((t - t_in + 0.4) / 0.4) * (1 - ease_io((t - t_out) / 0.5))
    off = (1 - e) * 420
    pts = [(1300 + off, 1420 - off), (1000 + off, 1600 - off), (880 + off, 1740 - off), (812 + off, 1862 - off)]
    S = [tuple(v * ss for v in cam.ws(*p)) for p in pts]
    d.line(S, fill=INK + (255,), width=int(30 * cam.z * ss), joint="curve")
    d.line(S, fill=(150, 164, 164, 255), width=int(25 * cam.z * ss), joint="curve")
    d.line([(x - 4 * ss, y - 3 * ss) for x, y in S], fill=(196, 208, 206, 255), width=int(3 * cam.z * ss), joint="curve")
    pour = clamp((t - t_in) / 0.25) * (1 - clamp((t - t_out + 0.2) / 0.2))
    if pour > 0:
        sx, sy = pts[-1]
        stream = [(sx + (762 - sx) * u + 3 * math.sin(t * 20 + u * 9) * u, sy + 4 + (1958 - sy - 4) * u ** 1.25) for u in np.linspace(0, 1, 12)]
        d.line([tuple(v * ss for v in cam.ws(*p)) for p in stream], fill=(92, 58, 38, int(235 * pour)),
               width=max(2, int(7 * cam.z * ss * pour)), joint="curve")
        X, Y = cam.ws(762, 1958)
        for k in range(3):
            r = (10 + 14 * ((t * 2.2 + k / 3) % 1)) * cam.z
            d.ellipse([(X - r * 1.6) * ss, (Y - r * 0.4) * ss, (X + r * 1.6) * ss, (Y + r * 0.4) * ss],
                      outline=(150, 112, 80, int(160 * pour)), width=2)
    return True


def draw_drips(d, cam, t, k, ss=2):
    if k <= 0.01:
        return
    for i, wx in enumerate((150, 330, 610, 840, 1060)):
        period = 0.55 + 0.17 * i
        for j in range(2):
            ph = ((t + i * 0.37 + j * period / 2) % period) / period
            X, _ = cam.ws(wx, 0)
            y = -20 + ph ** 1.8 * (H * 0.75)
            a = int(200 * k * (1 - ph) ** 0.3)
            r = 4 * cam.z
            d.ellipse([(X - r) * ss, (y - r * 2.4) * ss, (X + r) * ss, (y + r) * ss], fill=(226, 236, 244, a))


def steam(frame, t, cam, cx, cy, grow0=None, alpha=1.0, col=(250, 246, 236), dur=2.6):
    lo = 2
    w, h = W // lo, H // lo
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    grow = ease_io((t - grow0) / dur) if grow0 is not None else 0.0
    Hs = lerp(300, 1500, grow)
    for k in range(5):
        ph = k * 1.7 + cx * 0.01
        pts = []
        for i in range(40):
            s = i / 39
            x = cx + (k - 2) * 18 + (26 + 60 * grow) * s ** 1.1 * math.sin(5.5 * s - 1.3 * t + ph) + 40 * grow * s
            y = cy - s * Hs
            X, Y = cam.ws(x, y)
            pts.append((X / lo, Y / lo, s))
        for i in range(len(pts) - 1):
            s = pts[i][2]
            a = (1 - s) ** 1.3 * smooth(s / 0.08) * (150 - 40 * grow) * alpha
            wdt = lerp(5, 16 + 30 * grow, s) * cam.z / lo * 1.6
            d.line([pts[i][:2], pts[i + 1][:2]], fill=int(a), width=max(1, int(wdt)))
    if grow0 is not None and t > grow0:
        for k in range(7):
            age = t - grow0 - k * 0.32
            if age <= 0:
                continue
            y = cy - 120 - age * 260
            x = cx + 30 * math.sin(age * 1.3 + k) + 30 * age
            r = 30 + age * 60
            a = 90 * smooth(age / 0.5) * clamp(1 - age / 2.6) * alpha
            X, Y = cam.ws(x, y)
            d.ellipse([(X - r) / lo, (Y - r * 0.8) / lo, (X + r) / lo, (Y + r * 0.8) / lo], fill=int(a))
    layer = layer.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BICUBIC)
    st = Image.new("RGBA", (W, H), col + (0,))
    st.putalpha(layer)
    frame.alpha_composite(st)


def sunlight(rgb, t, cam, t0, col, speed=95):
    lo = 4
    yy, xx = np.mgrid[0:H // lo, 0:W // lo].astype(np.float32) * lo
    wx = xx / cam.z + cam.left
    wy = yy / cam.z + cam.top
    c = 120 + speed * (t - t0)
    q = (wx - c) * 0.86 + (wy - 2000) * 0.5
    band = np.exp(-(q / 170) ** 2)
    vert = np.clip((wy - 1830) / 60, 0, 1) * np.clip((2300 - wy) / 40, 0, 1)
    m = np.asarray(Image.fromarray((band * vert).astype(np.float32), "F").resize((W, H), Image.BILINEAR))
    rgb += m[..., None] * np.array(col, np.float32)


# ================================================================== reels
class Reel:
    n = 0
    slug = ""
    look = staticmethod(lambda t: ("day", "day", 0.0))   # (preset a, preset b, mix)
    shots = []       # (t0, t1, kind, opts)
    cuts = []        # (time, transition)
    text = []
    brand_t = 12.2
    tags = []
    lantern = None   # t -> lit amount, or None (no lantern)
    rain = None      # t -> intensity
    stars = None     # t -> (g0, g1, g2)
    rainbow = None   # t -> alpha
    mist = None      # t -> amount
    fireworks = []
    bikes = None     # t -> [(sprite, dx, dy)]
    calm_end = True


def look_at(reel, t):
    a, b, u = reel.look(t)
    sa, ga = G[a]
    sb, gb = G[b]
    return gmix(sa, sb, u), gmix(ga, gb, u)


class Reel1(Reel):
    n, slug = 1, "hajimemashite"
    # afternoon; a bicycle arrives, coffee is poured, steam rises into the cloud
    shots = [(0.0, 6.3, "wide", dict(cam=lambda t: cam_wide(t, 0, 6.3, 200, 1212, 1.0, 1.08, 612, 628), ref=1212)),
             (6.3, 11.6, "close", dict(focus=(700, 2000), keys=[(6.3, 1.0, 620, 1310), (9.6, 1.08, 620, 1310)],
                                       tilt=(9.6, 11.9), props=[], book=True, cups=[(760, 1952, 9.6)],
                                       spout=(7.0, 8.4), sun=((34, 22, 6), 6.3))),
             (11.6, 15.0, "wide", dict(cam=lambda t: cam_wide(t, 11.6, 15, 1104, 1112, 1.03, 1.045), ref=1104, end=True))]
    cuts = [(6.3, "cloth"), (11.6, "grass")]
    text = [
        dict(lines=[("急ぐ毎日の、途中に。", 58)], top=440, t_in=[0.5], t_out=(3.0, 3.35)),
        dict(lines=[("ひと休みできる場所が", 56), ("あったら。", 56)], top=560, t_in=[3.55, 4.1], t_out=(5.75, 6.1)),
        dict(lines=[("コーヒーを一杯。", 56), ("人生のこと、心のこと、", 48), ("神さまのこと。", 48)], top=470,
             t_in=[6.6, 7.5, 8.0], t_out=(9.55, 9.9)),
        dict(lines=[("答えを急がず、", 56), ("一緒に考える。", 56)], top=560, t_in=[10.0, 10.5], t_out=(11.85, 12.15)),
    ]
    tags = [("ゆっくり考える場所。", 38), ("フォローして、ひと休みしに来てね。", 31)]

    @staticmethod
    def bikes(t):
        u = clamp((t - 2.9) / 2.8)
        e = 1 - (1 - u) ** 2.4
        return [("bike", -760 * (1 - e), 1.2 * math.sin(t * 9) * (1 - e))]


class Reel2(Reel):
    n, slug = 2, "yasundeii"
    shots = [(0.0, 4.6, "wide", dict(cam=lambda t: cam_wide(t, 0, 4.6, 640, 1212, 1.0, 1.08, 612, 628), ref=1212)),
             (4.6, 10.6, "close", dict(focus=(560, 2060), keys=[(4.6, 1.0, 480, 1370), (8.8, 1.08, 480, 1370)],
                                       tilt=(8.8, 10.9), props=["tea"], book=True, hand=(4.9, 5.45, 5.95, 6.6, 5.4, 6.4),
                                       cups=[(760, 1952, 8.8)], sun=((52, 26, 2), 4.6))),
             (10.6, 15.0, "wide", dict(cam=lambda t: cam_wide(t, 10.6, 15, 1100, 1112, 1.03, 1.05), ref=1104, end=True))]
    cuts = [(4.6, "cloth"), (10.6, "grass")]
    text = [
        dict(lines=[("今日も、", 58), ("がんばりすぎてない？", 58)], top=470, t_in=[0.45, 0.95], t_out=(2.95, 3.3)),
        dict(lines=[("「疲れた」って、", 56), ("言えてる？", 56)], top=560, t_in=[3.4, 3.9], t_out=(5.5, 5.85)),
        dict(lines=[("「すべて疲れた人、", 46), ("重荷を負っている人は", 46), ("わたしのもとに来なさい。", 46),
                    ("わたしがあなたがたを", 46), ("休ませてあげます。」", 46), ("マタイの福音書 11:28", 30)],
             top=440, t_in=[6.0, 6.35, 6.7, 7.3, 7.65, 8.2], t_out=(10.15, 10.5), quote=True,
             gaps=[1.6] * 6),
        dict(lines=[("休んでいい。", 66)], top=600, t_in=[10.65], t_out=(11.8, 12.1)),
    ]
    tags = [("ゆっくり考える場所。", 38), ("今日がんばった人に、送ってあげて。", 30)]

    @staticmethod
    def look(t):
        return ("sunset", "dusk", smooth((t - 10.4) / 3.2))

    lantern = staticmethod(lambda t: smooth((t - 11.0) / 0.5) * (0.92 + 0.08 * math.sin(t * 13) * math.sin(t * 5.3)))
    stars = staticmethod(lambda t: (0.75 * smooth((t - 11.6) / 1.2), 0.0, 0.0))


class Reel3(Reel):
    n, slug = 3, "hanabi"
    shots = [(0.0, 3.4, "wide", dict(cam=lambda t: cam_wide(t, 0, 3.4, 1060, 1100, 1.0, 1.03), ref=1104, birds=False)),
             (3.4, 10.6, "close", dict(focus=(640, 2000), keys=[(3.4, 1.0, 560, 1310), (8.3, 1.07, 560, 1310)],
                                       tilt=(8.3, 10.9), props=["cup2"], chime=True, cups=[(760, 1952, 8.3), (500, 1977, None)])),
             (10.6, 15.0, "wide", dict(cam=lambda t: cam_wide(t, 10.6, 15, 1100, 1112, 1.03, 1.05), ref=1104, end=True))]
    cuts = [(3.4, "dissolve"), (10.6, "grass")]
    look = staticmethod(lambda t: ("night", "night", 0.0))
    text = [
        dict(lines=[("きれいなものほど、", 56), ("すぐに消えていく。", 56)], top=500, t_in=[0.4, 0.95], t_out=(2.85, 3.2)),
        dict(lines=[("花火も、夏も、", 56), ("大切な時間も。", 56)], top=540, t_in=[3.35, 3.95], t_out=(5.45, 5.8)),
        dict(lines=[("なのに、なぜ", 52), ("「ずっと続いてほしい」と", 52), ("思うんだろう。", 52)], top=480,
             t_in=[5.95, 6.45, 7.0], t_out=(8.35, 8.7)),
        dict(lines=[("「神はまた、", 54), ("人の心に永遠を", 54), ("与えられた。」", 54), ("伝道者の書 3:11", 32)],
             top=470, t_in=[8.85, 9.25, 9.65, 10.2], t_out=(11.75, 12.05), quote=True),
    ]
    tags = [("その切なさは、", 36), ("永遠を知っている心のしるしかも。", 34)]
    lantern = staticmethod(lambda t: 0.9 + 0.1 * math.sin(t * 11) * math.sin(t * 4.1))
    stars = staticmethod(lambda t: (smooth((t - 6.8) / 1.5) * 0.9 + 0.1, smooth((t - 8.6) / 2.0) * 0.95,
                                    smooth((t - 9.4) / 2.2) * 0.9))
    fireworks = [(0.25, 800, 330, 175, 0, 2.2), (1.25, 250, 400, 140, 1, 2.0), (2.15, 690, 210, 205, 2, 2.3),
                 (2.85, 930, 480, 110, 3, 1.8), (3.7, 300, 300, 185, 0, 2.2), (4.55, 770, 210, 150, 1, 2.0),
                 (5.35, 540, 250, 240, 0, 3.4)]


class Reel4(Reel):
    n, slug = 4, "amayadori"
    shots = [(0.0, 3.2, "close", dict(focus=(520, 2150), keys=[(0.0, 1.04, 470, 1420), (3.2, 1.12, 470, 1420)],
                                      props=["phone"], phone=True, cups=[(760, 1952, None)])),
             (3.2, 6.1, "wide", dict(cam=lambda t: cam_wide(t, 3.2, 6.1, 1090, 1110, 1.0, 1.04), ref=1104, birds=False)),
             (6.1, 11.3, "close", dict(focus=(640, 2000), keys=[(6.1, 1.0, 560, 1310), (9.5, 1.07, 560, 1310)],
                                       tilt=(9.5, 11.6), props=["cup2"], cups=[(760, 1952, 9.5), (500, 1977, None)])),
             (11.3, 15.0, "wide", dict(cam=lambda t: cam_wide(t, 11.3, 15, 1100, 1112, 1.03, 1.05), ref=1104, end=True))]
    cuts = [(3.2, "dissolve"), (6.1, "dissolve"), (11.3, "grass")]
    text = [
        dict(lines=[("つながってるはずなのに、", 52), ("なんでさみしいんだろう。", 52)], top=480, t_in=[0.4, 1.0], t_out=(2.85, 3.2)),
        dict(lines=[("雨宿りで、", 58), ("はじめて話した。", 58)], top=540, t_in=[6.4, 6.9], t_out=(8.5, 8.85)),
        dict(lines=[("「人がひとりでいるのは", 54), ("良くない。」", 54), ("創世記 2:18", 32)],
             top=520, t_in=[9.0, 9.5, 10.1], t_out=(11.75, 12.05), quote=True),
    ]
    tags = [("人は、つながるように", 38), ("造られた。", 38)]

    @staticmethod
    def look(t):
        return ("storm", "after", smooth((t - 8.7) / 1.8))

    rain = staticmethod(lambda t: clamp(0.25 + 0.75 * smooth((t - 2.6) / 1.0)) * (1 - smooth((t - 8.2) / 1.2)))
    rainbow = staticmethod(lambda t: smooth((t - 10.0) / 2.2))

    @staticmethod
    def bikes(t):
        out = []
        for (name, t0, dur, x1, dy) in (("bike", 3.45, 2.1, 0, 0), ("bike2", 3.85, 2.2, -120, 30)):
            u = clamp((t - t0) / dur)
            e = 1 - (1 - u) ** 2.4
            out.append((name, x1 - 820 * (1 - e), dy + 1.2 * math.sin(t * 9 + dy) * (1 - e)))
        return out


class Reel5(Reel):
    n, slug = 5, "sakuhin"
    shots = [(0.0, 3.2, "wide", dict(cam=lambda t: cam_wide(t, 0, 3.2, 1070, 1100, 1.0, 1.03), ref=1104, birds=False)),
             (3.2, 11.0, "close", dict(focus=(386, 2190), keys=[(3.2, 1.0, 306, 1500), (5.8, 1.04, 330, 1440),
                                                              (8.4, 1.42, 470, 1330), (9.0, 1.42, 470, 1330)],
                                       tilt=(9.0, 11.3), props=["cups5"], cups=[(760, 1952, 9.0)],
                                       spout=(9.0, 10.0), sun=((40, 24, 18), 4.0))),
             (11.0, 15.0, "wide", dict(cam=lambda t: cam_wide(t, 11.0, 15, 1100, 1112, 1.03, 1.05), ref=1104, end=True))]
    cuts = [(3.2, "dissolve"), (11.0, "grass")]
    text = [
        dict(lines=[("比べて、比べて、", 58), ("疲れてない？", 58)], top=500, t_in=[0.4, 0.95], t_out=(2.85, 3.2)),
        dict(lines=[("同じ形の器は、", 56), ("ひとつもない。", 56)], top=540, t_in=[3.4, 3.95], t_out=(5.5, 5.85)),
        dict(lines=[("ていねいに作られたものには、", 50), ("必ず作り手がいる。", 50)], top=520, t_in=[6.0, 6.6], t_out=(8.45, 8.8)),
        dict(lines=[("「私たちは", 56), ("神の作品であって」", 56), ("エペソ人への手紙 2:10", 32)],
             top=520, t_in=[8.95, 9.4, 10.0], t_out=(11.75, 12.05), quote=True),
    ]
    tags = [("あなたも、目的をもって", 38), ("造られた。", 38)]

    @staticmethod
    def look(t):
        return ("dawn", "morning", smooth((t - 8.5) / 4.0))

    mist = staticmethod(lambda t: 1 - 0.75 * smooth((t - 6.0) / 7.0))


REELS = {1: Reel1, 2: Reel2, 3: Reel3, 4: Reel4, 5: Reel5}

# ================================================================== frame assembly
RR = {}


def init(n):
    R0.init()
    reel = REELS[n]
    RR["reel"] = reel
    RR["ground"] = Image.open(f"{BUILD}/A_ground.png").convert("RGBA")
    if reel.bikes:
        RR["nobike"] = Image.open(f"{BUILD}/A_ground_nobike.png").convert("RGBA")
        RR["front"] = Image.open(f"{BUILD}/A_front.png").convert("RGBA")
        RR["bike"] = Image.open(f"{BUILD}/bike.png").convert("RGBA")
        RR["bike2"] = Image.open(f"{BUILD}/bike2.png").convert("RGBA")
    for s in reel.shots:
        for pk in s[3].get("props", []):
            RR["props_" + pk] = Image.open(f"{BUILD}/props_{pk}.png").convert("RGBA")
    RR["tex"] = build_textures(n)
    spec = list(reel.text) + [brand_spec(reel.brand_t, reel.tags)]
    RR["text"] = build_blocks(spec)
    RR["logo"] = logo_frames()
    RR["rain"] = Rain()
    RR["fw"] = Fireworks(reel.fireworks)
    mist = fnoise(W * 2, 520, 140, 4, 61)
    yy = np.linspace(-1, 1, 520, dtype=np.float32)[:, None]
    RR["mist"] = (np.clip(mist * 1.3 - 0.2, 0, 1) * np.exp(-(yy / 0.55) ** 2)).astype(np.float32)


def sky_tex_layers(reel, t, world):
    out = []
    if reel.stars:
        for g, a in enumerate(reel.stars(t)):
            if a > 0.01:
                out.append((RR["tex"][f"stars{g}_{world}"], a))
    if reel.rainbow:
        a = reel.rainbow(t)
        if a > 0.01:
            out.append((RR["tex"][f"rainbow_{world}"], a))
    return out


def comp_tex(rgb, tex, a):
    arr = np.asarray(tex).astype(np.float32)
    al = arr[..., 3:4] / 255 * a
    rgb[:] = rgb * (1 - al) + arr[..., :3] * al


def frame_wide(t, o):
    reel = RR["reel"]
    cam = o["cam"](t)
    ref = o["ref"]
    gs, gg = look_at(reel, t)
    sky = place(R0.R["skyA"], (0, 0), cam, ref, p=0.86, dx=-0.9 * t)
    rgb = np.asarray(sky).astype(np.float32)
    grade(rgb, gs)
    for tex, a in sky_tex_layers(reel, t, "A"):
        comp_tex(rgb, place(tex, (0, 0), cam, ref, p=0.86, dx=-0.9 * t), a)
    eff_top = ref + (cam.top - ref) * 0.86
    hy = (A_HOR - eff_top) * cam.z
    if reel.fireworks:  # fireworks sit behind the ground
        RR["fw"].draw(rgb, t)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if reel.bikes:
        g.alpha_composite(place(RR["nobike"], (0, G_OY), cam, ref))
        bk = reel.bikes(t)
        for i, (name, dx, dy) in enumerate(bk):
            g.alpha_composite(place(RR[name], (BIKE_ORIGIN[0], BIKE_ORIGIN[1] - dy), cam, ref, dx=dx))
            if i == 0:
                g.alpha_composite(place(RR["front"], (0, G_OY), cam, ref))
    else:
        g.alpha_composite(place(RR["ground"], (0, G_OY), cam, ref))
    calm = lerp(1.0, 0.55, smooth((t - o.get("t0", 0) - 0.3) / 1.2)) if o.get("end") else 1.0
    g.alpha_composite(overlay_wide(t, cam, calm, -(cam.top - 200) * 0.10 if not o.get("end") else -100, o.get("birds", True)))
    lit = reel.lantern(t) if reel.lantern else 0.0
    if reel.lantern:
        ov = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
        LX, LY = draw_lantern(ImageDraw.Draw(ov), cam, lit)
        g.alpha_composite(ov.resize((W, H), Image.LANCZOS))
    ga = np.asarray(g).astype(np.float32)
    grade(ga[..., :3], gg)
    al = ga[..., 3:4] / 255
    rgb = rgb * (1 - al) + ga[..., :3] * al
    if reel.lantern and lit > 0.01:
        add_glow(rgb, LX, LY, 420 * cam.z, (255, 170, 80), 0.55 * lit)
        add_glow(rgb, LX, LY, 70 * cam.z, (255, 220, 160), 0.9 * lit)
    if reel.n == 2:
        add_glow(rgb, -80, hy - 60, 1100, (255, 150, 80), 0.45 * (1 - smooth((t - 10.6) / 3.0)))
    if reel.n == 5:
        add_glow(rgb, W + 60, hy - 40, 1150, (255, 196, 150), 0.30 + 0.15 * smooth((t - 9.0) / 2.5))
    if reel.n == 4:
        add_glow(rgb, W * 0.75, 200, 1300, (255, 240, 200), 0.35 * smooth((t - 9.0) / 1.5) * (1 - smooth((t - 12.0) / 3)))
    if reel.mist:
        mist_pass(rgb, reel.mist(t), t, hy)
    frame = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    if reel.rain:
        RR["rain"].draw(frame, t, reel.rain(t))
    return frame


def mist_pass(rgb, m, t, hy):
    if m <= 0.01:
        return
    mm = RR["mist"]
    off = int((t * 14) % W)
    band = mm[:, off:off + W]
    y0 = int(hy - 260)
    ys0, ys1 = max(0, y0), min(H, y0 + band.shape[0])
    if ys1 > ys0:
        b = band[ys0 - y0: ys1 - y0][..., None] * 0.75 * m
        rgb[ys0:ys1] = rgb[ys0:ys1] * (1 - b) + np.array((246, 234, 230), np.float32) * b
    rgb[:] = rgb * (1 - 0.12 * m) + np.array((240, 226, 226), np.float32) * 0.12 * m


def frame_close(t, o):
    reel = RR["reel"]
    cam = cam_close(t, o["focus"], o["keys"], o.get("tilt"))
    ref = 690
    gs, gg = look_at(reel, t)
    bg = place(R0.R["bgB"], (0, 0), cam, ref, p=0.75, dx=-0.9 * t)
    rgb = np.asarray(bg).astype(np.float32)
    eff_top = ref + (cam.top - ref) * 0.75
    hy = (B_HOR - eff_top) * cam.z
    sky = grade(rgb.copy(), gs)
    grd = grade(rgb, gg)
    ramp = np.clip((np.arange(H, dtype=np.float32) - (hy - 30)) / 60, 0, 1)[:, None, None]
    rgb = sky * (1 - ramp) + grd * ramp
    for tex, a in sky_tex_layers(reel, t, "B"):
        comp_tex(rgb, place(tex, (0, 0), cam, ref, p=0.75, dx=-0.9 * t), a)
    if reel.fireworks:
        fl = RR["fw"].draw(rgb, t, 1.1)
        rgb += np.array((60, 46, 40), np.float32) * fl * 0.18
    g = place(R0.R["standB"], (0, 0), cam, ref)
    for pk in o.get("props", []):
        g.alpha_composite(place(RR["props_" + pk], (0, PROP_OY), cam, ref))
    ss = 2
    ov = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    if o.get("book"):
        hand = o.get("hand")
        if hand:
            hi0, hi1, hrel, hout, b0, b1 = hand
            R0.HAND_IN, R0.HAND_REL, R0.HAND_OUT = (hi0, hi1), hrel, hout
            R0.book_theta = lambda tt: math.pi * ease_io((tt - b0) / (b1 - b0))
        else:
            R0.HAND_IN = (99, 100)
            R0.book_theta = lambda tt: 0.0
        R0.draw_book_hand(ov, t, cam, ss)
    if o.get("chime"):
        draw_chime(d, cam, t, ss)
    if o.get("spout"):
        draw_spout(d, cam, t, *o["spout"], ss=ss)
    rk = reel.rain(t) if reel.rain else 0
    drip_k = max(rk, 0.5 * (1 - smooth((t - 9.5) / 2.0))) if reel.rain else 0
    draw_drips(d, cam, t, drip_k, ss)
    g.alpha_composite(ov.resize((W, H), Image.LANCZOS))
    ga = np.asarray(g).astype(np.float32)
    grade(ga[..., :3], gg)
    al = ga[..., 3:4] / 255
    rgb = rgb * (1 - al) + ga[..., :3] * al
    if o.get("sun"):
        col, t0 = o["sun"]
        sunlight(rgb, t, cam, t0, col)
    if reel.n == 3:  # warm lantern light from the left, plus firework flashes
        add_glow(rgb, -150, 700, 1500, (255, 170, 90), 0.20 * (0.94 + 0.06 * math.sin(t * 11)))
        add_glow(rgb, 200, 1500, 900, (255, 190, 120), 0.07)
    if o.get("phone"):
        X, Y = cam.ws(525, 2148)
        add_glow(rgb, X, Y, 420 * cam.z, (120, 170, 230), 0.32 + 0.06 * math.sin(t * 3))
    if reel.n == 2:
        add_glow(rgb, -80, hy - 60, 1100, (255, 150, 80), 0.40)
    if reel.n == 5:
        add_glow(rgb, W + 60, hy - 40, 1150, (255, 196, 150), 0.30 + 0.15 * smooth((t - 9.0) / 2.5))
    if reel.n == 4:
        add_glow(rgb, W * 0.75, 200, 1300, (255, 240, 200), 0.35 * smooth((t - 9.0) / 1.5))
    if reel.mist:
        mist_pass(rgb, reel.mist(t) * 0.5, t, hy)
    frame = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    night = reel.n == 3
    for (cx, cy, g0) in o.get("cups", []):
        steam(frame, t, cam, cx, cy, g0, alpha=0.75 if night else (0.8 if reel.n == 4 and t < 9 else 1.0))
    if reel.rain:
        RR["rain"].draw(frame, t, rk * 0.8)
    return frame


def shot_at(t, shot):
    t0, t1, kind, o = shot
    o = dict(o, t0=t0)
    return frame_wide(t, o) if kind == "wide" else frame_close(t, o)


def render(i):
    reel = RR["reel"]
    t = i / FPS
    k = next(j for j, s in enumerate(reel.shots) if s[0] <= t < s[1] or j == len(reel.shots) - 1)
    frame = shot_at(t, reel.shots[k])
    for (tc, kind) in reel.cuts:
        if kind == "dissolve" and tc - 0.3 <= t < tc + 0.3:
            a, b = [s for s in reel.shots if s[1] == tc][0], [s for s in reel.shots if s[0] == tc][0]
            fa = shot_at(t, a) if t >= tc else frame
            fb = frame if t >= tc else shot_at(t, b)
            frame = Image.blend(fa, fb, smooth((t - tc + 0.3) / 0.6))
        if kind == "grass":
            if tc - 0.2 <= t < tc:
                b = [s for s in reel.shots if s[0] == tc][0]
                frame = Image.blend(frame, shot_at(t, b), smooth((t - tc + 0.2) / 0.2))
            if tc - 0.45 <= t <= tc + 0.45:
                x = 540 + (t - tc) / 0.38 * 1250
                frame.alpha_composite(R0.R["curtain"], (int(x - R0.R["curtain"].width / 2), 0))
        if kind == "cloth" and tc - 0.5 <= t <= tc + 0.55:
            x = 540 + (tc - t) / 0.5 * 1150
            frame.alpha_composite(R0.R["cloth"], (int(x - R0.R["cloth"].width / 2), 0))
    if not os.environ.get("NOTEXT"):
        R0.text_layer(frame, t, RR["text"])
        lg = RR["logo"](t, reel.brand_t)
        if lg is not None:
            sh = Image.new("RGBA", (LS + 80, LS + 80), (0, 0, 0, 0))
            m = lg.split()[3].point(lambda v: int(v * 0.45))
            sh.paste((20, 24, 30, 255), (40, 46), m)
            frame.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (TEXT_CX - LS // 2 - 40, 600 - 22 - LS - 40))
            frame.alpha_composite(lg, (TEXT_CX - LS // 2, 600 - 22 - LS))
    arr = np.asarray(frame.convert("RGB")).astype(np.float32)
    arr = arr * R0.R["paper"]
    arr = arr * 0.965 + 6.0
    arr[..., 0] *= 1.008
    arr[..., 2] *= 0.992
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def main():
    n = int(sys.argv[1])
    reel = REELS[n]
    for s in reel.shots:
        for pk in s[3].get("props", []):
            build_props(pk)
    out_dir = f"{BUILD}/b2_{n}"
    os.makedirs(out_dir, exist_ok=True)
    if len(sys.argv) > 2 and sys.argv[2] == "stills":
        init(n)
        for tt in [float(x) for x in sys.argv[3:]]:
            Image.frombytes("RGB", (W, H), render(int(round(tt * FPS)))).save(f"{out_dir}/still_{tt:05.2f}.png")
        return
    out = f"{out_dir}/video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "animation", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4, initializer=init, initargs=(n,)) as pool:
        for k, buf in enumerate(pool.imap(render, range(NFRAMES), chunksize=2)):
            ff.stdin.write(buf)
            if k % 90 == 0:
                print(f"reel {n}: frame {k}/{NFRAMES}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
