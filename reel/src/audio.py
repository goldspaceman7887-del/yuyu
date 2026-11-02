"""Synthesises the original 15.0 s soundtrack (48 kHz stereo) -> build/audio.wav

Ambience (slightly forward): wind in grass, distant cicadas, leaves, one bird,
one distant bicycle bell, a wood creak, a ceramic touch, the page turn, cloth.
Music (original): felt piano + guitar harmonics + warm pad, 72 BPM in F major,
Fmaj9 | Am7 | Bbmaj7 | Gm7 C7sus4 | Fadd9 (resolves as ゆとりば appears at 13.33 s).
"""
import math
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

from common import BUILD, DUR

SR = 48000
N = int(SR * DUR)
rng = np.random.default_rng(2024)
t_all = np.arange(N) / SR


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def smooth_rand(n, rate, seed):
    r = np.random.default_rng(seed)
    k = max(4, int(DUR * rate) + 4)
    pts = r.random(k)
    return np.interp(np.linspace(0, k - 3, n), np.arange(k), pts)


def place(buf, sig, t0, pan=0.0, gain=1.0):
    i0 = int(t0 * SR)
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    if i0 >= N:
        return
    sig = sig[: N - i0]
    l = math.cos((pan + 1) * math.pi / 4)
    r = math.sin((pan + 1) * math.pi / 4)
    buf[0, i0:i0 + len(sig)] += sig * gain * l * 1.414
    buf[1, i0:i0 + len(sig)] += sig * gain * r * 1.414


def reverb(stereo, seconds=2.4, wet=0.25, damp=5000, seed=1):
    out = np.zeros_like(stereo)
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    for ch in range(2):
        r = np.random.default_rng(seed + ch)
        ir = r.standard_normal(n) * np.exp(-tt * 6.9 / seconds)
        ir = lp(ir, damp)
        ir[: int(0.012 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = fftconvolve(stereo[ch], ir)[:N]
    return stereo * (1 - wet) + out * wet * 1.6


# ------------------------------------------------------------------ ambience
def ambience():
    amb = np.zeros((2, N))
    # wind: brown-ish rumble + grass hiss, both following slow gusts
    gust = 0.55 + 0.45 * smooth_rand(N, 0.5, 3)
    for ch in range(2):
        w = rng.standard_normal(N)
        low = lp(w, 380) * 2.2
        hiss = bp(rng.standard_normal(N), 1800, 6500) * 0.55
        g2 = 0.55 + 0.45 * smooth_rand(N, 0.9, 10 + ch)
        amb[ch] += (low * gust + hiss * gust * g2) * 0.11
    # calmer at the very end (the scene becomes almost still)
    calm = np.interp(t_all, [0, 12.4, 13.6, 15], [1, 1, 0.72, 0.68])
    amb *= calm
    # distant cicadas (two, panned), band-limited and soft
    for (pan, f0, ph, g) in ((-0.55, 4300, 0.0, 1.0), (0.6, 3700, 1.7, 0.7)):
        carrier = bp(rng.standard_normal(N), f0 - 500, f0 + 500, 2)
        pulse = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 95 * t_all + ph))
        phrase = 0.55 + 0.45 * np.sin(2 * np.pi * 0.23 * t_all + ph) ** 2
        mm = 0.7 + 0.3 * np.sin(2 * np.pi * 3.6 * t_all + ph)
        sig = lp(carrier * pulse, 6000) * phrase * mm
        place(amb, sig * 0.010 * g, 0, pan)
    # leaves rustling in a few gusts
    for (t0, dur, pan) in ((1.1, 1.4, -0.4), (4.0, 1.2, 0.5), (9.6, 1.6, -0.2), (12.2, 1.3, 0.3)):
        n = int(dur * SR)
        e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
        crack = (rng.random(n) < 0.004) * rng.standard_normal(n) * 4
        sig = bp(rng.standard_normal(n) * 0.6 + crack, 1500, 7000) * e
        place(amb, sig * 0.05, t0, pan)
    return amb


def sfx():
    s = np.zeros((2, N))
    # one distant bird (two soft syllables)
    for k, t0 in enumerate((2.15, 2.42)):
        n = int(0.16 * SR)
        tt = np.arange(n) / SR
        f = np.where(tt < 0.08, 2900 + 9000 * tt, 3620 - 5000 * (tt - 0.08)) if k == 0 else 3300 - 4000 * tt
        ph = 2 * np.pi * np.cumsum(f) / SR
        e = np.sin(np.pi * tt / tt[-1]) ** 2
        sig = (np.sin(ph) + 0.2 * np.sin(2 * ph)) * e
        place(s, lp(sig, 5000) * 0.022, t0, 0.45)
    # very distant bicycle bell, once (two quick strikes)
    for t0 in (4.25, 4.37):
        n = int(1.1 * SR)
        tt = np.arange(n) / SR
        sig = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d)
                  for f, a, d in ((2950, 1.0, 4.0), (4130, 0.6, 5.5), (6280, 0.3, 8.0), (7710, 0.15, 10)))
        sig *= np.minimum(1, tt / 0.002)
        place(s, lp(sig, 5200) * 0.012, t0, -0.3)
    # soft wooden creak of the stand
    n = int(0.55 * SR)
    clicks = np.zeros(n)
    pos, rate = 0.0, 55.0
    while pos < n - 10:
        clicks[int(pos)] = rng.uniform(0.6, 1.0)
        rate = max(30, min(90, rate + rng.normal(0, 6)))
        pos += SR / rate
    sig = bp(clicks, 280, 900, 2) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    place(s, sig * 0.22, 5.15, 0.15)
    # cloth flutter as the banner crosses the lens
    n = int(0.9 * SR)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    flutter = 0.7 + 0.3 * np.sin(2 * np.pi * 11 * np.arange(n) / SR)
    place(s, lp(rng.standard_normal(n), 1400) * e * flutter * 0.08, 5.8, 0.4)
    # quiet ceramic touch (cup on saucer)
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    sig = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d)
              for f, a, d in ((2210, 1.0, 14), (3870, 0.5, 18), (5630, 0.25, 24)))
    sig += lp(rng.standard_normal(n), 400) * np.exp(-tt * 60) * 0.6
    place(s, sig * 0.02, 6.32, 0.2)
    # page turn: paper swish with tiny crackles, then a soft landing
    n = int(0.75 * SR)
    tt = np.arange(n) / SR
    e = np.interp(tt, [0, 0.12, 0.45, 0.75], [0, 1, 0.6, 0])
    crack = (rng.random(n) < 0.006) * rng.standard_normal(n) * 3
    sig = bp(rng.standard_normal(n) + crack, 900, 8000) * e
    place(s, sig * 0.055, 6.95, -0.1)
    n = int(0.12 * SR)
    place(s, lp(rng.standard_normal(n), 600) * np.exp(-np.arange(n) / SR * 40) * 0.05, 7.78, -0.15)
    # a breath of air as the steam rises toward the cloud
    n = int(2.5 * SR)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    place(s, bp(rng.standard_normal(n), 300, 2400) * e * 0.02, 9.7, 0.0)
    return s


# ------------------------------------------------------------------ music
BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "Ab": 8,
        "A": 9, "Bb": 10, "B": 11}


def hz(name):
    n, o = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((NOTE[n] + 12 * (o + 1) - 69) / 12)


def felt_piano(f, dur, vel):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    B = 0.00035
    for k in range(1, 11):
        fk = k * f * math.sqrt(1 + B * k * k)
        if fk > 9000:
            break
        amp = (1 / k ** 1.5) * (1.0 if k == 1 else 0.85)
        decay = 0.55 + 0.35 * k + f / 900
        sig += amp * np.sin(2 * np.pi * fk * tt + k) * np.exp(-tt * decay)
    att = np.minimum(1, tt / 0.012)
    thump = lp(rng.standard_normal(n), 300) * np.exp(-tt * 45) * 0.05
    sig = (sig * att + thump) * vel
    return lp(sig, 2600 + 1400 * vel)  # the felt


def guitar_harm(f, dur, vel):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * f * tt) + 0.15 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 1.6)
    return sig * np.minimum(1, tt / 0.003) * vel


def vibes(f, dur, vel):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 4 * f * tt) * np.exp(-tt * 6)) * np.exp(-tt * 0.9)
    trem = 1 - 0.18 * (0.5 + 0.5 * np.sin(2 * np.pi * 5.2 * tt))
    return sig * trem * np.minimum(1, tt / 0.004) * vel


def pad(freqs, t0, t1, vel):
    n = int((t1 - t0 + 1.5) * SR)
    tt = np.arange(n) / SR
    sig = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.12):
            sig += np.sin(2 * np.pi * f * (1 + det / 100) * tt + rng.random() * 6)
            sig += 0.3 * np.sin(2 * np.pi * 2 * f * (1 + det / 100) * tt)
    env = np.interp(tt, [0, 1.4, t1 - t0, t1 - t0 + 1.5], [0, 1, 1, 0])
    return lp(sig, 1200) * env * vel / len(freqs)


def music():
    m = np.zeros((2, N))
    start = 0.25
    chords = [
        (0, ["F2", "C3"], ["A3", "C4", "E4", "G4"]),
        (1, ["A2", "E3"], ["G3", "C4", "E4"]),
        (2, ["Bb1", "F2"], ["A3", "D4", "F4"]),
        (3, ["G2", "D3"], ["F3", "Bb3", "D4"]),
        (3.5, ["C3", "G3"], ["F3", "Bb3", "C4"]),
    ]
    # left-hand pattern: bass on 1, open fifth on the "and" of 2, a chord tone on 4
    for (bar, bass, upper) in chords:
        t0 = start + bar * BAR
        half = bar % 1 > 0
        place(m, felt_piano(hz(bass[0]), 4.5, 0.42), t0, -0.25)
        place(m, felt_piano(hz(bass[1]), 4.0, 0.26), t0 + BEAT * 1.5, -0.2)
        if not half:
            place(m, felt_piano(hz(upper[0]), 3.5, 0.22), t0 + BEAT * 3, -0.1)
    # original, sparse right-hand melody (beats from start)
    mel = [
        (0.0, "C5", 0.30), (2.0, "A4", 0.24), (3.5, "G4", 0.22),
        (4.0, "E4", 0.26), (6.0, "G4", 0.24), (7.0, "C5", 0.22),
        (8.0, "D5", 0.28), (9.5, "C5", 0.22), (10.5, "A4", 0.24),
        (12.0, "Bb4", 0.24), (13.0, "A4", 0.22), (14.0, "G4", 0.22),
    ]
    for (b, n, v) in mel:
        place(m, felt_piano(hz(n), 4.0, v), start + b * BEAT, 0.15)
    # resolution on Fadd9 exactly when ゆとりば appears (bar 5 downbeat = 13.58 s - 0.25 lead)
    t_res = 13.3
    for (n, v, pan) in (("F2", 0.40, -0.25), ("C3", 0.26, -0.2), ("A3", 0.22, 0.0), ("G4", 0.2, 0.15), ("A4", 0.24, 0.2)):
        place(m, felt_piano(hz(n), 3.0, v), t_res + (0.0 if n[-1] in "23" else 0.06), pan)
    place(m, vibes(hz("C6"), 2.4, 0.07), t_res + 0.35, 0.35)
    # guitar harmonics, very light
    for (b, n) in ((1.0, "E5"), (9.0, "F5"), (12.5, "D5")):
        place(m, guitar_harm(hz(n), 3.0, 0.05), start + b * BEAT, -0.45)
    place(m, guitar_harm(hz("C6"), 2.0, 0.04), t_res + 0.7, -0.4)
    # warm ambient pad following the harmony
    pads = [(0, 1, ["F3", "A3", "C4", "E4"]), (1, 2, ["E3", "A3", "C4", "G4"]), (2, 3, ["F3", "A3", "D4"]),
            (3, 3.5, ["G3", "Bb3", "D4"]), (3.5, 4.0, ["G3", "Bb3", "C4"])]
    for (b0, b1, notes) in pads:
        sig = pad([hz(n) for n in notes], 0, (b1 - b0) * BAR, 0.05)
        place(m, sig, start + b0 * BAR - 0.3, 0.0)
    place(m, pad([hz(n) for n in ("F3", "A3", "C4", "G4")], 0, DUR - t_res, 0.055), t_res - 0.2, 0.0)
    return reverb(m, 2.6, 0.32)


def main():
    amb = ambience()
    fx = sfx()
    mu = music()
    mix = amb * 2.4 + reverb(fx, 1.4, 0.18, 6000, 7) * 2.6 + mu * 0.17
    # gentle fade-in on the first 60 ms only; no fade-out (the final frame holds)
    fade = np.minimum(1, t_all / 0.06)
    mix *= fade
    peak = np.max(np.abs(mix))
    mix = mix / peak * 0.7
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16).T.copy()
    with wave.open(f"{BUILD}/audio.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote audio.wav", pcm.shape[0] / SR, "s")


if __name__ == "__main__":
    main()
