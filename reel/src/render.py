"""Renders the 15.0 s, 1080x1920, 30 fps Yutoriba reel (video only) to build/video.mp4.

Shots
  A 0.00-6.25   wide: slow downward drift from the cumulus to the coffee stand
  B 6.25-12.55  close-up of the counter: cup, steam, the Bible opened by a hand,
                then a slow tilt up / pull back as the steam rises into the cloud
  C 12.55-15.00 wide again, nearly still, brand card
Transitions come from objects in the scene: the banner cloth crosses the lens (A->B),
foreground grass passes the lens (B->C).
"""
import math
import random
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import *  # noqa

G_OY = 2080
BAN_X, BAN_Y = 944, 2296

T_AB = 6.25
T_BC = 12.55

# ------------------------------------------------------------------ text spec
# (text, size, bold, indent_chars)
TEXT = [
    dict(lines=[("毎日、急いでばかりいない？", 58, True, 0)],
         top=430, t_in=[0.5], t_out=(2.75, 3.15)),
    dict(lines=[("少し立ち止まると、", 56, True, 0), ("見えてくるものがある。", 56, True, 0)],
         top=600, t_in=[3.3, 3.95], t_out=(5.55, 5.9)),
    dict(lines=[("「わたしは道であり、", 54, True, 0), ("真理であり、", 54, True, 1),
                ("いのちなのです。」", 54, True, 1), ("ヨハネの福音書 14:6", 32, True, 0)],
         top=470, t_in=[6.7, 6.95, 7.2, 7.75], t_out=(9.3, 9.65), quote=True),
    dict(lines=[("人生について、", 54, True, 0), ("聖書と一緒に考えてみませんか。", 54, True, 0)],
         top=560, t_in=[9.85, 10.3], t_out=(12.05, 12.4)),
    dict(lines=[("ゆっくり考える場所。", 46, True, 0), ("ゆとりば", 118, True, 0),
                ("まずは、ヨハネの福音書から。", 36, True, 0)],
         top=500, t_in=[12.85, 13.3, 13.85], t_out=None, brand=True),
]
TEXT_CX = 520  # slightly left of centre: clear of the right-hand Reels buttons


def make_line_img(text, size, bold, track=0.06):
    ss = 2
    f = ImageFont.truetype(FONT_B if bold else FONT_R, size * ss)
    adv = [f.getlength(ch) + track * size * ss for ch in text]
    wtot = int(sum(adv) - track * size * ss) + 4 * ss
    pad = 60 * ss
    m = Image.new("L", (wtot + 2 * pad, int(size * 1.6 * ss) + 2 * pad), 0)
    d = ImageDraw.Draw(m)
    x = pad
    for ch, a in zip(text, adv):
        d.text((x, pad + size * 0.8 * ss), ch, font=f, fill=255, anchor="lm")
        x += a
    m = m.resize((m.width // ss, m.height // ss), Image.LANCZOS)
    A = np.asarray(m).astype(np.float32) / 255
    # ink-on-paper: slightly uneven density
    n = fnoise(A.shape[1], A.shape[0], 6, 2, seed=len(text) * 7 + size)
    A_ink = A * (0.86 + 0.14 * n)
    sh = np.asarray(Image.fromarray((A * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    sh = np.roll(np.roll(sh, 2, 0), 1, 1)
    halo = np.asarray(Image.fromarray((A * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(20))).astype(np.float32) / 255
    halo = np.clip(halo * 2.8, 0, 1)
    # composite: halo (translucent cool charcoal) < shadow < ivory ink
    ivory = np.array((251, 246, 231), np.float32)
    shadow_c = np.array((36, 34, 34), np.float32)
    halo_c = np.array((34, 46, 60), np.float32)
    a_h = halo * 0.46
    a_s = sh * 0.75
    a_t = A_ink
    out_a = a_t + a_s * (1 - a_t)
    out_c = (ivory * a_t[..., None] + shadow_c * (a_s * (1 - a_t))[..., None]) / np.maximum(out_a[..., None], 1e-4)
    out_a2 = out_a + a_h * (1 - out_a)
    out_c = (out_c * out_a[..., None] + halo_c * (a_h * (1 - out_a))[..., None]) / np.maximum(out_a2[..., None], 1e-4)
    rgba = np.concatenate([np.clip(out_c, 0, 255), (out_a2 * 255)[..., None]], 2).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA")
    return img, pad, int(sum(adv) - track * size * ss) // ss


def build_text():
    blocks = []
    for b in TEXT:
        lines = []
        y = b["top"]
        imgs = [make_line_img(t, s, bo) for (t, s, bo, ind) in b["lines"]]
        widths = [w for (_, _, w) in imgs]
        sizes = [s for (_, s, _, _) in b["lines"]]
        if b.get("quote"):
            x_left = TEXT_CX - max(widths[:3]) / 2 - sizes[0] * 0.5
        for i, ((img, pad, w), (t, s, bo, ind)) in enumerate(zip(imgs, b["lines"])):
            if b.get("quote") and i < 3:
                x = x_left + ind * s
            elif b.get("quote"):
                x = x_left + max(widths[:3]) - w + sizes[0] * 0.5  # reference right-aligned under the quote
                y += s * 0.5
            else:
                x = TEXT_CX - w / 2
            lines.append(dict(img=img, x=int(x - pad), y=int(y - pad), w=w, pad=pad, t0=b["t_in"][i]))
            gap = 1.75
            if b.get("brand"):
                gap = {0: 1.9, 1: 1.35, 2: 1.6}[i]
                if i == 0:
                    y += s * gap
                    continue
            y += s * gap
        x0 = min(l["x"] + l["pad"] for l in lines) - 70
        x1 = max(l["x"] + l["pad"] + l["w"] for l in lines) + 70
        y0 = min(l["y"] + l["pad"] for l in lines) - 50
        y1 = max(l["y"] + l["img"].height - l["pad"] for l in lines) + 30
        bw, bh = x1 - x0 + 240, y1 - y0 + 240
        m = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(m).rounded_rectangle([120, 120, bw - 120, bh - 120], radius=80, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(55))
        back = Image.new("RGBA", (bw, bh), (30, 44, 62, 0))
        back.putalpha(m.point(lambda v: int(v * 0.36)))
        blocks.append(dict(lines=lines, t_out=b["t_out"], back=back, bx=x0 - 120, by=y0 - 120))
    return blocks


def text_layer(frame, t, blocks):
    for b in blocks:
        fo = 1.0
        if b["t_out"]:
            o0, o1 = b["t_out"]
            if t >= o1:
                continue
            fo = 1 - smooth((t - o0) / (o1 - o0))
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
            dur = 0.85
            p = clamp(dt / dur)
            img = ln["img"]
            a = np.asarray(img).astype(np.float32)
            xs = np.arange(img.width, dtype=np.float32) - ln["pad"]
            feather = 140.0
            front = p * (ln["w"] + feather + 40) - 20
            ramp = np.clip((front - xs) / feather, 0, 1)
            op = smooth(dt / 1.0) * fo
            a[..., 3] *= ramp[None, :] * op
            frame.alpha_composite(Image.fromarray(a.astype(np.uint8), "RGBA"), (ln["x"], ln["y"]))


# ------------------------------------------------------------------ resources
R = {}


def init():
    R["skyA"] = Image.open(f"{BUILD}/A_sky.png").convert("RGB")
    R["ground"] = Image.open(f"{BUILD}/A_ground.png").convert("RGBA")
    R["banner"] = np.asarray(Image.open(f"{BUILD}/banner.png").convert("RGBA")).astype(np.float32)
    R["bgB"] = Image.open(f"{BUILD}/B_bg.png").convert("RGB")
    R["standB"] = Image.open(f"{BUILD}/B_stand.png").convert("RGBA")
    R["text"] = build_text()
    # paper texture + gentle vignette (static, like the paper the drawing sits on)
    n1 = fnoise(W, H, 1.5, 2, 101)
    n2 = fnoise(W, H, 70, 4, 102)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.07 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    R["paper"] = ((0.975 + 0.035 * n1 + 0.025 * (n2 - 0.5)) * v)[..., None].astype(np.float32)
    rng = random.Random(5)
    # foreground screen-space grass
    fg = []
    for i in range(170):
        x = rng.uniform(-60, W + 60)
        e = min(1.0, abs(x - 520) / 560) ** 1.6
        h = lerp(70, 380, e) * rng.uniform(0.55, 1.1)
        fg.append(dict(x=x, h=h, w=rng.uniform(7, 15), bend=rng.uniform(-50, 50), ph=rng.random() * 6.28,
                       amp=rng.uniform(10, 26), col=lerpc(GRASS_DARK, (122, 150, 76), rng.random() * 0.8)))
    fg.sort(key=lambda b: b["h"])
    R["fg"] = fg
    # mid-ground animated blades around the stand (world A coords)
    mg = []
    for i in range(320):
        x = rng.uniform(60, 1180)
        y = rng.uniform(2722, 2800)
        mg.append(dict(x=x, y=y, h=rng.uniform(16, 48) * (0.7 + (y - 2722) / 160), ph=rng.random() * 6.28,
                       col=lerpc(GRASS_NEAR, GRASS_LIGHT if rng.random() < 0.5 else GRASS_DARK, rng.uniform(0.2, 0.7))))
    R["mg"] = mg
    R["cloth"] = make_cloth()
    R["curtain"] = make_curtain()
    R["cover"], R["pageR"], R["pageL"] = make_book_textures()


def make_cloth():
    """Out-of-focus banner cloth that crosses the lens (A->B)."""
    w, h = 1320, H
    x = np.arange(w, dtype=np.float32)
    shade = 0.9 + 0.07 * np.sin(x / 95) + 0.04 * np.sin(x / 37 + 1)
    col = np.array((236, 228, 205), np.float32)[None, None, :] * shade[None, :, None]
    col = np.repeat(col, h, 0)
    hem = (np.arange(h) > h - 260)[:, None]
    col = np.where(hem[..., None], np.array((70, 96, 116), np.float32) * shade[None, :, None], col)
    edge = np.clip(np.minimum(x, w - 1 - x) / 220, 0, 1)
    a = np.repeat(edge[None, :], h, 0)
    img = Image.fromarray(np.concatenate([col, (a * 255)[..., None]], 2).astype(np.uint8), "RGBA")
    return img.filter(ImageFilter.GaussianBlur(6))


def make_curtain():
    """Out-of-focus foreground grass passing the lens (B->C)."""
    w, h = 1900, H
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(8)
    for i in range(240):
        cx = rng.gauss(w / 2, w / 4.5)
        bw = rng.uniform(26, 70)
        lean = rng.uniform(-260, 260)
        col = lerpc((52, 78, 40), (110, 140, 70), rng.random())
        d.polygon([(cx - bw / 2, h + 40), (cx + bw / 2, h + 40), (cx + lean + 4, rng.uniform(-200, h * 0.35)),
                   (cx + lean - 4, rng.uniform(-200, h * 0.35))], fill=col + (255,))
    core = Image.new("L", (w, h), 0)
    ImageDraw.Draw(core).rectangle([w * 0.47, 0, w * 0.53, h], fill=255)
    core = core.filter(ImageFilter.GaussianBlur(60))
    a = np.maximum(np.asarray(img)[..., 3], np.asarray(core)).astype(np.uint8)
    arr = np.asarray(img).copy()
    fill = np.array((70, 98, 52), np.uint8)
    empty = arr[..., 3] == 0
    arr[empty, :3] = fill
    arr[..., 3] = a
    return Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(10))


def make_book_textures():
    tw, th = 480, 600
    # cover: cloth navy, worn corners, blind border, small faded-gold 聖書
    cov = Image.new("RGBA", (tw, th), NAVY + (255,))
    d = ImageDraw.Draw(cov)
    n = fnoise(tw, th, 30, 3, 55)
    arr = np.asarray(cov).astype(np.float32)
    arr[..., :3] *= (0.9 + 0.16 * n)[..., None]
    cov = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(cov)
    d.rectangle([22, 22, tw - 22, th - 22], outline=(70, 84, 104), width=3)
    f = ImageFont.truetype(FONT_B, 64)
    d.text((tw / 2, th * 0.36), "聖書", font=f, fill=(186, 162, 112), anchor="mm")
    for (cx, cy) in ((0, 0), (tw, 0), (0, th), (tw, th)):
        d.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(84, 92, 104))
    d.rectangle([0, 0, tw - 1, th - 1], outline=INK, width=5)
    # pages: ivory with soft, unreadable grey lines (kept deliberately understated)
    def page(left):
        pg = Image.new("RGBA", (tw, th), (244, 238, 220, 255))
        dd = ImageDraw.Draw(pg)
        for col in range(2):
            x0 = 50 + col * 200 if not left else 40 + col * 200
            for k in range(26):
                y = 60 + k * 19
                L = 170 if k % 9 != 8 else rng.uniform(40, 120)
                dd.line([(x0, y), (x0 + L, y)], fill=(176, 170, 156, 255), width=5)
        g = np.asarray(pg).astype(np.float32)
        xs = np.arange(tw, dtype=np.float32)
        gut = np.exp(-((tw - xs) if left else xs) / 70)
        g[..., :3] *= (1 - 0.18 * gut)[None, :, None]
        pg = Image.fromarray(g.astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(2.2))
        ImageDraw.Draw(pg).rectangle([0, 0, tw - 1, th - 1], outline=INK, width=4)
        return pg
    rng = random.Random(3)
    return cov, page(False), page(True)


# ------------------------------------------------------------------ cameras
class Cam:
    def __init__(self, top, z, xc=620.0, left=None):
        self.top, self.z = top, z
        self.left = left if left is not None else xc - (W / 2) / z

    def ws(self, x, y):
        return ((x - self.left) * self.z, (y - self.top) * self.z)


def cam_A(t):
    T = T_AB
    u = 0.22 * clamp(t / T) + 0.78 * ease_io(t / T)
    return Cam(lerp(200, 1212, u), lerp(1.0, 1.08, u), lerp(612, 628, u)), 1212


def cam_C(t):
    u = clamp((t - T_BC) / (DUR - T_BC))
    return Cam(lerp(1104, 1112, u), lerp(1.03, 1.045, u), 620), 1104


FOCUS_B = (560.0, 2060.0)


def cam_B(t):
    z0, top0 = 1.0, 690.0
    sx, sy = (FOCUS_B[0] - (620 - W / 2)) * z0, (FOCUS_B[1] - top0) * z0
    if t < 9.5:
        u = ease_io((t - T_AB) / (9.5 - T_AB)) * 0.9 + 0.1 * clamp((t - T_AB) / (9.5 - T_AB))
        z = lerp(1.0, 1.08, u)
        return Cam(FOCUS_B[1] - sy / z, z, left=FOCUS_B[0] - sx / z), top0
    c1 = cam_B(9.4999)[0]
    u = ease_io((t - 9.5) / (T_BC + 0.3 - 9.5))
    z = lerp(c1.z, 1.0, u)
    top = lerp(c1.top, 300, u)
    xc1 = c1.left + (W / 2) / c1.z
    return Cam(top, z, lerp(xc1, 620, u)), top0


def place(img, origin, cam, ref_top, p=1.0, dx=0.0):
    eff_top = ref_top + (cam.top - ref_top) * p
    eff_left = cam.left - dx
    a = K / cam.z
    data = (a, 0, (eff_left - origin[0]) * K, 0, a, (eff_top - origin[1]) * K)
    return img.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC)


# ------------------------------------------------------------------ animated bits
def warp_banner(t, strength=1.0):
    b = R["banner"]
    h, w = b.shape[:2]
    ys = np.arange(h, dtype=np.float32)
    yn = ys / h
    dx = strength * (9 * yn ** 1.4 * np.sin(2 * math.pi * 0.32 * t + ys * 0.016)
                     + 4 * yn * np.sin(2 * math.pi * 0.71 * t + 1.3)) * K
    xs = np.arange(w, dtype=np.float32)[None, :] - dx[:, None]
    x0 = np.clip(np.floor(xs).astype(np.int32), 0, w - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    fr = (xs - np.floor(xs))[..., None]
    rows = np.arange(h)[:, None]
    out = b[rows, x0] * (1 - fr) + b[rows, x1] * fr
    valid = ((xs >= 0) & (xs <= w - 1))[..., None]
    out = out * valid
    shade = 1 - 0.07 * np.sin(2 * math.pi * 0.32 * t + ys * 0.016 + 1.2)[:, None] * yn[:, None]
    out[..., :3] *= shade[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def gust(t):
    return 0.6 + 0.4 * math.sin(0.55 * t + 0.4) * math.sin(0.23 * t + 1.1)


def draw_blade(d, x, yb, h, w, bend, col, outline=True, ss=2):
    pts_l, pts_r = [], []
    for i in range(9):
        s = i / 8
        cx = x + bend * s ** 1.8
        cy = yb - h * s
        hw = w / 2 * (1 - s) ** 0.9
        pts_l.append(((cx - hw) * ss, cy * ss))
        pts_r.append(((cx + hw) * ss, cy * ss))
    poly = pts_l + pts_r[::-1]
    d.polygon(poly, fill=col + (255,), outline=INK + (255,) if outline else None, width=2 if outline else 0)


def overlay_wide(t, cam, calm=1.0, yshift=0.0, birds=True):
    ss = 2
    ov = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    g = gust(t) * calm
    # mid-ground blades at the stand's feet
    for b in R["mg"]:
        X, Y = cam.ws(b["x"], b["y"])
        if X < -40 or X > W + 40 or Y < 0 or Y > H + 60:
            continue
        sway = (4 + 5 * g) * math.sin(2.1 * t + b["ph"] + b["x"] * 0.01)
        hh = b["h"] * cam.z
        d.line([(X * ss, Y * ss), ((X + sway * 0.4) * ss, (Y - hh * 0.5) * ss), ((X + sway) * ss, (Y - hh) * ss)],
               fill=b["col"] + (255,), width=3, joint="curve")
    # tiny steam from the cup on the counter
    cx, cy = cam.ws(705, 2472)
    for k in range(3):
        pts = []
        for i in range(10):
            s = i / 9
            pts.append(((cx + (k - 1) * 4 * cam.z + 3 * math.sin(6 * s - 2.2 * t + k)) * ss, (cy - s * 34 * cam.z) * ss))
        d.line(pts, fill=(250, 246, 236, 110), width=3)
    # birds, far away
    if birds:
        for (t0, t1, x0, y0, x1, y1, sz) in ((0.7, 6.0, 1140, 470, -40, 400, 8), (1.4, 6.4, 1180, 540, 40, 500, 6.5)):
            if t0 < t < t1:
                u = (t - t0) / (t1 - t0)
                bx, by = lerp(x0, x1, u), lerp(y0, y1, u) + 6 * math.sin(u * 7)
                f = math.sin(2 * math.pi * 2.6 * t + x0)
                for sgn in (-1, 1):
                    d.line([(bx * ss, by * ss), ((bx + sgn * sz * 0.9) * ss, (by - sz * 0.45 * f) * ss),
                            ((bx + sgn * sz * 1.8) * ss, (by - sz * 0.1 * f + 2) * ss)],
                           fill=(44, 56, 70, 230), width=3, joint="curve")
    # foreground grass framing the bottom edge
    for b in R["fg"]:
        sway = (b["amp"] * (0.5 + 0.8 * g)) * math.sin(1.25 * t + b["ph"] + b["x"] * 0.004) * calm
        draw_blade(d, b["x"], H + 30 + yshift + (1 - b["h"] / 380) * 30, b["h"], b["w"], b["bend"] + sway, b["col"])
    return ov.resize((W, H), Image.LANCZOS)


def shot_wide(t, cam, ref_top, calm=1.0, yshift=0.0, birds=True):
    frame = place(R["skyA"], (0, 0), cam, ref_top, p=0.86, dx=-0.9 * t).convert("RGBA")
    g = R["ground"].copy()
    g.alpha_composite(warp_banner(t, calm), (int(BAN_X * K), int(BAN_Y * K)))
    frame.alpha_composite(place(g, (0, G_OY), cam, ref_top, p=1.0))
    frame.alpha_composite(overlay_wide(t, cam, calm, yshift, birds))
    return frame


# ---------------------------------------------------------------- book & hand
def persp_coeffs(dst, src):
    """Coefficients mapping output (dst) points to input (src) points for Image.PERSPECTIVE."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, np.float64), np.array(B, np.float64)).tolist()


def paste_quad(canvas, tex, quad):
    xs = [p[0] for p in quad]; ys = [p[1] for p in quad]
    x0, y0 = int(math.floor(min(xs))) - 2, int(math.floor(min(ys))) - 2
    x1, y1 = int(math.ceil(max(xs))) + 2, int(math.ceil(max(ys))) + 2
    if x1 - x0 < 3 or y1 - y0 < 3:
        return
    area = 0.5 * abs(sum(quad[i][0] * quad[(i + 1) % 4][1] - quad[(i + 1) % 4][0] * quad[i][1] for i in range(4)))
    if area < 40:
        return
    src = [(0, 0), (tex.width, 0), (tex.width, tex.height), (0, tex.height)]
    dst = [(x - x0, y - y0) for x, y in quad]
    try:
        c = persp_coeffs(dst, src)
    except np.linalg.LinAlgError:
        return
    patch = tex.transform((x1 - x0, y1 - y0), Image.PERSPECTIVE, c, resample=Image.BICUBIC)
    m = Image.new("L", patch.size, 0)
    ImageDraw.Draw(m).polygon(dst, fill=255)
    pa = np.asarray(patch).copy()
    pa[..., 3] = np.minimum(pa[..., 3], np.asarray(m))
    canvas.alpha_composite(Image.fromarray(pa, "RGBA"), (x0, y0))


BOOK = dict(bx=335.0, by=2190.0, W=240.0, D=300.0, T=30.0)


def book_theta(t):
    return math.pi * ease_io((t - 6.85) / (7.85 - 6.85))


def draw_book_hand(canvas, t, cam, ss=2):
    bx, by, Wb, D, T = BOOK["bx"], BOOK["by"], BOOK["W"], BOOK["D"], BOOK["T"]
    th = book_theta(t)
    h2 = T / 2

    def P(u, v, h):
        X, Y = cam.ws(bx + u + 0.15 * v, by - 0.5 * v - h)
        return (X * ss, Y * ss)

    def rot(u, hl):
        return u * math.cos(th) - hl * math.sin(th), h2 + u * math.sin(th) + hl * math.cos(th)

    d = ImageDraw.Draw(canvas)
    lw = max(2, int(2.2 * cam.z))
    # soft contact shadow
    sh = [P(-Wb * smooth(th / math.pi) - 6, -6, 0), P(Wb + 8, -6, 0), P(Wb + 8, D + 4, 0), P(-Wb * smooth(th / math.pi) - 6, D + 4, 0)]
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 10 * ss, y + 8 * ss) for x, y in sh], fill=(60, 40, 24, 70))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(10 * ss)))
    # lower half block: front page-edge face + back cover sliver
    d.polygon([P(0, 0, 0), P(Wb, 0, 0), P(Wb, 0, h2), P(0, 0, h2)], fill=(236, 228, 206, 255), outline=INK + (255,), width=lw)
    for k in range(1, 5):
        hh = h2 * k / 5
        d.line([P(3, 0, hh), P(Wb - 3, 0, hh)], fill=(196, 186, 162, 255), width=1)
    d.line([P(0, 0, 0.5), P(Wb, 0, 0.5)], fill=NAVY + (255,), width=lw + 2)
    d.polygon([P(Wb, 0, 0), P(Wb, D, 0), P(Wb, D, h2), P(Wb, 0, h2)], fill=(226, 218, 196, 255), outline=INK + (255,), width=lw)
    # right page (top of lower block)
    paste_quad(canvas, R["pageR"], [P(0, D, h2), P(Wb, D, h2), P(Wb, 0, h2), P(0, 0, h2)])
    # left stack appears as the upper half lands
    # flipping upper half (pages + front cover), rotated about the spine
    cover_up = math.cos(th) > -0.02
    tex = R["cover"] if cover_up else R["pageL"]
    hl_face = h2 if cover_up else 0.0
    fu, fh = rot(Wb, hl_face)
    su, sh_ = rot(0, hl_face)
    if cover_up:
        quad = [P(su, D, sh_), P(fu, D, fh), P(fu, 0, fh), P(su, 0, sh_)]
    else:
        quad = [P(fu, D, fh), P(su, D, sh_), P(su, 0, sh_), P(fu, 0, fh)]
    # free-edge band (page block thickness)
    e0u, e0h = rot(Wb, 0)
    e1u, e1h = rot(Wb, h2)
    d.polygon([P(e0u, 0, e0h), P(e0u, D, e0h), P(e1u, D, e1h), P(e1u, 0, e1h)], fill=(232, 224, 200, 255), outline=INK + (255,), width=lw)
    paste_quad(canvas, tex, quad)
    # near cross-section of the flipping half
    cs = [rot(0, 0), rot(Wb, 0), rot(Wb, h2), rot(0, h2)]
    d.polygon([P(u, 0, h) for u, h in cs], fill=(236, 228, 206, 255), outline=INK + (255,), width=lw)
    cu, ch = rot(0, h2)
    fu2, fh2 = rot(Wb, h2)
    d.line([P(cu, 0, ch), P(fu2, 0, fh2)], fill=NAVY + (255,), width=lw + 2)
    # ribbon bookmark + a page that lifts in the breeze, once open
    if th > math.pi * 0.92:
        d.line([P(6, D * 0.55, h2 + 0.5), P(18, D * 0.2, h2 + 0.5), P(26, -4, h2 - 2), P(30, -6, 2)],
               fill=(150, 66, 56, 255), width=max(3, int(4 * cam.z)), joint="curve")
        lift = (5 + 4 * math.sin(2 * math.pi * 0.45 * t)) * clamp((t - 7.9) / 0.4)
        if lift > 0.5:
            d.polygon([P(Wb, 0, h2), P(Wb - 46, 0, h2 + lift * 0.6), P(Wb - 4, 44, h2 + lift)],
                      fill=(246, 240, 224, 255), outline=INK + (255,), width=max(1, lw - 1))
    # the hand
    hand_pose(canvas, t, P, rot, ss, cam)


HAND_IN, HAND_REL, HAND_OUT = (6.3, 6.85), 7.32, 7.95


def hand_pose(canvas, t, P, rot, ss, cam):
    if t < HAND_IN[0] or t > HAND_OUT:
        return
    Wb, D, h2 = BOOK["W"], BOOK["D"], BOOK["T"] / 2
    base_dir = math.atan2(-0.78, -0.62)
    th = book_theta(min(t, HAND_REL))
    u, hh = rot(Wb, h2)
    cx, cy = P(u + 4, 46, hh)
    ang = base_dir + 0.35 * th
    L = 900 * ss
    if t < HAND_IN[1]:
        e = 1 - ease_io((t - HAND_IN[0]) / (HAND_IN[1] - HAND_IN[0]))
        cx -= math.cos(ang) * L * e
        cy -= math.sin(ang) * L * e
    elif t > HAND_REL:
        e = ease_io((t - HAND_REL) / (HAND_OUT - HAND_REL)) ** 1.3
        ang2 = ang + 0.25 * e
        cx -= math.cos(ang2) * L * e
        cy -= math.sin(ang2) * L * e + 120 * ss * e
        ang = ang2
    draw_hand(canvas, cx, cy, ang, cam.z * ss)


def draw_hand(canvas, cx, cy, ang, sc):
    d = ImageDraw.Draw(canvas)
    ca, sa = math.cos(ang), math.sin(ang)

    def T(pts):
        return [(cx + (x * ca - y * sa) * sc, cy + (x * sa + y * ca) * sc) for x, y in pts]

    def capsule(x0, y0, x1, y1, r, n=10):
        a = math.atan2(y1 - y0, x1 - x0)
        pts = []
        for i in range(n + 1):
            q = a + math.pi / 2 + math.pi * i / n
            pts.append((x0 + r * math.cos(q), y0 + r * math.sin(q)))
        for i in range(n + 1):
            q = a - math.pi / 2 + math.pi * i / n
            pts.append((x1 + r * math.cos(q), y1 + r * math.sin(q)))
        return pts

    lw = max(2, int(1.0 * sc))
    skin, skin_d = SKIN + (255,), (206, 168, 138, 255)
    sleeve = [(-520, -46), (-150, -44), (-148, 48), (-520, 50)]
    d.polygon(T(sleeve), fill=SLEEVE + (255,), outline=INK + (255,), width=lw)
    d.line(T([(-170, -44), (-168, 47)]), fill=(60, 76, 96, 255), width=lw)
    d.polygon(T(capsule(-118, 30, -50, 40, 9)), fill=skin_d, outline=INK + (255,), width=lw)  # thumb (below)
    palm = [(-156, -34), (-70, -32), (-56, -6), (-58, 30), (-156, 36)]
    d.polygon(T(palm), fill=skin, outline=INK + (255,), width=lw)
    for (yo, ln, r) in ((-24, -16, 7.2), (-8, -2, 7.8), (8, -6, 7.6), (23, -20, 6.6)):
        d.polygon(T(capsule(-74, yo, ln, yo * 0.85, r)), fill=skin, outline=INK + (255,), width=lw)
        d.line(T([(ln - 18, yo * 0.85 - r * 0.6), (ln - 16, yo * 0.85 + r * 0.6)]), fill=(150, 116, 92, 255), width=max(1, lw - 1))
    d.line(T([(-120, -10), (-80, -4)]), fill=(176, 140, 112, 255), width=max(1, lw - 1))


def steam_B(t, cam, frame_rgba):
    """Soft rising steam; after 9.5 s it lengthens and drifts up into the cloud."""
    lo = 2
    w, h = W // lo, H // lo
    layer = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(layer)
    cx, cy = 760.0, 1952.0
    grow = ease_io((t - 9.4) / 2.6)
    Hs = lerp(300, 1500, grow)
    for k in range(5):
        ph = k * 1.7
        pts = []
        for i in range(40):
            s = i / 39
            x = cx + (k - 2) * 18 + (26 + 60 * grow) * s ** 1.1 * math.sin(5.5 * s - 1.3 * t + ph) + 40 * grow * s
            y = cy - s * Hs - 30 * (t % 3.0) * 0  # keep anchored to the cup
            X, Y = cam.ws(x, y)
            pts.append((X / lo, Y / lo, s))
        for i in range(len(pts) - 1):
            s = pts[i][2]
            a = (1 - s) ** 1.3 * smooth(s / 0.08) * (150 - 40 * grow)
            wdt = lerp(5, 16 + 30 * grow, s) * cam.z / lo * 1.6
            d.line([pts[i][:2], pts[i + 1][:2]], fill=int(a), width=max(1, int(wdt)))
    # larger plume puffs that rise toward the cloud and dissolve into it
    if t > 9.4:
        for k in range(7):
            age = t - 9.4 - k * 0.32
            if age <= 0:
                continue
            y = cy - 120 - age * 260
            x = cx + 30 * math.sin(age * 1.3 + k) + 30 * age
            r = 30 + age * 60
            a = 90 * smooth(age / 0.5) * clamp(1 - age / 2.6)
            X, Y = cam.ws(x, y)
            d.ellipse([(X - r) / lo, (Y - r * 0.8) / lo, (X + r) / lo, (Y + r * 0.8) / lo], fill=int(a))
    layer = layer.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BICUBIC)
    st = Image.new("RGBA", (W, H), (250, 246, 236, 0))
    st.putalpha(layer)
    frame_rgba.alpha_composite(st)


def sunlight_B(arr, t, cam):
    """Soft amber light that slides slowly across the aged wood of the counter."""
    lo = 4
    w, h = W // lo, H // lo
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32) * lo
    wx = xx / cam.z + cam.left
    wy = yy / cam.z + cam.top
    c = 120 + 95 * (t - T_AB)
    q = (wx - c) * 0.86 + (wy - 2000) * 0.5
    band = np.exp(-(q / 170) ** 2)
    vert = np.clip((wy - 1830) / 60, 0, 1) * np.clip((2300 - wy) / 40, 0, 1)
    m = (band * vert).astype(np.float32)
    m = np.asarray(Image.fromarray(m, "F").resize((W, H), Image.BILINEAR))
    arr[..., :3] += m[..., None] * np.array((34, 22, 6), np.float32)


def shot_B(t):
    cam, ref = cam_B(t)
    frame = place(R["bgB"], (0, 0), cam, ref, p=0.75, dx=-0.9 * t).convert("RGBA")
    frame.alpha_composite(place(R["standB"], (0, 0), cam, ref, p=1.0))
    ss = 2
    ov = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    draw_book_hand(ov, t, cam, ss)
    frame.alpha_composite(ov.resize((W, H), Image.LANCZOS))
    arr = np.asarray(frame).astype(np.float32)
    sunlight_B(arr, t, cam)
    frame = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    # glints on the glass jars
    d = ImageDraw.Draw(frame)
    for (gx, gy, ph) in ((912, 1668, 0.0), (1042, 1716, 1.9)):
        a = max(0.0, math.sin(2 * math.pi * 0.35 * t + ph)) ** 3
        if a > 0.02:
            X, Y = cam.ws(gx, gy)
            r = 5 * cam.z
            d.ellipse([X - r, Y - r * 2.2, X + r, Y + r * 2.2], fill=(255, 252, 240, int(170 * a)))
    steam_B(t, cam, frame)
    return frame


# ------------------------------------------------------------------ frame
def render(i):
    t = i / FPS
    if t < T_AB:
        cam, ref = cam_A(t)
        frame = shot_wide(t, cam, ref, 1.0, -(cam.top - 200) * 0.10, True)
    elif t < T_BC:
        frame = shot_B(t)
    else:
        cam, ref = cam_C(t)
        calm = lerp(1.0, 0.55, smooth((t - T_BC) / 1.2))
        frame = shot_wide(t, cam, ref, calm, -100, False)
    # soften the cut under the passing grass with a short dissolve
    if 12.35 <= t < T_BC:
        cam, ref = cam_C(t)
        other = shot_wide(t, cam, ref, 1.0, -100, False)
        frame = Image.blend(frame, other, smooth((t - 12.35) / 0.2))
    # transitions made of things in the scene
    if 5.75 <= t <= 6.8:
        x = 540 + (T_AB - t) / 0.5 * 1150
        frame.alpha_composite(R["cloth"], (int(x - R["cloth"].width / 2), 0))
    if 12.1 <= t <= 13.05:
        x = 540 + (t - T_BC) / 0.38 * 1250
        frame.alpha_composite(R["curtain"], (int(x - R["curtain"].width / 2), 0))
    text_layer(frame, t, R["text"])
    arr = np.asarray(frame.convert("RGB")).astype(np.float32)
    arr = arr * R["paper"]
    arr = arr * 0.965 + 6.0
    arr[..., 0] *= 1.008
    arr[..., 2] *= 0.992
    return np.clip(arr, 0, 255).astype(np.uint8).tobytes()


def main():
    out = f"{BUILD}/video.mp4"
    frames = list(range(NFRAMES))
    if len(sys.argv) > 1 and sys.argv[1] == "stills":
        init()
        for tt in [float(x) for x in sys.argv[2:]]:
            Image.frombytes("RGB", (W, H), render(int(round(tt * FPS)))).save(f"{BUILD}/still_{tt:05.2f}.png")
        return
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-tune", "animation", "-movflags", "+faststart", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(4, initializer=init) as pool:
        for k, buf in enumerate(pool.imap(render, frames, chunksize=2)):
            ff.stdin.write(buf)
            if k % 30 == 0:
                print(f"frame {k}/{NFRAMES}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("wrote", out)


if __name__ == "__main__":
    main()
