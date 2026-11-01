"""Builds the static illustration layers for the reel (run once).

World A  : the wide field view (1240 x 3000 world units, horizon at y=2350).
World B  : the close-up of the counter (1240 x 2620 world units, horizon at y=1560).
Layers are saved at K px per world unit in build/.
"""
import math
import random

import numpy as np
from PIL import Image, ImageFilter

from common import *  # noqa

AW, AH, A_HOR = 1240, 3000, 2350
G_OY = 2080  # ground layer starts at this world-y
BW, BH, B_HOR = 1240, 2620, 1560


# =========================================================== shared pieces
def draw_plant(p, cx, base_y, height, spread, n, rng, kind="round"):
    leaves = []
    for i in range(n):
        a = -math.pi / 2 + rng.uniform(-spread, spread)
        L = height * rng.uniform(0.45, 1.0)
        stem_end = (cx + math.cos(a) * L * 0.55, base_y + math.sin(a) * L * 0.55)
        p.line([(cx, base_y), stem_end], (84, 104, 56), 0.7, 0.2)
        if kind == "round":
            ll, lw = height * rng.uniform(0.22, 0.32), height * rng.uniform(0.13, 0.18)
        elif kind == "long":
            ll, lw = height * rng.uniform(0.5, 0.75), height * rng.uniform(0.06, 0.09)
        else:  # fern
            ll, lw = height * rng.uniform(0.35, 0.5), height * rng.uniform(0.1, 0.14)
        la = a + rng.uniform(-0.5, 0.5)
        col = lerpc(GRASS_DARK, (128, 158, 84), rng.random())
        leaves.append((stem_end[0], stem_end[1], ll, lw, la, col))
    leaves.sort(key=lambda l: -l[1])
    for (x, y, ll, lw, la, col) in leaves:
        pts = leaf_pts(x, y, ll, lw, la)
        p.poly(pts, col, INK, 0.7, 0.15)
        p.line([(x, y), (x + math.cos(la) * ll * 0.8, y + math.sin(la) * ll * 0.8)],
               lerpc(col, INK, 0.45), 0.45, 0.1)


def draw_pot(p, x0, y0, x1, y1, rng):
    inset = (x1 - x0) * 0.12
    rim = (y1 - y0) * 0.2
    p.poly([(x0, y0), (x1, y0), (x1 - 1, y0 + rim), (x0 + 1, y0 + rim)], (190, 116, 84), INK, 1.0, 0.2)
    p.poly([(x0 + 2, y0 + rim), (x1 - 2, y0 + rim), (x1 - inset, y1), (x0 + inset, y1)],
           TERRACOTTA, INK, 1.1, 0.25)
    # shading on right side + hatching
    p.poly([(x1 - (x1 - x0) * 0.3, y0 + rim), (x1 - 2, y0 + rim), (x1 - inset, y1),
            (x1 - inset - (x1 - x0) * 0.2, y1)], TERRA_DARK + (150,), None)
    for i in range(5):
        xx = x1 - (x1 - x0) * 0.08 * (i + 1) - inset * 0.5
        p.simple_line([(xx, y0 + rim + 3), (xx - 2, y1 - 2)], INK + (70,), 0.4)
    # chipped rim
    cx = rng.uniform(x0 + 4, x1 - 8)
    p.poly([(cx, y0), (cx + 5, y0), (cx + 3, y0 + 3)], (214, 160, 128), None)


def draw_bike(p):
    R, F, r = (225.0, 2662.0), (485.0, 2662.0), 78.0
    frame = TEAL
    for (cx, cy) in (R, F):
        # tyre, rim, spokes
        p.ellipse((cx - r, cy - r, cx + r, cy + r), None, (58, 58, 60), 3.2, 0.25)
        p.ellipse((cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5), None, (150, 152, 150), 0.8, 0.1)
        for k in range(18):
            a = k * math.pi * 2 / 18
            p.simple_line([(cx + 4 * math.cos(a + 0.3), cy + 4 * math.sin(a + 0.3)),
                           (cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))], (120, 124, 124, 200), 0.35)
        p.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), (150, 150, 146), INK, 0.8, 0.1)
        # mudguard
        p.arc(cx, cy, r + 6, r + 6, math.pi * 1.08, math.pi * 1.92, (182, 186, 180), 2.6, 0.1)
        p.arc(cx, cy, r + 7.5, r + 7.5, math.pi * 1.08, math.pi * 1.92, INK, 0.6, 0.1)
    B = (338.0, 2684.0)
    Stop = (306.0, 2534.0)
    Hb, Ht = (462.0, 2580.0), (452.0, 2524.0)
    # chain stays / seat stays
    p.line([R, B], frame, 3.0, 0.2)
    p.line([R, (314.0, 2566.0)], frame, 2.6, 0.2)
    # step-through down tube (curved)
    curve = []
    for t in np.linspace(0, 1, 20):
        x = (1 - t) ** 2 * Hb[0] + 2 * (1 - t) * t * 392 + t * t * B[0]
        y = (1 - t) ** 2 * Hb[1] + 2 * (1 - t) * t * 2676 + t * t * B[1]
        curve.append((x, y))
    p.line(curve, frame, 5.0, 0.2)
    p.line(curve, INK, 0.6, 0.2)
    p.line([B, Stop], frame, 4.2, 0.2)
    p.line([Hb, Ht], frame, 5.0, 0.1)
    # fork
    p.line([Hb, (476.0, 2630.0), F], (150, 156, 154), 2.4, 0.15)
    # chain guard
    p.poly([(240, 2652), (345, 2668), (352, 2690), (245, 2672)], (98, 140, 146), INK, 0.8, 0.2)
    # crank + pedal
    p.line([B, (360.0, 2712.0)], (60, 60, 62), 1.6, 0.1)
    p.rect(350, 2710, 374, 2716, (70, 70, 70), INK, 0.6, 0.1)
    # kickstand
    p.line([R, (246.0, 2741.0)], (110, 112, 112), 1.6, 0.1)
    # rear rack
    p.line([(160.0, 2578.0), (306.0, 2578.0)], (150, 152, 150), 2.0, 0.1)
    p.line([(176.0, 2578.0), R], (150, 152, 150), 1.2, 0.1)
    p.line([(286.0, 2578.0), R], (150, 152, 150), 1.2, 0.1)
    # saddle
    p.line([Stop, (302.0, 2516.0)], (150, 152, 150), 2.0, 0.1)
    p.poly([(278, 2512), (322, 2508), (330, 2514), (316, 2522), (282, 2520)], (82, 62, 48), INK, 0.9, 0.2)
    # stem + swept-back handlebar + grips + bell
    p.line([Ht, (448.0, 2498.0)], (150, 152, 150), 2.2, 0.1)
    bar = [(448.0, 2498.0), (430.0, 2494.0), (405.0, 2500.0), (392.0, 2506.0)]
    p.line(bar, (160, 162, 160), 2.0, 0.1)
    p.line([(392.0, 2506.0), (374.0, 2512.0)], (58, 52, 48), 3.2, 0.1)
    p.ellipse((432, 2486, 442, 2495), (196, 196, 188), INK, 0.6, 0.05)
    # front basket (wire) with folded cloth bag
    bx0, by0, bx1, by1 = 462, 2506, 540, 2566
    p.poly([(bx0 + 10, by0 - 6), (bx0 + 52, by0 - 18), (bx0 + 40, by0 + 4)], (176, 160, 120), INK, 0.8, 0.2)
    p.rect(bx0, by0, bx1, by1, (120, 128, 126, 40), (110, 116, 116), 1.4, 0.2)
    for i in range(1, 9):
        x = bx0 + i * (bx1 - bx0) / 9
        p.simple_line([(x, by0), (x, by1)], (110, 116, 116, 220), 0.45)
    for i in range(1, 6):
        y = by0 + i * (by1 - by0) / 6
        p.simple_line([(bx0, y), (bx1, y)], (110, 116, 116, 220), 0.45)
    p.line([(bx0 + 20.0, by1), (476.0, 2630.0)], (130, 134, 132), 1.0, 0.1)
    # lamp
    p.ellipse((482, 2588, 496, 2602), (210, 204, 180), INK, 0.6, 0.05)


def draw_card(p, x0, y0, x1, y1, word=None, icon=None, size=12, tilt=0.0):
    p.poly([(x0, y0), (x1, y0 + tilt), (x1, y1 + tilt), (x0, y1)], PAPER, INK, 0.8, 0.2)
    p.simple_line([(x0 + 1.5, y1 - 1.5), (x1 - 1.5, y1 + tilt - 1.5)], (200, 188, 160, 160), 0.6)
    cx = (x0 + x1) / 2
    if word:
        p.text_v(word, cx, y0 + (y1 - y0 - len(word) * size * 1.05) / 2 + 1, size, (54, 46, 42), True)
    if icon == "cup":
        s = (x1 - x0) * 0.32
        cy = (y0 + y1) / 2 + 2
        p.poly([(cx - s, cy - s * 0.6), (cx + s, cy - s * 0.6), (cx + s * 0.75, cy + s * 0.7),
                (cx - s * 0.75, cy + s * 0.7)], None, (54, 46, 42), 0.9, 0.1)
        p.arc(cx + s, cy, s * 0.35, s * 0.35, -1.4, 1.4, (54, 46, 42), 0.8, 0.05)
        for k in (-0.4, 0.2):
            p.line([(cx + k * s, cy - s * 0.8), (cx + k * s + 2, cy - s * 1.2), (cx + k * s, cy - s * 1.6)],
                   (54, 46, 42), 0.6, 0.05)


# =========================================================== world A
def build_A_sky():
    w, h = int(AW * K), int(AH * K)
    arr = sky_gradient(w, h, 0, A_HOR)
    sky = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    box = (-60, 260, 1300, 2420)
    cloud = make_cloud(box, tower_puffs(), seed=7, base_y=2250)
    sky.alpha_composite(cloud, (int(box[0] * K), int(box[1] * K)))
    # horizon haze
    ys = np.arange(h, dtype=np.float32) / K
    haze = np.clip(1 - np.abs(ys - A_HOR) / 140, 0, 1) ** 2 * 0.35
    a = np.asarray(sky).astype(np.float32)
    a[..., :3] = a[..., :3] * (1 - haze[:, None, None]) + np.array(SKY_HOR, np.float32) * haze[:, None, None]
    Image.fromarray(a.astype(np.uint8)).convert("RGB").save(f"{BUILD}/A_sky.png")
    cloud.save(f"{BUILD}/cloud.png")


def draw_field(p, y_hor, y_bot, x0, x1, rng, n_blades, near_len=26):
    # low hazy hill, then a distant rounded tree line
    hill = [(x0, y_hor)] + [(x, y_hor - 26 * math.exp(-((x - 170) / 190) ** 2) - 10 * math.exp(-((x - 1050) / 160) ** 2))
                            for x in np.linspace(x0, x1, 60)] + [(x1, y_hor)]
    p.poly(hill, (128, 156, 166), None)
    x = x0
    while x < x1:
        if rng.random() < 0.55:
            n = rng.randint(2, 6)
            for k in range(n):
                r = rng.uniform(4, 10)
                cx = x + k * r * 1.2
                p.ellipse((cx - r, y_hor - r * 1.5 - 2, cx + r, y_hor + 2), lerpc((104, 138, 136), (88, 118, 116), rng.random()), None)
            x += n * 10
        x += rng.uniform(10, 60)
    p.rect(x0, y_hor - 4, x1, y_hor + 1, (112, 146, 138), None)
    # field base with distance gradient
    steps = 40
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        ya, yb = lerp(y_hor, y_bot, t0 ** 1.4), lerp(y_hor, y_bot, t1 ** 1.4)
        p.rect(x0, ya, x1, yb + 1, lerpc(GRASS_FAR, GRASS_NEAR, t0 ** 0.8), None)
    # mottled patches
    for _ in range(140):
        y = lerp(y_hor + 4, y_bot, rng.random() ** 1.3)
        t = (y - y_hor) / (y_bot - y_hor)
        rx, ry = rng.uniform(30, 120) * (0.4 + t), rng.uniform(3, 9) * (0.4 + t)
        xx = rng.uniform(x0, x1)
        col = lerpc(GRASS_FAR, GRASS_NEAR, t)
        col = lerpc(col, (182, 190, 120) if rng.random() < 0.5 else GRASS_DARK, 0.25)
        p.ellipse((xx - rx, y - ry, xx + rx, y + ry), col + (120,), None)
    # individual blades
    for _ in range(n_blades):
        t = rng.random() ** 0.7
        y = lerp(y_hor + 2, y_bot + 10, t)
        L = lerp(2.5, near_len, t) * rng.uniform(0.6, 1.2)
        xx = rng.uniform(x0, x1)
        a = -math.pi / 2 + rng.uniform(-0.35, 0.35)
        base = lerpc(GRASS_FAR, GRASS_NEAR, t)
        r = rng.random()
        col = lerpc(base, GRASS_DARK, 0.7) if r < 0.4 else lerpc(base, GRASS_LIGHT, 0.7) if r < 0.75 else lerpc(base, INK, 0.45)
        p.simple_line([(xx, y), (xx + math.cos(a) * L * 0.5 + 1, y + math.sin(a) * L * 0.5),
                       (xx + math.cos(a) * L + 2, y + math.sin(a) * L)], col + (235,), lerp(0.4, 1.1, t))


def draw_stand_A(p, rng):
    # ground shadow
    p.ellipse((440, 2722, 970, 2764), (58, 82, 42, 120), None)
    # bamboo pole (behind banner)
    p.rect(931, 2150, 940, 2748, (196, 180, 128), INK, 0.9, 0.15)
    for y in (2240, 2380, 2520, 2660):
        p.simple_line([(931, y), (940, y)], INK + (200,), 0.7)
    p.line([(936.0, 2292.0), (1042.0, 2292.0)], (196, 180, 128), 2.4, 0.1)
    p.line([(936.0, 2290.0), (1042.0, 2290.0)], INK, 0.5, 0.1)
    # back posts and back shelf seen through the open stand
    p.rect(519, 2268, 529, 2505, (120, 94, 70), INK, 0.8, 0.2)
    p.rect(831, 2268, 841, 2505, (120, 94, 70), INK, 0.8, 0.2)
    p.rect(522, 2414, 838, 2421, WOOD_MID, INK, 0.7, 0.2)
    for (x, hgt, col) in ((560, 22, (210, 204, 186)), (590, 16, (186, 120, 90)), (742, 24, (150, 170, 160)),
                          (770, 18, (220, 214, 196)), (800, 14, (200, 140, 100))):
        p.rect(x, 2414 - hgt, x + 18, 2414, col, INK, 0.6, 0.15)
    # roof slab (thatch) and underside
    p.poly([(422, 2196), (944, 2192), (950, 2250), (414, 2252)], THATCH, INK, 1.3, 0.5)
    for x in np.arange(418, 948, 3.2):
        col = THATCH_LIGHT if rng.random() < 0.5 else (176, 154, 116)
        y0 = 2196 + rng.uniform(0, 4)
        p.simple_line([(x, y0), (x + rng.uniform(-1, 1), 2250 + rng.uniform(-1, 3))], col + (190,), 0.5)
    p.line([(418.0, 2214.0), (946.0, 2210.0)], INK_SOFT, 0.6, 0.4)
    p.poly([(416, 2250), (948, 2249), (940, 2263), (425, 2264)], (96, 74, 54), INK, 0.9, 0.2)
    # tin repair patch on the roof
    p.rect(796, 2206, 846, 2230, (162, 170, 168), INK, 0.7, 0.2)
    for x in (800, 842):
        for y in (2210, 2226):
            p.ellipse((x - 1, y - 1, x + 1, y + 1), INK, None)
    # rope ties
    for x in (520, 700, 860):
        p.line([(x, 2236.0), (x + 4, 2262.0)], (150, 128, 90), 1.4, 0.1)
    # front beam + side stick (with a dangling rope)
    p.rect(436, 2262, 928, 2276, WOOD_DARK, INK, 1.0, 0.3)
    p.grain(438, 2263, 926, 2275, (60, 44, 32), 6, vertical=False, alpha=120, amp=0.6)
    p.line([(372.0, 2290.0), (480.0, 2286.0)], WOOD_MID, 2.6, 0.2)
    p.line([(392.0, 2290.0), (394.0, 2336.0)], (150, 128, 90), 0.8, 0.3)
    # hanging cards: 珈琲 / 氷 / cup pictogram (same as the close-up)
    for (x, word, icon) in ((548, "珈琲", None), (640, "氷", None), (760, None, "cup")):
        p.simple_line([(x + 14, 2276), (x + 14, 2290)], INK + (200,), 0.5)
        h = 50 if word == "珈琲" else 38
        draw_card(p, x, 2290, x + 28, 2290 + h, word, icon, 12, tilt=1.0)
    # counter items (left -> right)
    # glass jars
    for (x0, x1, top, fill) in ((498, 528, 2452, (98, 64, 44)), (532, 556, 2464, (190, 130, 60))):
        p.rect(x0, top - 6, x1, top, (176, 150, 112), INK, 0.7, 0.1)
        p.rect(x0, top, x1, 2498, TEAL_LIGHT + (110,), INK, 0.8, 0.15)
        p.rect(x0 + 2, top + (2498 - top) * 0.4, x1 - 2, 2496, fill + (210,), None)
        p.simple_line([(x0 + 4, top + 4), (x0 + 4, 2490)], (250, 250, 240, 200), 0.9)
    # kettle
    p.poly([(574, 2472), (608, 2472), (614, 2498), (568, 2498)], (150, 164, 164), INK, 0.9, 0.2)
    p.ellipse((578, 2464, 604, 2476), (162, 176, 176), INK, 0.7, 0.1)
    p.line([(610.0, 2490.0), (622.0, 2478.0), (626.0, 2462.0), (632.0, 2458.0)], (150, 164, 164), 1.6, 0.1)
    p.arc(591, 2468, 14, 12, math.pi, math.pi * 2, INK, 1.0, 0.1)
    # Bible (small, dark cover) and cup with saucer
    p.poly([(642, 2490), (676, 2489), (680, 2495), (646, 2496)], NAVY, INK, 0.7, 0.1)
    p.poly([(646, 2496), (680, 2495), (680, 2498), (646, 2499)], PAPER, INK, 0.5, 0.05)
    p.ellipse((688, 2495, 722, 2501), (176, 140, 100), INK, 0.6, 0.05)
    p.poly([(694, 2477), (716, 2477), (714, 2497), (696, 2497)], (232, 226, 210), INK, 0.8, 0.1)
    p.poly([(694, 2477), (716, 2477), (715, 2482), (695, 2482)], TEAL_LIGHT, None)
    p.ellipse((694, 2475, 716, 2479), (74, 48, 34), INK, 0.5, 0.05)
    # stacked cups
    for i, y in enumerate((2486, 2474)):
        p.poly([(762 + i, y), (790 - i, y), (786 - i, y + 12), (766 + i, y + 12)], (226, 220, 206), INK, 0.7, 0.1)
    # little herb pot on the counter
    draw_pot(p, 820, 2480, 848, 2498, rng)
    draw_plant(p, 834, 2481, 40, 0.9, 9, rng, "round")
    # front posts (with a rope-bound repair)
    for x in (476, 868):
        p.rect(x, 2262, x + 15, 2690, WOOD_DARK, INK, 1.1, 0.3)
        p.grain(x + 1, 2264, x + 14, 2688, (60, 44, 32), 4, alpha=150, amp=0.5)
    for x in (476, 868):
        p.rect(x + 1, 2276, x + 14, 2296, (40, 30, 22, 140), None)
        for k in range(10):
            yy = 2300 + k * 38
            p.simple_line([(x + 10, yy), (x + 14, yy + 14)], (40, 30, 22, 140), 0.4)
    for k in range(6):
        y = 2392 + k * 4
        p.line([(474.0, y), (493.0, y + 3)], (186, 164, 118), 1.2, 0.05)
    # counter ledge
    p.poly([(452, 2496), (908, 2494), (910, 2502), (450, 2504)], WOOD_LIGHT, INK, 0.8, 0.15)
    p.poly([(450, 2504), (910, 2502), (910, 2514), (452, 2516)], WOOD, INK, 1.0, 0.2)
    p.grain(452, 2505, 908, 2513, (150, 118, 84), 5, vertical=False, alpha=150, amp=0.5)
    # red front panel with planks, wear and a repair plank
    p.poly([(464, 2514), (896, 2512), (896, 2690), (464, 2690)], RED, INK, 1.2, 0.3)
    p.rect(465, 2515, 895, 2526, RED_DARK + (150,), None)
    for x in np.arange(464, 896, 48):
        p.line([(x, 2515.0), (x + rng.uniform(-1, 1), 2689.0)], RED_DARK, 0.8, 0.3)
    p.grain(466, 2516, 894, 2688, (150, 70, 52), 40, alpha=110, amp=1.0)
    for _ in range(26):  # worn paint
        x, y = rng.uniform(470, 890), rng.uniform(2520, 2684)
        rx, ry = rng.uniform(2, 9), rng.uniform(1, 3)
        p.ellipse((x - rx, y - ry, x + rx, y + ry), (204, 168, 128, 150), None)
    p.rect(752, 2516, 796, 2688, RED_LIGHT, INK, 0.9, 0.3)
    p.grain(754, 2518, 794, 2686, (170, 92, 70), 8, alpha=120, amp=0.8)
    for y in (2526, 2678):
        for x in (758, 790):
            p.ellipse((x - 1.2, y - 1.2, x + 1.2, y + 1.2), (70, 60, 56), None)
    draw_card(p, 600, 2548, 638, 2626, "珈琲", None, 16, tilt=-1)
    draw_card(p, 652, 2550, 690, 2628, "麦茶", None, 16, tilt=1)
    for (x, y) in ((600, 2548), (638, 2547), (652, 2550), (690, 2551)):
        p.rect(x - 3, y - 2, x + 3, y + 3, (226, 214, 180, 200), None)
    # base rail + cart wheels
    p.rect(456, 2688, 904, 2700, WOOD_DARK, INK, 1.0, 0.2)
    for cx in (545, 815):
        p.ellipse((cx - 28, 2684, cx + 28, 2740), (70, 58, 48), INK, 1.2, 0.2)
        p.ellipse((cx - 20, 2692, cx + 20, 2732), (104, 86, 66), INK, 0.6, 0.1)
        for k in range(8):
            a = k * math.pi / 4
            p.simple_line([(cx, 2712), (cx + 19 * math.cos(a), 2712 + 19 * math.sin(a))], INK + (200,), 0.6)
    # pots on the right (pole base)
    draw_pot(p, 900, 2690, 962, 2750, rng)
    draw_plant(p, 931, 2692, 120, 1.1, 22, rng, "round")
    draw_pot(p, 968, 2708, 1010, 2752, rng)
    draw_plant(p, 989, 2709, 90, 0.5, 10, rng, "long")
    draw_pot(p, 1016, 2702, 1066, 2752, rng)
    draw_plant(p, 1041, 2703, 84, 1.2, 18, rng, "fern")
    # bicycle, then the front-left pots that sit in front of it
    draw_bike(p)
    draw_pot(p, 548, 2700, 604, 2750, rng)
    draw_plant(p, 576, 2701, 92, 1.1, 20, rng, "round")
    draw_pot(p, 610, 2716, 646, 2752, rng)
    draw_plant(p, 628, 2717, 70, 0.45, 9, rng, "long")


def build_A_ground():
    gw, gh = AW, AH - G_OY
    p = Pen((int(gw * S), int(gh * S)), S, (0, G_OY), seed=5)
    rng = random.Random(42)
    draw_field(p, A_HOR, AH, 0, AW, rng, 26000)
    draw_stand_A(p, rng)
    # static foreground blades over the base of the stand, pots and wheels
    for _ in range(1400):
        x = rng.uniform(0, AW)
        y = rng.uniform(2735, 2780)
        L = rng.uniform(10, 30)
        a = -math.pi / 2 + rng.uniform(-0.4, 0.4)
        col = lerpc(GRASS_NEAR, GRASS_LIGHT if rng.random() < 0.5 else GRASS_DARK, rng.random() * 0.6)
        p.simple_line([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], col + (235,), 0.9)
    down(p.result()).save(f"{BUILD}/A_ground.png")


def build_banner():
    bw, bh = 92, 300
    p = Pen((int(bw * S), int(bh * S)), S, (0, 0), seed=8)
    p.poly([(2, 2), (bw - 2, 2), (bw - 3, bh - 2), (3, bh - 2)], (236, 228, 205), INK, 1.1, 0.3)
    p.rect(2, 2, bw - 2, 12, (66, 92, 112), INK, 0.8, 0.1)
    p.rect(3, bh - 14, bw - 3, bh - 2, (66, 92, 112), INK, 0.8, 0.1)
    rng = random.Random(4)
    for _ in range(30):
        x, y = rng.uniform(6, bw - 6), rng.uniform(16, bh - 18)
        p.simple_line([(x, y), (x + rng.uniform(-2, 2), y + rng.uniform(10, 40))], (200, 190, 166, 120), 0.5)
    p.text_v("ひとやすみ", bw / 2, 34, 44, (52, 58, 76), True)
    down(p.result()).save(f"{BUILD}/banner.png")


# =========================================================== world B (close-up)
def build_B_bg():
    w, h = int(BW * K), int(BH * K)
    arr = sky_gradient(w, h, 0, B_HOR)
    sky = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    cloud = Image.open(f"{BUILD}/cloud.png")
    s = 0.9
    cw, ch = int(cloud.width * s), int(cloud.height * s)
    c2 = cloud.resize((cw, ch), Image.LANCZOS)
    # cloud box was (-60,260)-(1300,2420); base at 2250 -> place base at B_HOR-10
    ox = (620 - (560 + 60) * s)  # keep tower centre near x=620
    oy = (B_HOR - 10) - (2250 - 260) * s
    sky.alpha_composite(c2, (int(ox * K), int(oy * K)))
    ys = np.arange(h, dtype=np.float32) / K
    haze = np.clip(1 - np.abs(ys - B_HOR) / 120, 0, 1) ** 2 * 0.35
    a = np.asarray(sky).astype(np.float32)
    a[..., :3] = a[..., :3] * (1 - haze[:, None, None]) + np.array(SKY_HOR, np.float32) * haze[:, None, None]
    sky = Image.fromarray(a.astype(np.uint8))
    # field seen through the stand
    p = Pen((int(BW * S), int((BH - B_HOR + 30) * S)), S, (0, B_HOR - 30), seed=12)
    draw_field(p, B_HOR, BH, 0, BW, random.Random(9), 14000, near_len=40)
    fld = down(p.result())
    sky.alpha_composite(fld, (0, int((B_HOR - 30) * K)))
    sky.convert("RGB").save(f"{BUILD}/B_bg.png")


def build_B_stand():
    p = Pen((int(BW * S), int(BH * S)), S, (0, 0), seed=21)
    rng = random.Random(77)
    # roof underside: thatch fringe, rafters, front beam
    p.rect(-10, -10, BW + 10, 150, (112, 88, 64), INK, 1.2, 0.4)
    for x in np.arange(-10, BW + 10, 70):
        p.rect(x, -10, x + 16, 150, WOOD_DARK, INK, 0.8, 0.3)
    p.poly([(-10, 120), (BW + 10, 112), (BW + 10, 236), (-10, 244)], THATCH, INK, 1.6, 0.6)
    for x in np.arange(-10, BW + 10, 5):
        col = THATCH_LIGHT if rng.random() < 0.5 else (176, 154, 116)
        p.simple_line([(x, 120 + rng.uniform(0, 6)), (x + rng.uniform(-2, 2), 236 + rng.uniform(-2, 10))], col + (200,), 0.8)
    p.rect(-10, 236, BW + 10, 276, WOOD_DARK, INK, 1.4, 0.4)
    p.grain(-8, 238, BW + 8, 274, (60, 44, 32), 10, vertical=False, alpha=140, amp=1.0, w=0.8)
    # tin patch
    p.rect(860, 140, 1000, 200, (162, 170, 168), INK, 1.0, 0.3)
    for x in (870, 990):
        for y in (150, 190):
            p.ellipse((x - 2, y - 2, x + 2, y + 2), INK, None)
    # hanging cards (same three as the wide shot)
    for (x, word, icon, h) in ((250, "珈琲", None, 190), (520, "氷", None, 120), (860, None, "cup", 120)):
        p.line([(x + 45.0, 276.0), (x + 45.0, 310.0)], INK, 0.8, 0.1)
        draw_card(p, x, 310, x + 90, 310 + h, word, icon, 44 if word else 12, tilt=3)
    # posts at the frame edges, left one with a rope repair
    p.rect(30, 276, 112, 2300, WOOD_DARK, INK, 1.6, 0.5)
    p.grain(32, 280, 110, 2296, (60, 44, 32), 14, alpha=150, amp=1.5, w=0.8)
    p.rect(98, 280, 110, 2296, (40, 30, 22, 120), None)
    for k in range(9):
        y = 1230 + k * 14
        p.line([(28.0, y), (114.0, y + 10)], (186, 164, 118), 4.0, 0.1)
        p.line([(28.0, y + 3), (114.0, y + 13)], INK, 0.6, 0.1)
    p.rect(1128, 276, 1210, 2300, WOOD_DARK, INK, 1.6, 0.5)
    p.grain(1130, 280, 1208, 2296, (60, 44, 32), 14, alpha=150, amp=1.5, w=0.8)
    p.rect(1196, 280, 1208, 2296, (40, 30, 22, 120), None)
    # back rail of the counter (behind items)
    p.rect(70, 1800, 1170, 1830, WOOD_MID, INK, 1.0, 0.3)
    # counter top (seen from above, slight perspective) + front edge
    p.poly([(60, 1828), (1180, 1828), (1220, 2250), (20, 2250)], WOOD, INK, 1.4, 0.5)
    p.grain(40, 1832, 1200, 2246, (160, 128, 92), 70, vertical=False, alpha=120, amp=2.0, w=0.9)
    for y in (1930, 2060, 2170):  # board seams
        x_off = (y - 1828) / (2250 - 1828) * 40
        p.line([(60 - x_off, y), (1180 + x_off, y)], (130, 100, 72), 1.0, 0.6)
    # butterfly-key repair across a crack
    p.line([(940.0, 1990.0), (965.0, 2010.0), (990.0, 2050.0), (1010.0, 2070.0)], INK_SOFT, 1.0, 0.3)
    p.poly([(950, 2010), (1000, 2010), (985, 2030), (1000, 2050), (950, 2050), (965, 2030)],
           (150, 112, 78), INK, 1.0, 0.2)
    # wear marks and cup rings
    for _ in range(18):
        x, y = rng.uniform(100, 1150), rng.uniform(1850, 2230)
        p.ellipse((x - rng.uniform(10, 40), y - 3, x + rng.uniform(10, 40), y + 3), (214, 192, 152, 90), None)
    p.ellipse((1030, 2120, 1150, 2150), None, (150, 116, 82, 160), 1.0, 0.3)
    p.poly([(20, 2250), (1220, 2250), (1220, 2300), (20, 2300)], WOOD_MID, INK, 1.4, 0.4)
    p.grain(22, 2252, 1218, 2298, (120, 90, 64), 10, vertical=False, alpha=150, amp=1.0)
    # red panel below
    p.poly([(20, 2300), (1220, 2300), (1220, 2640), (20, 2640)], RED, INK, 1.4, 0.4)
    for x in np.arange(20, 1220, 130):
        p.line([(x, 2302.0), (x + 2, 2638.0)], RED_DARK, 1.2, 0.5)
    p.grain(22, 2302, 1218, 2638, (150, 70, 52), 50, alpha=110, amp=2.0, w=0.9)
    for _ in range(30):
        x, y = rng.uniform(30, 1210), rng.uniform(2310, 2630)
        rx, ry = rng.uniform(4, 22), rng.uniform(2, 6)
        p.ellipse((x - rx, y - ry, x + rx, y + ry), (204, 168, 128, 150), None)
    # kettle (back left)
    p.poly([(120, 1720), (270, 1720), (300, 1830), (90, 1830)], (150, 164, 164), INK, 1.4, 0.4)
    p.ellipse((140, 1690, 250, 1735), (162, 176, 176), INK, 1.2, 0.2)
    p.ellipse((180, 1676, 210, 1694), (110, 90, 70), INK, 1.0, 0.1)
    p.arc(195, 1712, 70, 60, math.pi, math.pi * 2, INK, 3.0, 0.2)
    p.arc(195, 1712, 70, 60, math.pi, math.pi * 2, (72, 60, 52), 2.0, 0.2)
    p.line([(290.0, 1800.0), (330.0, 1760.0), (342.0, 1700.0), (368.0, 1688.0)], (150, 164, 164), 7.0, 0.2)
    p.line([(290.0, 1800.0), (330.0, 1760.0), (342.0, 1700.0), (368.0, 1688.0)], INK, 0.8, 0.2)
    p.poly([(250, 1740), (282, 1760), (282, 1820), (258, 1826)], (190, 200, 198, 160), None)
    # glass jars (back right)
    for (x0, x1, top, fill) in ((900, 1010, 1640, (98, 64, 44)), (1030, 1130, 1690, (190, 130, 60))):
        p.rect(x0 - 4, top - 26, x1 + 4, top, (176, 150, 112), INK, 1.2, 0.2)
        p.grain(x0 - 2, top - 24, x1 + 2, top - 2, (140, 112, 80), 6, vertical=False, alpha=150, amp=0.6)
        p.rect(x0, top, x1, 1826, TEAL_LIGHT + (110,), INK, 1.3, 0.3)
        p.rect(x0 + 6, top + (1826 - top) * 0.38, x1 - 6, 1820, fill + (215,), None)
        if fill[0] < 120:  # coffee beans
            for _ in range(60):
                bx, by = rng.uniform(x0 + 10, x1 - 10), rng.uniform(top + (1826 - top) * 0.4, 1815)
                p.ellipse((bx - 5, by - 3.5, bx + 5, by + 3.5), (72, 46, 32), (52, 34, 24), 0.4, 0.05, n=12)
        p.simple_line([(x0 + 12, top + 10), (x0 + 12, 1810)], (250, 250, 240, 200), 2.0)
    # saucer, cup and coffee (centre-right)
    p.ellipse((630, 2090, 890, 2150), (176, 140, 100), INK, 1.2, 0.2)
    p.ellipse((650, 2096, 870, 2140), (190, 156, 116), None)
    p.poly([(675, 1960), (845, 1960), (830, 2110), (690, 2110)], (232, 226, 210), INK, 1.5, 0.4)
    p.poly([(690, 2060), (830, 2060), (830, 2110), (690, 2110)], (214, 206, 188, 200), None)
    for k in range(6):  # hatched shadow side
        x = 800 + k * 6
        p.simple_line([(x, 1975), (x - 4, 2100)], INK + (60,), 0.6)
    drip = [(675, 1960), (845, 1960), (842, 1985), (820, 1998), (800, 1988), (775, 2002), (745, 1990),
            (718, 2000), (695, 1988), (677, 1986)]
    p.poly(drip, TEAL_LIGHT, INK, 0.9, 0.2)
    p.ellipse((675, 1946, 845, 1974), (230, 224, 206), INK, 1.4, 0.3)
    p.ellipse((684, 1950, 836, 1971), (74, 48, 34), None)
    p.ellipse((720, 1953, 780, 1960), (120, 86, 60, 200), None)
    p.arc(850, 2020, 34, 40, -1.5, 1.5, INK, 2.6, 0.2)
    p.arc(850, 2020, 34, 40, -1.5, 1.5, (232, 226, 210), 1.6, 0.2)
    # small sprig of mint in a tiny pot (right of the cup)
    draw_pot(p, 980, 1890, 1060, 1960, rng)
    draw_plant(p, 1020, 1892, 120, 0.9, 16, rng, "round")
    down(p.result()).save(f"{BUILD}/B_stand.png")


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["sky", "ground", "banner", "bbg", "bstand"]
    if "sky" in which:
        build_A_sky(); print("A_sky")
    if "ground" in which:
        build_A_ground(); print("A_ground")
    if "banner" in which:
        build_banner(); print("banner")
    if "bbg" in which:
        build_B_bg(); print("B_bg")
    if "bstand" in which:
        build_B_stand(); print("B_stand")
