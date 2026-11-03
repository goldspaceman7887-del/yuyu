"""Synthesises an original soundtrack for each reel -> reels/build/<name>_audio.wav (48 kHz stereo)

Ambience follows the picture: train interior (rumble + rail joints) under the train shots,
cafe room tone (low murmur, a cup set down) under the cafe shots, crossfaded with the picture.
Music: felt piano + soft pad + guitar harmonics, slow (66-72 BPM), no drums, no vocals.
Each reel has its own key and progression and resolves when the ゆとりば card appears.
"""
import math
import os
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "reel", "src"))
from audio import felt_piano, guitar_harm, vibes, pad, hz  # noqa: E402  (instrument voices from reel 1)

from reels import REELS, XF  # noqa: E402

SR = 48000
BUILD = os.path.join(ROOT, "build")

MUSIC = {
    "01_kotoba": dict(bpm=70, chords=[
        (["D2", "A2"], ["F#3", "A3", "C#4", "E4"]),     # Dmaj9
        (["B1", "F#2"], ["A3", "D4", "F#4"]),           # Bm7
        (["G1", "D2"], ["F#3", "B3", "D4"]),            # Gmaj7
        (["A1", "E2"], ["G3", "D4", "E4"]),             # A7sus4
    ], resolve=(["D2", "A2"], ["F#3", "A3", "E4", "F#4"]),
        mel=["A4", "F#4", "E4", "D4", "F#4", "A4", "B4", "A4", "F#4", "G4", "F#4", "E4"], seed=11),
    "02_sonosaki": dict(bpm=66, chords=[
        (["A1", "E2"], ["G3", "C4", "E4", "B4"]),       # Am9
        (["F1", "C2"], ["E3", "A3", "C4"]),             # Fmaj7
        (["C2", "G2"], ["E3", "G3", "C4", "D4"]),       # Cadd9
        (["G1", "D2"], ["F3", "B3", "D4", "E4"]),       # G6/G7
    ], resolve=(["F1", "C2"], ["E3", "A3", "C4", "G4"]),   # Fmaj9: open, unfinished, hopeful
        mel=["E4", "C5", "B4", "A4", "G4", "A4", "E4", "G4", "D5", "C5", "B4", "D4"], seed=23),
    "03_konomachi": dict(bpm=68, chords=[
        (["E2", "B2"], ["G3", "B3", "D4", "F#4"]),      # Em9
        (["C2", "G2"], ["E3", "B3", "D4"]),             # Cmaj9
        (["G1", "D2"], ["F#3", "B3", "D4"]),            # Gmaj7
        (["D2", "A2"], ["F#3", "A3", "E4"]),            # Dadd9
    ], resolve=(["G1", "D2"], ["B3", "D4", "F#4", "A4"]),  # Gmaj9 - comes home
        mel=["B4", "G4", "F#4", "E4", "D4", "E4", "G4", "F#4", "A4", "G4", "F#4", "D4"], seed=37),
}


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


class Mix:
    def __init__(self, dur):
        self.N = int(SR * dur)
        self.buf = np.zeros((2, self.N))

    def place(self, sig, t0, pan=0.0, gain=1.0, buf=None):
        b = self.buf if buf is None else buf
        i0 = int(t0 * SR)
        if i0 < 0:
            sig, i0 = sig[-i0:], 0
        if i0 >= self.N:
            return
        sig = sig[: self.N - i0]
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        b[0, i0:i0 + len(sig)] += sig * gain * l * 1.414
        b[1, i0:i0 + len(sig)] += sig * gain * r * 1.414


def reverb(stereo, seconds=2.4, wet=0.25, damp=5000, seed=1):
    n_out = stereo.shape[1]
    out = np.zeros_like(stereo)
    n = int(seconds * SR)
    tt = np.arange(n) / SR
    for ch in range(2):
        r = np.random.default_rng(seed + ch)
        ir = r.standard_normal(n) * np.exp(-tt * 6.9 / seconds)
        ir = lp(ir, damp)
        ir[: int(0.012 * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out[ch] = fftconvolve(stereo[ch], ir)[:n_out]
    return stereo * (1 - wet) + out * wet * 1.6


# ------------------------------------------------------------------ ambience beds
def train_bed(N, rng):
    tt = np.arange(N) / SR
    rumble = lp(rng.standard_normal(N), 140, 3) * 1.4 + bp(rng.standard_normal(N), 180, 600) * 0.25
    sway = 0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * tt)
    st = np.stack([rumble * sway, np.roll(rumble, 400) * sway])
    # rail joints: a pair of soft "ta-tan" clacks every ~1.6 s
    clack = np.zeros(N)
    k = int(0.09 * SR)
    kt = np.arange(k) / SR
    hit = lp(rng.standard_normal(k), 900) * np.exp(-kt * 38) + 0.6 * np.sin(2 * np.pi * 70 * kt) * np.exp(-kt * 25)
    t = 0.35
    while t < N / SR:
        for dt, g in ((0.0, 1.0), (0.17, 0.8)):
            i = int((t + dt) * SR)
            if i + k < N:
                clack[i:i + k] += hit * g
        t += 1.55 + rng.random() * 0.15
    st += np.stack([clack, np.roll(clack, 200)]) * 0.35
    return st * 0.22


def cafe_bed(N, rng):
    tt = np.arange(N) / SR
    room = lp(rng.standard_normal(N), 500) * 0.35 + bp(rng.standard_normal(N), 250, 1200) * 0.10
    # far-away murmur: band-limited noise with syllable-rate envelope
    env = np.interp(np.arange(N), np.arange(0, N, 2400), rng.random(len(range(0, N, 2400))))
    mur = bp(rng.standard_normal(N), 300, 900) * (0.4 + 0.6 * env) * 0.18
    st = np.stack([room + mur, np.roll(room, 300) + np.roll(mur, 900)])
    return st * 0.30


def cup_clink(rng):
    n = int(0.6 * SR)
    tt = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, a, d in
            ((2310, 1.0, 14), (3480, 0.6, 20), (5120, 0.3, 30)))
    s += lp(rng.standard_normal(n), 3000) * np.exp(-tt * 120) * 0.5
    return s * 0.05


def page_turn(rng):
    n = int(0.7 * SR)
    tt = np.arange(n) / SR
    env = np.interp(tt, [0, 0.08, 0.3, 0.7], [0, 1, 0.5, 0])
    return bp(rng.standard_normal(n), 1500, 7000) * env * 0.06


def ambience(name, mix, rng):
    shots = REELS[name]["shots"]
    starts, s = [], 0.0
    for sh in shots:
        starts.append(s)
        s += sh["dur"] - XF
    tt = np.arange(mix.N) / SR
    beds = {"train": train_bed(mix.N, rng), "cafe": cafe_bed(mix.N, rng)}
    kind = {"T": "train", "P": "train", "C": "cafe", "M": "cafe"}
    gains = {"train": np.zeros(mix.N), "cafe": np.zeros(mix.N)}
    for k, (sh, s0) in enumerate(zip(shots, starts)):
        a = np.clip((tt - s0) / XF, 0, 1) if k else np.ones(mix.N)
        e = s0 + sh["dur"]
        b = np.clip((e - tt) / XF, 0, 1) if k < len(shots) - 1 else np.ones(mix.N)
        w = np.minimum(a, b) * (tt >= s0 - 0.01)
        gains[kind[sh["src"]]] = np.maximum(gains[kind[sh["src"]]], w)
    out = sum(beds[k] * np.sqrt(gains[k])[None] for k in beds)
    # spot effects
    for sh, s0 in zip(shots, starts):
        if sh["src"] == "M":
            mix.place(cup_clink(rng), s0 + 0.9, 0.25, buf=out)
            if name == "01_kotoba":
                mix.place(page_turn(rng), s0 + 2.6, 0.1, buf=out)
        if sh["src"] == "C" and name != "01_kotoba":
            mix.place(cup_clink(rng), s0 + 1.6, -0.3, gain=0.6, buf=out)
    # the room settles under the closing card
    t_close = [b["t"] for b in REELS[name]["text"] if b["kind"] == "close"][0]
    out *= np.interp(tt, [0, t_close, t_close + 2.5, 99], [1, 1, 0.55, 0.55])[None]
    return out


# ------------------------------------------------------------------ music
def music(name, mix, rng):
    spec = MUSIC[name]
    beat = 60 / spec["bpm"]
    bar = 4 * beat
    m = np.zeros_like(mix.buf)
    t_brand = [b["t"] for b in REELS[name]["text"] if b["kind"] == "brand"][0]
    start = 0.15
    i, t = 0, start
    # loop the progression until the resolution at the brand card
    while t + bar <= t_brand + 0.3:
        bass, upper = spec["chords"][i % len(spec["chords"])]
        mix.place(felt_piano(hz(bass[0]), 4.5, 0.42), t, -0.25, buf=m)
        mix.place(felt_piano(hz(bass[1]), 4.0, 0.26), t + beat * 1.5, -0.2, buf=m)
        mix.place(felt_piano(hz(upper[0]), 3.5, 0.2), t + beat * 3, -0.1, buf=m)
        mix.place(pad([hz(n) for n in upper], 0, bar, 0.05), t - 0.3, 0.0, buf=m)
        # sparse melody: three notes a bar, one rest
        mel = spec["mel"]
        for j, b in enumerate((0.0, 1.5, 2.5) if i % 2 == 0 else (0.5, 2.0)):
            n = mel[(i * 3 + j) % len(mel)]
            mix.place(felt_piano(hz(n), 3.6, 0.2 + 0.05 * rng.random()), t + b * beat + rng.random() * 0.02, 0.15,
                      buf=m)
        if i % 2 == 1:
            mix.place(guitar_harm(hz(upper[-1]) * 2, 3.0, 0.045), t + beat * 3.5, -0.45, buf=m)
        i += 1
        t += bar
    # resolution exactly as ゆとりば appears
    bass, upper = spec["resolve"]
    t_res = t_brand
    for n, v, p in ((bass[0], 0.40, -0.25), (bass[1], 0.26, -0.2)):
        mix.place(felt_piano(hz(n), 4.0, v), t_res, p, buf=m)
    for j, n in enumerate(upper):
        mix.place(felt_piano(hz(n), 4.0, 0.2), t_res + 0.05 + 0.07 * j, 0.1, buf=m)
    mix.place(vibes(hz(upper[-1]) * 2, 2.6, 0.07), t_res + 0.4, 0.35, buf=m)
    mix.place(pad([hz(n) for n in upper], 0, mix.N / SR - t_res, 0.055), t_res - 0.2, 0.0, buf=m)
    return reverb(m, 2.6, 0.32)


def make(name, dur):
    rng = np.random.default_rng(sum(map(ord, name)))
    mix = Mix(dur)
    amb = ambience(name, mix, rng)
    mu = music(name, mix, rng)
    out = amb * 1.4 + mu * 0.2
    tt = np.arange(mix.N) / SR
    out *= np.minimum(1, tt / 0.05)[None]
    out *= np.interp(tt, [0, dur - 0.8, dur], [1, 1, 0.2])[None]  # soft tail
    out = out / np.max(np.abs(out)) * 0.7
    pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16).T.copy()
    p = os.path.join(BUILD, f"{name}_audio.wav")
    with wave.open(p, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print("wrote", p, f"{dur:.2f} s")


def reel_duration(name):
    shots = REELS[name]["shots"]
    return sum(sh["dur"] for sh in shots) - XF * (len(shots) - 1)


if __name__ == "__main__":
    for nm in (sys.argv[1:] or list(REELS)):
        make(nm, reel_duration(nm))
