"""Soundtracks for the batch-2 reels: python3 audio2.py <reel 1-5> -> build/b2_<n>/audio.wav

Same palette as reel 1 (felt piano, guitar harmonics, warm pad, 72 BPM in F major, ambience
mixed forward), with a different progression per reel and its own sound effects. The music
resolves on F when ゆとり場 appears (12.7 s).
"""
import math
import sys
import wave

import numpy as np

import audio as A
from audio import SR, N, t_all, bp, lp, hp, place, reverb, felt_piano, guitar_harm, vibes, pad, hz, BEAT, BAR
from common import BUILD

rng = np.random.default_rng(77)
T_RES = 12.7


def env_from(fn):
    return np.array([fn(x) for x in np.arange(0, 15.0, 0.01)])


def follow(fn):
    """Sample-rate envelope from a function of time."""
    return np.interp(t_all, np.arange(0, 15.0, 0.01), env_from(fn))


# ------------------------------------------------------------------ ambience pieces
def wind(level=1.0, seed=3):
    amb = np.zeros((2, N))
    gust = 0.55 + 0.45 * A.smooth_rand(N, 0.5, seed)
    for ch in range(2):
        w = rng.standard_normal(N)
        low = lp(w, 380) * 2.2
        hiss = bp(rng.standard_normal(N), 1800, 6500) * 0.55
        g2 = 0.55 + 0.45 * A.smooth_rand(N, 0.9, seed + 7 + ch)
        amb[ch] += (low * gust + hiss * gust * g2) * 0.11 * level
    return amb


def cicadas(level=1.0):
    amb = np.zeros((2, N))
    for (pan, f0, ph, g) in ((-0.55, 4300, 0.0, 1.0), (0.6, 3700, 1.7, 0.7)):
        carrier = bp(rng.standard_normal(N), f0 - 500, f0 + 500, 2)
        pulse = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 95 * t_all + ph))
        phrase = 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * t_all + ph) ** 2
        sig = lp(carrier * pulse, 6000) * phrase
        place(amb, sig * 0.010 * g * level, 0, pan)
    return amb


def higurashi(starts):
    """Evening cicada: a falling 'kana-kana-kana' phrase."""
    out = np.zeros((2, N))
    for (t0, pan, g) in starts:
        n = int(3.2 * SR)
        tt = np.arange(n) / SR
        f = 4700 - 700 * tt / 3.2
        ph = 2 * np.pi * np.cumsum(f) / SR
        am = (0.5 + 0.5 * np.sin(2 * np.pi * 7.5 * tt)) ** 3
        e = np.exp(-tt * 0.6) * np.minimum(1, tt / 0.05)
        sig = np.sin(ph) * am * e + 0.3 * np.sin(2 * ph) * am * e
        place(out, lp(sig, 7000) * 0.016 * g, t0, pan)
    return out


def crickets(level=1.0):
    out = np.zeros((2, N))
    for (pan, f0, rate, ph) in ((-0.5, 4700, 1.9, 0.0), (0.45, 5200, 2.3, 0.4), (0.1, 4400, 1.6, 0.8)):
        chirp = (np.sin(2 * np.pi * rate * t_all + ph) > 0.55).astype(float)
        pulses = (0.5 + 0.5 * np.sin(2 * np.pi * 32 * t_all)) ** 4
        sig = np.sin(2 * np.pi * f0 * t_all) * chirp * pulses
        place(out, lp(sig, 7000) * 0.006 * level, 0, pan)
    return out


def birds(times, level=1.0, seed=5):
    out = np.zeros((2, N))
    r = np.random.default_rng(seed)
    for t0 in times:
        for k in range(r.integers(2, 5)):
            n = int(r.uniform(0.07, 0.15) * SR)
            tt = np.arange(n) / SR
            f0, f1 = r.uniform(2800, 4200), r.uniform(3200, 5200)
            f = f0 + (f1 - f0) * tt / tt[-1]
            ph = 2 * np.pi * np.cumsum(f) / SR
            e = np.sin(np.pi * tt / tt[-1]) ** 2
            place(out, lp(np.sin(ph) * e, 6000) * 0.02 * level, t0 + k * r.uniform(0.11, 0.2), r.uniform(-0.7, 0.7))
    return out


def rain(fn):
    e = follow(fn)
    out = np.zeros((2, N))
    for ch in range(2):
        hiss = bp(rng.standard_normal(N), 900, 9000) * 0.5
        body = lp(rng.standard_normal(N), 500) * 1.2
        patter = lp((rng.random(N) < 0.0025) * rng.standard_normal(N) * 6, 3000)
        out[ch] = (hiss + body + patter) * e * 0.13
    return out


# ------------------------------------------------------------------ one-shots
def bell(t0, out, pan=-0.3, g=0.012):
    for dt in (0.0, 0.12):
        n = int(1.1 * SR)
        tt = np.arange(n) / SR
        sig = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d)
                  for f, a, d in ((2950, 1.0, 4.0), (4130, 0.6, 5.5), (6280, 0.3, 8.0), (7710, 0.15, 10)))
        place(out, lp(sig * np.minimum(1, tt / 0.002), 5200) * g, t0 + dt, pan)


def freewheel(t0, t1, out, pan=-0.4, g=0.05):
    n = int((t1 - t0) * SR)
    clicks = np.zeros(n)
    pos, rate = 0.0, 16.0
    while pos < n - 10:
        clicks[int(pos)] = 1.0
        rate = max(6, rate * 0.995)
        pos += SR / rate
    e = np.interp(np.arange(n), [0, n * 0.2, n], [0, 1, 0.4])
    place(out, bp(clicks, 2000, 7000) * e * g, t0, pan)


def click(t0, out, f=(1800, 5200), g=0.12, pan=0.0):
    n = int(0.08 * SR)
    sig = bp(rng.standard_normal(n), *f) * np.exp(-np.arange(n) / SR * 90)
    place(out, sig * g, t0, pan)


def ceramic(t0, out, g=0.02, pan=0.2, f0=2210):
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    sig = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d)
              for f, a, d in ((f0, 1.0, 14), (f0 * 1.75, 0.5, 18), (f0 * 2.55, 0.25, 24)))
    sig += lp(rng.standard_normal(n), 400) * np.exp(-tt * 60) * 0.6
    place(out, sig * g, t0, pan)


def ice(t0, out):
    for k, dt in enumerate((0.0, 0.09, 0.2)):
        n = int(0.35 * SR)
        tt = np.arange(n) / SR
        f = 4200 + 900 * k
        sig = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.62 * tt)) * np.exp(-tt * 30)
        place(out, sig * 0.012, t0 + dt, 0.3)


def pour(t0, t1, out, g=0.05):
    n = int((t1 - t0) * SR)
    tt = np.arange(n) / SR
    gur = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 9 * tt + 3 * np.sin(2 * np.pi * 1.3 * tt)))
    e = np.interp(tt, [0, 0.15, tt[-1] - 0.25, tt[-1]], [0, 1, 1, 0])
    sig = bp(rng.standard_normal(n), 500, 3200) * gur * e
    sig += bp(rng.standard_normal(n), 3000, 7000) * 0.3 * e
    place(out, sig * g, t0, 0.15)


def cloth(t0, out):
    n = int(0.9 * SR)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    flutter = 0.7 + 0.3 * np.sin(2 * np.pi * 11 * np.arange(n) / SR)
    place(out, lp(rng.standard_normal(n), 1400) * e * flutter * 0.08, t0, 0.4)


def page(t0, out):
    n = int(0.75 * SR)
    tt = np.arange(n) / SR
    e = np.interp(tt, [0, 0.12, 0.45, 0.75], [0, 1, 0.6, 0])
    crack = (rng.random(n) < 0.006) * rng.standard_normal(n) * 3
    place(out, bp(rng.standard_normal(n) + crack, 900, 8000) * e * 0.055, t0, -0.1)
    n = int(0.12 * SR)
    place(out, lp(rng.standard_normal(n), 600) * np.exp(-np.arange(n) / SR * 40) * 0.05, t0 + 0.8, -0.15)


def grass_whoosh(t0, out, dur=1.0, g=0.05):
    n = int(dur * SR)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    crack = (rng.random(n) < 0.004) * rng.standard_normal(n) * 4
    place(out, bp(rng.standard_normal(n) * 0.6 + crack, 1500, 7000) * e * g, t0, 0.0)


def breath(t0, out, dur=2.5):
    n = int(dur * SR)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    place(out, bp(rng.standard_normal(n), 300, 2400) * e * 0.02, t0, 0.0)


def boom(t0, out, g=0.10, crackle=False, pan=0.0):
    n = int(2.2 * SR)
    tt = np.arange(n) / SR
    body = lp(rng.standard_normal(n), 140) * np.exp(-tt * 2.4) * np.minimum(1, tt / 0.01) * 3
    thump = np.sin(2 * np.pi * 55 * tt * (1 - 0.3 * tt)) * np.exp(-tt * 6)
    place(out, (body + thump) * g, t0, pan)
    if crackle:
        m = int(1.4 * SR)
        cr = (rng.random(m) < 0.004) * rng.standard_normal(m) * 4
        place(out, hp(cr, 2500) * np.exp(-np.arange(m) / SR * 1.6) * 0.02, t0 + 0.35, -pan)


def chime(t0, out, g=0.016, pan=0.45):
    n = int(2.4 * SR)
    tt = np.arange(n) / SR
    f0 = 2380 * rng.uniform(0.985, 1.015)
    sig = sum(a * np.sin(2 * np.pi * f0 * r * tt + rng.random() * 6) * np.exp(-tt * d)
              for r, a, d in ((1.0, 1.0, 1.6), (2.76, 0.45, 3.0), (5.40, 0.2, 5.0), (0.5, 0.15, 2.0)))
    place(out, sig * np.minimum(1, tt / 0.002) * g, t0, pan)


def thunder(t0, out, g=0.16):
    n = int(3.5 * SR)
    tt = np.arange(n) / SR
    e = np.interp(tt, [0, 0.25, 0.9, 3.5], [0, 1, 0.6, 0]) * (0.7 + 0.3 * A.smooth_rand(n, 6, 9)[:n])
    place(out, lp(rng.standard_normal(n), 110) * e * g * 3, t0, -0.2)


def drips(t0, t1, out, g=0.02, seed=4):
    r = np.random.default_rng(seed)
    t = t0
    while t < t1:
        n = int(0.09 * SR)
        tt = np.arange(n) / SR
        f = r.uniform(900, 1800) * (1 + 1.8 * np.exp(-tt * 70))
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45)
        place(out, sig * g * r.uniform(0.5, 1), t, r.uniform(-0.6, 0.6))
        t += r.uniform(0.2, 0.7)


# ------------------------------------------------------------------ music
def music(chords, mel, harm, vel=1.0):
    m = np.zeros((2, N))
    start = T_RES - 4 * BAR
    for (bar, bass, upper) in chords:
        t0 = start + bar * BAR
        half = bar % 1 > 0
        place(m, felt_piano(hz(bass[0]), 4.5, 0.42 * vel), t0, -0.25)
        place(m, felt_piano(hz(bass[1]), 4.0, 0.26 * vel), t0 + BEAT * 1.5, -0.2)
        if not half:
            place(m, felt_piano(hz(upper[0]), 3.5, 0.22 * vel), t0 + BEAT * 3, -0.1)
    for (b, n, v) in mel:
        place(m, felt_piano(hz(n), 4.0, v * vel), start + b * BEAT, 0.15)
    for (n, v, pan) in (("F2", 0.40, -0.25), ("C3", 0.26, -0.2), ("A3", 0.22, 0.0), ("G4", 0.2, 0.15), ("A4", 0.24, 0.2)):
        place(m, felt_piano(hz(n), 3.0, v * vel), T_RES + (0.0 if n[-1] in "23" else 0.06), pan)
    place(m, vibes(hz("C6"), 2.4, 0.07), T_RES + 0.35, 0.35)
    for (b, n) in harm:
        place(m, guitar_harm(hz(n), 3.0, 0.05), start + b * BEAT, -0.45)
    place(m, guitar_harm(hz("C6"), 2.0, 0.04), T_RES + 0.7, -0.4)
    for (bar, bass, upper) in chords:
        nxt = [c[0] for c in chords if c[0] > bar]
        b1 = nxt[0] if nxt else 4.0
        sig = pad([hz(n) for n in upper], 0, (b1 - bar) * BAR, 0.05)
        place(m, sig, start + bar * BAR - 0.3, 0.0)
    place(m, pad([hz(n) for n in ("F3", "A3", "C4", "G4")], 0, 15.0 - T_RES, 0.055), T_RES - 0.2, 0.0)
    return reverb(m, 2.6, 0.32)


MUSIC = {
    1: ([(0, ["F2", "C3"], ["A3", "C4", "G4"]), (1, ["D2", "A2"], ["F3", "C4", "E4"]),
         (2, ["Bb1", "F2"], ["A3", "D4", "F4"]), (3, ["C3", "G3"], ["Bb3", "D4", "F4"]), (3.5, ["C3", "G3"], ["Bb3", "C4", "E4"])],
        [(1.0, "A4", 0.26), (2.0, "C5", 0.24), (3.5, "D5", 0.22), (5.0, "C5", 0.24), (6.5, "A4", 0.22), (8.0, "F5", 0.26),
         (9.0, "E5", 0.22), (10.5, "D5", 0.24), (12.0, "C5", 0.24), (13.5, "E5", 0.2), (14.5, "G5", 0.2)],
        [(1.0, "G5"), (9.0, "F5")]),
    2: ([(0, ["Bb1", "F2"], ["A3", "D4", "F4"]), (1, ["A2", "E3"], ["G3", "C4", "E4"]),
         (2, ["G2", "D3"], ["F3", "Bb3", "D4"]), (3, ["C3", "G3"], ["F3", "Bb3", "C4"])],
        [(1.0, "F4", 0.24), (2.5, "A4", 0.24), (4.0, "G4", 0.24), (5.5, "E4", 0.22), (8.0, "F4", 0.24), (9.5, "D4", 0.22),
         (11.0, "E4", 0.2), (12.5, "G4", 0.22), (14.0, "A4", 0.22)],
        [(2.0, "D5"), (10.0, "C5")]),
    3: ([(0, ["F2", "C3"], ["A3", "C4", "E4"]), (1, ["G2", "D3"], ["F3", "Bb3", "D4"]),
         (2, ["A2", "E3"], ["G3", "C4", "E4"]), (3, ["Bb1", "F2"], ["A3", "D4", "F4"])],
        [(2.0, "C5", 0.18), (6.0, "D5", 0.18), (10.0, "E5", 0.18), (12.0, "C5", 0.16), (14.0, "D5", 0.2)],
        [(4.0, "E5"), (12.5, "F5")]),
    4: ([(0, ["D2", "A2"], ["F3", "A3", "C4"]), (1, ["Bb1", "F2"], ["A3", "D4", "F4"]),
         (2, ["G2", "D3"], ["F3", "Bb3", "D4"]), (3, ["C3", "G3"], ["F3", "Bb3", "C4"])],
        [(1.0, "A4", 0.22), (2.5, "F4", 0.2), (4.0, "D5", 0.22), (6.0, "C5", 0.2), (8.0, "A4", 0.24), (9.5, "C5", 0.24),
         (11.0, "D5", 0.24), (12.5, "E5", 0.24), (14.0, "G5", 0.22)],
        [(9.0, "F5"), (12.5, "E5")]),
    5: ([(0, ["F2", "C3"], ["A3", "C4", "G4"]), (1, ["G2", "D3"], ["F3", "Bb3", "D4"]),
         (2, ["A2", "E3"], ["G3", "C4", "E4"]), (3, ["Bb1", "F2"], ["A3", "D4", "F4"]), (3.5, ["C3", "G3"], ["Bb3", "C4", "E4"])],
        [(1.0, "C4", 0.2), (2.0, "F4", 0.22), (4.0, "G4", 0.22), (5.0, "Bb4", 0.22), (8.0, "C5", 0.24), (9.0, "E5", 0.22),
         (11.0, "D5", 0.24), (12.0, "F5", 0.24), (13.0, "G5", 0.24), (14.0, "A5", 0.22)],
        [(1.0, "C5"), (9.0, "G5")]),
}


def build(n):
    import batch2
    reel = batch2.REELS[n]
    amb = np.zeros((2, N))
    fx = np.zeros((2, N))
    calm = np.interp(t_all, [0, 12.0, 13.4, 15], [1, 1, 0.72, 0.68])
    mvel = 1.0
    if n == 1:
        amb += wind() + cicadas()
        for t0 in (1.1, 9.8, 11.5):
            grass_whoosh(t0, fx, 1.3)
        freewheel(3.0, 5.6, fx)
        bell(4.3, fx, -0.3, 0.016)
        click(5.75, fx, (1500, 5000), 0.12, -0.3)
        cloth(5.85, fx)
        ceramic(6.6, fx)
        pour(7.05, 8.3, fx)
        breath(9.7, fx)
        grass_whoosh(11.2, fx, 1.0, 0.06)
    elif n == 2:
        amb += wind(0.8) + higurashi([(0.3, -0.5, 1.0), (3.6, 0.55, 0.8), (8.0, -0.3, 0.7), (11.6, 0.4, 0.6)])
        cloth(4.15, fx)
        ice(4.85, fx)
        ceramic(5.0, fx, 0.016, -0.2, 1900)
        page(5.5, fx)
        grass_whoosh(10.2, fx, 1.0, 0.06)
        click(11.0, fx, (1200, 4000), 0.08, -0.5)
        breath(8.9, fx)
    elif n == 3:
        amb += wind(0.45) + crickets()
        for (t0, x, y, R, ci, life) in reel.fireworks:
            pan = (x - 540) / 600
            boom(t0 + 0.6, fx, 0.08 + 0.0004 * R, crackle=ci in (0, 2), pan=pan)
        for t0 in (3.9, 5.2, 6.4, 7.6, 8.9, 10.4, 13.6):
            chime(t0, fx)
        grass_whoosh(10.2, fx, 1.0, 0.04)
        mvel = 0.9
    elif n == 4:
        amb += wind(0.7) + rain(reel.rain)
        thunder(0.9, fx)
        thunder(4.6, fx, 0.12)
        drips(0.0, 11.5, fx)
        freewheel(3.5, 5.6, fx, -0.5)
        freewheel(3.9, 6.0, fx, -0.2, 0.04)
        bell(4.0, fx, -0.5, 0.012)
        click(5.6, fx, (1500, 5000), 0.1, -0.4)
        click(6.0, fx, (1500, 5000), 0.1, -0.2)
        ceramic(6.4, fx)
        ceramic(6.75, fx, 0.018, -0.1, 2050)
        amb += birds([9.8, 10.9, 12.3, 13.8], 0.8) + cicadas(0.6) * np.clip((t_all - 10) / 2, 0, 1)
        grass_whoosh(10.9, fx, 1.0, 0.06)
    elif n == 5:
        amb += wind(0.6) + birds([0.6, 1.5, 2.6, 4.1, 5.3, 7.0, 8.2, 10.1, 11.4, 12.9, 14.1], 1.0)
        ceramic(3.6, fx, 0.014, -0.3, 2600)
        ceramic(6.3, fx, 0.016, 0.2, 2300)
        pour(9.1, 9.9, fx)
        breath(9.3, fx)
        grass_whoosh(10.6, fx, 1.0, 0.06)
    mu = music(*MUSIC[n], vel=mvel)
    mix = amb * calm * 2.4 + reverb(fx, 1.4, 0.18, 6000, 7) * 2.6 + mu * 0.17
    mix *= np.minimum(1, t_all / 0.06)
    mix = mix / np.max(np.abs(mix)) * 0.7
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16).T.copy()
    path = f"{BUILD}/b2_{n}/audio.wav"
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", path)


if __name__ == "__main__":
    build(int(sys.argv[1]))
