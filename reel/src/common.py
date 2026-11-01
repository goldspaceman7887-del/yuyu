"""Shared palette, noise and hand-drawn ink helpers for the Yutoriba reel."""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
FONT_R = os.path.join(ROOT, "fonts", "ZenOldMincho-Regular.ttf")
FONT_B = os.path.join(ROOT, "fonts", "ZenOldMincho-Bold.ttf")
os.makedirs(BUILD, exist_ok=True)

W, H = 1080, 1920
FPS = 30
DUR = 15.0
NFRAMES = int(round(FPS * DUR))

K = 1.5   # storage scale of world layers (px per world unit)
S = 3.0   # drawing (supersample) scale; layers are drawn at S then halved to K

# ---------------------------------------------------------------- palette
INK = (62, 49, 40)
INK_SOFT = (92, 76, 62)
SKY_TOP = (50, 104, 156)
SKY_MID = (66, 124, 176)
SKY_HOR = (132, 174, 204)
CLOUD = [  # dark -> light cel tones
    (128, 154, 180),
    (163, 183, 200),
    (203, 211, 212),
    (233, 227, 206),
    (246, 240, 222),
]
RED = (178, 86, 64)
RED_LIGHT = (196, 112, 84)
RED_DARK = (140, 64, 50)
WOOD = (196, 170, 128)
WOOD_LIGHT = (218, 198, 158)
WOOD_DARK = (92, 70, 52)
WOOD_MID = (150, 118, 84)
THATCH = (206, 186, 146)
THATCH_LIGHT = (224, 208, 172)
GRASS_FAR = (150, 168, 110)
GRASS_NEAR = (96, 126, 64)
GRASS_DARK = (66, 92, 48)
GRASS_LIGHT = (170, 186, 112)
MOSS = (110, 136, 70)
TEAL = (78, 126, 132)
TEAL_LIGHT = (122, 164, 164)
TERRACOTTA = (176, 104, 74)
TERRA_DARK = (138, 76, 54)
PAPER = (240, 233, 212)
IVORY = (247, 241, 224)
NAVY = (48, 60, 78)
AMBER = (236, 188, 120)
SKIN = (230, 196, 166)
SLEEVE = (84, 104, 128)


def lerp(a, b, t):
    return a + (b - a) * t


def lerpc(c0, c1, t):
    return tuple(int(round(lerp(a, b, t))) for a, b in zip(c0, c1))


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_io(t):
    t = clamp(t)
    return 0.5 - 0.5 * math.cos(math.pi * t)


def fnoise(w, h, scale, octaves=4, seed=0, persistence=0.5):
    """Fractal value noise in [0,1], shape (h, w)."""
    rng = np.random.default_rng(seed)
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        gw = max(2, int(w / scale) + 2)
        gh = max(2, int(h / scale) + 2)
        grid = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(grid, "F").resize((w, h), Image.BICUBIC)
        total += amp * np.asarray(im)
        norm += amp
        amp *= persistence
        scale = max(1.0, scale / 2)
    total /= norm
    lo, hi = np.percentile(total, 1), np.percentile(total, 99)
    return np.clip((total - lo) / (hi - lo + 1e-6), 0, 1)


class Pen:
    """Draws in world coordinates onto a supersampled RGBA canvas with a wobbly ink hand."""

    def __init__(self, size, scale, origin=(0.0, 0.0), seed=1):
        # premultiplied colour canvas + coverage mask, so translucent ink composites correctly
        self.rgb = Image.new("RGB", size, (0, 0, 0))
        self.m = Image.new("L", size, 0)
        self.d = ImageDraw.Draw(self.rgb, "RGBA")
        self.dm = ImageDraw.Draw(self.m)
        self.s = scale
        self.ox, self.oy = origin
        self.rng = random.Random(seed)

    def result(self):
        a = np.asarray(self.m).astype(np.float32)[..., None] / 255.0
        c = np.asarray(self.rgb).astype(np.float32)
        c = np.where(a > 0, c / np.maximum(a, 1e-3), 0)
        out = np.concatenate([np.clip(c, 0, 255), a * 255], axis=2).astype(np.uint8)
        return Image.fromarray(out, "RGBA")

    def _mask_poly(self, xy, alpha):
        if alpha >= 250:
            self.dm.polygon(xy, fill=255)
            return
        xs = [p[0] for p in xy]; ys = [p[1] for p in xy]
        x0, y0 = int(max(0, min(xs))), int(max(0, min(ys)))
        x1, y1 = int(min(self.m.width, max(xs) + 2)), int(min(self.m.height, max(ys) + 2))
        if x1 <= x0 or y1 <= y0:
            return
        tmp = Image.new("L", (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(tmp).polygon([(x - x0, y - y0) for x, y in xy], fill=255)
        cur = np.asarray(self.m.crop((x0, y0, x1, y1))).astype(np.float32) / 255
        t = np.asarray(tmp).astype(np.float32) / 255 * (alpha / 255)
        new = cur + t * (1 - cur)
        self.m.paste(Image.fromarray((new * 255).astype(np.uint8)), (x0, y0))

    def P(self, x, y):
        return ((x - self.ox) * self.s, (y - self.oy) * self.s)

    def _wobble(self, pts, wob, step=4.0):
        dense = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0)
            n = max(1, int(L / step))
            for i in range(n):
                t = i / n
                dense.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        dense.append(tuple(pts[-1]))
        if wob <= 0 or len(dense) < 2:
            return dense
        ph = [self.rng.random() * 6.283 for _ in range(3)]
        out, cum = [], 0.0
        for i, (x, y) in enumerate(dense):
            if i:
                cum += math.hypot(x - dense[i - 1][0], y - dense[i - 1][1])
            j0, j1 = max(0, i - 1), min(len(dense) - 1, i + 1)
            dx = dense[j1][0] - dense[j0][0]
            dy = dense[j1][1] - dense[j0][1]
            L = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / L, dx / L
            o = wob * (0.6 * math.sin(cum * 0.045 + ph[0]) + 0.3 * math.sin(cum * 0.12 + ph[1])
                       + 0.15 * math.sin(cum * 0.33 + ph[2]))
            out.append((x + nx * o, y + ny * o))
        return out

    def line(self, pts, color=INK, w=1.3, wob=0.5, taper=False, vary=0.3):
        pts = self._wobble(pts, wob)
        ph = self.rng.random() * 6.283
        n = len(pts)
        for i in range(n - 1):
            ww = w * (1 - vary / 2 + vary * (0.5 + 0.5 * math.sin(i * 0.23 + ph)))
            if taper:
                t = i / max(1, n - 2)
                ww *= 0.35 + 0.65 * math.sin(math.pi * clamp(0.08 + 0.84 * t))
            W_ = max(1.0, ww * self.s)
            a = self.P(*pts[i])
            b = self.P(*pts[i + 1])
            wi = max(1, int(round(W_)))
            self.d.line([a, b], fill=color, width=wi)
            if len(color) == 3 or color[3] >= 250:
                self.dm.line([a, b], fill=255, width=wi)
            r = W_ / 2
            if r > 1.2:
                self.d.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=color)
                if len(color) == 3 or color[3] >= 250:
                    self.dm.ellipse([b[0] - r, b[1] - r, b[0] + r, b[1] + r], fill=255)

    def simple_line(self, pts, color, w=1.0, mask=None):
        xy = [self.P(*p) for p in pts]
        wi = max(1, int(round(w * self.s)))
        self.d.line(xy, fill=color, width=wi)
        a = 255 if len(color) == 3 else color[3]
        if mask or (mask is None and a >= 200):
            self.dm.line(xy, fill=255, width=wi)

    def poly(self, pts, fill=None, outline=INK, w=1.3, wob=0.5):
        if fill is not None:
            xy = [self.P(*p) for p in pts]
            self.d.polygon(xy, fill=fill)
            self._mask_poly(xy, 255 if len(fill) == 3 else fill[3])
        if outline is not None:
            self.line(list(pts) + [pts[0]], outline, w, wob)

    def ellipse(self, box, fill=None, outline=INK, w=1.2, wob=0.3, n=48):
        x0, y0, x1, y1 = box
        cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a))
               for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]
        self.poly(pts, fill, outline, w, wob)

    def arc(self, cx, cy, rx, ry, a0, a1, color=INK, w=1.2, wob=0.2, n=40):
        pts = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]
        self.line(pts, color, w, wob)

    def rect(self, x0, y0, x1, y1, fill=None, outline=INK, w=1.3, wob=0.5):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, outline, w, wob)

    def grain(self, x0, y0, x1, y1, color, n=20, vertical=True, alpha=60, amp=1.2, w=0.6):
        """Wavy wood-grain lines inside a box."""
        for _ in range(n):
            if vertical:
                x = self.rng.uniform(x0, x1)
                ph = self.rng.random() * 6.28
                ys = np.linspace(y0, y1, 24)
                pts = [(x + amp * math.sin(y * 0.05 + ph), y) for y in ys]
            else:
                y = self.rng.uniform(y0, y1)
                ph = self.rng.random() * 6.28
                xs = np.linspace(x0, x1, 24)
                pts = [(x, y + amp * math.sin(x * 0.05 + ph)) for x in xs]
            seg0 = self.rng.uniform(0, 0.4)
            seg1 = self.rng.uniform(0.6, 1.0)
            k0, k1 = int(seg0 * len(pts)), int(seg1 * len(pts))
            self.simple_line(pts[k0:k1], color + (alpha,), w)

    def text_v(self, s, x, y, size, color=INK, bold=True):
        """Vertical Japanese text, characters stacked top to bottom, x = centre."""
        f = ImageFont.truetype(FONT_B if bold else FONT_R, int(size * self.s))
        for i, ch in enumerate(s):
            px, py = self.P(x, y + i * size * 1.05)
            self.d.text((px, py), ch, font=f, fill=color, anchor="mt")
            self.dm.text((px, py), ch, font=f, fill=255, anchor="mt")

    def text(self, s, x, y, size, color=INK, bold=False, anchor="mm"):
        f = ImageFont.truetype(FONT_B if bold else FONT_R, int(size * self.s))
        self.d.text(self.P(x, y), s, font=f, fill=color, anchor=anchor)
        self.dm.text(self.P(x, y), s, font=f, fill=255, anchor=anchor)


def down(img, factor=2):
    return img.resize((img.width // factor, img.height // factor), Image.LANCZOS)


def leaf_pts(cx, cy, length, width, angle):
    """Pointed leaf outline, base at (cx,cy), pointing along angle (radians)."""
    pts = []
    for i in range(13):
        t = i / 12
        pts.append((t * length, math.sin(math.pi * t) ** 0.8 * width / 2))
    for i in range(11, 0, -1):
        t = i / 12
        pts.append((t * length, -math.sin(math.pi * t) ** 0.8 * width / 2))
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


# ----------------------------------------------------------------- clouds
def make_cloud(world_box, puffs, seed=7, light=(-0.45, -0.75, 0.55), base_y=None):
    """Painted cumulus: shaded puffs posterised into cel tones with dappled edges.
    world_box = (x0, y0, x1, y1) in world units; returns RGBA at scale K."""
    x0, y0, x1, y1 = world_box
    w, h = int((x1 - x0) * K), int((y1 - y0) * K)
    V = np.zeros((h, w), np.float32)
    A = np.zeros((h, w), np.float32)
    N = fnoise(w, h, 40, 5, seed) - 0.5
    N2 = fnoise(w, h, 9, 3, seed + 3) - 0.5
    L = np.array(light, np.float32)
    L /= np.linalg.norm(L)
    for (cx, cy, r, shade) in puffs:
        px, py, pr = (cx - x0) * K, (cy - y0) * K, r * K * 1.2
        bx0, bx1 = int(max(0, px - pr)), int(min(w, px + pr + 1))
        by0, by1 = int(max(0, py - pr)), int(min(h, py + pr + 1))
        if bx0 >= bx1 or by0 >= by1:
            continue
        yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        nx = (xx - px) / (r * K)
        ny = (yy - py) / (r * K)
        d2 = nx * nx + ny * ny
        edge = (1.0 + 0.30 * N[by0:by1, bx0:bx1] + 0.10 * N2[by0:by1, bx0:bx1]) ** 2
        inside = d2 < edge
        nz = np.sqrt(np.clip(1 - np.minimum(d2, 1), 0, 1))
        diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        val = (0.28 + 0.82 * diff) * shade
        V[by0:by1, bx0:bx1] = np.where(inside, val, V[by0:by1, bx0:bx1])
        A[by0:by1, bx0:bx1] = np.where(inside, 1.0, A[by0:by1, bx0:bx1])
    if base_y is not None:
        yy = (np.arange(h, dtype=np.float32) / K + y0)[:, None]
        V *= (1 - 0.22 * np.clip((yy - (base_y - 260)) / 260, 0, 1))
    V = V + N2 * 0.07 + N * 0.08
    th = [0.40, 0.55, 0.70, 0.84]
    idx = np.zeros_like(V, np.int32)
    for t in th:
        idx += (V > t)
    pal = np.array(CLOUD, np.float32)
    rgb = pal[idx]
    alpha = Image.fromarray((A * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    img = Image.fromarray(rgb.astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(0.6))
    img.putalpha(alpha)
    return img


def tower_puffs(seed=11):
    """The single monumental cumulus used in every shot (world-A coordinates)."""
    rng = random.Random(seed)
    base_y, top_y = 2250.0, 760.0
    puffs = []

    def prof(t):
        # half width and centre of the tower at height fraction t (0=base,1=top)
        hw = np.interp(t, [0, 0.18, 0.45, 0.7, 0.86, 1.0], [500, 400, 320, 330, 290, 160])
        c = 560 + 40 * math.sin(t * 2.6) - 60 * t
        return hw, c

    y = base_y - 40
    while y > top_y + 40:
        t = (base_y - y) / (base_y - top_y)
        hw, c = prof(t)
        n = int(hw * 2 / 175) + 2
        for i in range(n):
            fx = i / (n - 1)
            x = c - hw + 2 * hw * fx + rng.uniform(-30, 30)
            r = rng.uniform(130, 220) * (1 - 0.35 * t)
            edge = abs(fx - 0.5) * 2
            if edge > 0.8:
                r *= 0.75
            shade = 1.0 - 0.22 * (fx - 0.5) * 2 * 0.8 - 0.18 * (1 - t) ** 2
            puffs.append((x, y + rng.uniform(-20, 20), r, shade))
        y -= rng.uniform(85, 120)
    # crown
    hw, c = prof(1.0)
    for a in np.linspace(math.pi * 1.1, math.pi * 1.9, 7):
        r = rng.uniform(70, 110)
        puffs.append((c + 260 * math.cos(a), top_y + 170 + 170 * math.sin(a), r * 1.25, 1.05))
    # outline detail puffs
    detail = []
    for (x, y, r, sh) in puffs:
        if rng.random() < 0.5:
            continue
        for _ in range(1):
            a = rng.uniform(math.pi * 1.0, math.pi * 2.0)
            rr = r * rng.uniform(0.3, 0.5)
            detail.append((x + (r * 0.85) * math.cos(a), y + (r * 0.85) * math.sin(a), rr, sh * 1.03))
    # low cloud banks either side
    banks = []
    for i in range(14):
        x = rng.uniform(-40, 260)
        banks.append((x, rng.uniform(2080, 2240), rng.uniform(45, 85), 0.98))
    for i in range(16):
        x = rng.uniform(880, 1300)
        banks.append((x, rng.uniform(2110, 2260), rng.uniform(40, 80), 0.97))
    allp = detail + puffs + banks
    allp.sort(key=lambda p: p[1] - p[2] * 0.3)
    return allp


def sky_gradient(w, h, y0_world, horizon_world, scale=K):
    ys = (np.arange(h, dtype=np.float32) / scale + y0_world)
    t = np.clip(ys / horizon_world, 0, 1) ** 1.6
    top, mid, hor = [np.array(c, np.float32) for c in (SKY_TOP, SKY_MID, SKY_HOR)]
    col = np.where(t[:, None] < 0.6,
                   top + (mid - top) * (t[:, None] / 0.6),
                   mid + (hor - mid) * ((t[:, None] - 0.6) / 0.4))
    arr = np.repeat(col[:, None, :], w, axis=1)
    # painted brush mottling
    n = fnoise(w, h, 120, 4, 21)[..., None]
    arr = arr * (0.975 + 0.05 * n)
    return arr
