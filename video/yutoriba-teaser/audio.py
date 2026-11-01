"""Synthesize the 15s soundtrack: soft piano loop, a few koto plucks,
distant train, cafe murmur, spoon against cup, city hush. numpy only.
Usage: python3 audio.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR


def midi_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def band(x, lo, hi, soft=0.15):
    """Zero-phase band-pass in the frequency domain with soft edges."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo > 0:
        m *= 1 / (1 + np.exp(-(np.log(f + 1e-9) - np.log(lo)) / soft))
    if hi < SR / 2:
        m *= 1 / (1 + np.exp((np.log(f + 1e-9) - np.log(hi)) / soft))
    return np.fft.irfft(X * m, len(x))


def env_pts(pts):
    """piecewise-linear envelope from [(t, v), ...]"""
    ts, vs = zip(*pts)
    return np.interp(t_all, ts, vs)


def add(buf, sig, start):
    i = max(0, int(start * SR))
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


# ---------------------------------------------------------------- piano
def piano_note(m, vel, length=6.0):
    f0 = midi_hz(m)
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    B = 0.00035
    bright = 0.5 + 0.5 * vel
    for h in range(1, 13):
        fh = f0 * h * np.sqrt(1 + B * h * h)
        if fh > 12000:
            break
        amp = (1 / h ** 1.25) * (bright ** (h - 1))
        tau = 3.2 * (220 / f0) ** 0.35 / (1 + 0.35 * (h - 1))
        for det in (-0.7, 0.7):  # two strings, a few cents apart
            ph = rng.uniform(0, 2 * np.pi)
            out += 0.5 * amp * np.sin(2 * np.pi * fh * (1 + det * 0.0006) * t + ph) * np.exp(-t / tau)
    # soft attack
    att = np.minimum(1, t / 0.006)
    out *= att
    # felt hammer thump
    thump = band(rng.standard_normal(int(0.04 * SR)), 80, 900) * np.exp(-np.arange(int(0.04 * SR)) / SR / 0.01)
    out[:len(thump)] += thump * 0.15
    # damper release near the end
    rel = np.ones(n)
    k = int((length - 0.6) * SR)
    rel[k:] = np.linspace(1, 0, n - k)
    return out * rel * vel * 0.18


BEAT = 60 / 72
BAR = 4 * BEAT  # 3.333s
chords = [
    # bass, voicing (arp order)
    (38, [50, 57, 64, 66, 69, 73]),   # Dmaj9
    (47, [54, 59, 62, 66, 69, 73]),   # Bm(add9)
    (43, [50, 55, 59, 66, 69, 71]),   # Gmaj7
    (45, [52, 57, 61, 64, 69, 71]),   # A6sus-ish
]
piano = np.zeros(N + SR * 8)
pattern = [(0.0, 0), (0.5, 1), (1.0, 3), (1.5, 2), (2.0, 4), (2.5, 3), (3.0, 5), (3.5, 2)]
for bi, (bass, v) in enumerate(chords):
    t0 = bi * BAR
    add(piano, piano_note(bass, 0.55, 7.0), t0)
    add(piano, piano_note(bass + 12, 0.35, 7.0), t0 + 0.01)
    for beat, idx in pattern:
        hum = rng.uniform(-0.015, 0.015)
        vel = 0.33 + 0.12 * (beat == 0) + rng.uniform(-0.04, 0.04)
        add(piano, piano_note(v[idx], vel, 5.0), t0 + beat * BEAT + hum)
# a quiet melody line on top
melody = [(1.5, 78, 0.38), (3.0, 76, 0.32), (5.4, 74, 0.36), (6.6, 73, 0.30),
          (8.2, 78, 0.36), (9.4, 79, 0.30), (10.6, 76, 0.34), (11.8, 73, 0.30)]
for st, m, vel in melody:
    add(piano, piano_note(m, vel, 4.0), st)
# final resolving chord on the wordmark (lets ring)
final_t = 13.33
for i, m in enumerate([38, 50, 57, 62, 66, 69, 76]):
    add(piano, piano_note(m, 0.42 if i else 0.5, 6.0), final_t + i * 0.035)
piano = piano[:N]

# ---------------------------------------------------------------- koto (Karplus-Strong)
def koto(m, vel, length=3.5):
    f0 = midi_hz(m)
    n = int(length * SR)
    p = int(SR / f0)
    buf = rng.uniform(-1, 1, p) * np.hanning(p) ** 0.3
    out = np.zeros(n)
    out[:p] = buf
    damp = 0.996
    for i in range(p, n):
        out[i] = damp * 0.5 * (out[i - p] + out[i - p - 1 if i - p - 1 >= 0 else 0])
    # plectrum brightness + slight pitch bend feel via tremolo
    out = band(out, 120, 7000)
    return out / (np.abs(out).max() + 1e-9) * vel


kt = np.zeros(N + SR * 4)
for st, m, vel in [(0.25, 74, 0.10), (0.55, 81, 0.07), (6.05, 78, 0.09), (6.35, 81, 0.06),
                   (12.05, 76, 0.08), (13.9, 81, 0.07), (14.15, 86, 0.05)]:
    add(kt, koto(m, vel), st)
kt = kt[:N]

# ---------------------------------------------------------------- ambience
def noise(n=N):
    return rng.standard_normal(n)

# city hush (pink-ish, low)
hush = band(noise(), 60, 700, 0.3)
hush /= np.abs(hush).max()
hush *= env_pts([(0, 0.05), (3, 0.05), (3.4, 0.025), (6, 0.025), (6.4, 0.06), (9, 0.06), (9.4, 0.03),
                 (12, 0.03), (12.4, 0.07), (13.6, 0.06), (14.5, 0.02), (15, 0.0)])

# distant train passing (0-4s): rumble + faint wheel clacks
rumble = band(noise(), 30, 220, 0.25)
rumble /= np.abs(rumble).max()
rumble *= env_pts([(0, 0.0), (0.4, 0.05), (1.6, 0.11), (2.8, 0.08), (4.2, 0.0), (15, 0)])
clacks = np.zeros(N)
for k in range(10):
    st = 0.6 + k * 0.32 + (0.09 if k % 2 else 0)
    c = band(noise(int(0.06 * SR)), 100, 900) * np.exp(-np.arange(int(0.06 * SR)) / SR / 0.012)
    add(clacks, c * 0.05 * np.sin(np.pi * k / 10) ** 1.2, st)
clacks = band(clacks, 80, 1200)

# cafe murmur (soft voices-ish noise) scenes 2 & 4
murmur = band(noise(), 250, 1400, 0.2)
mod = band(noise(), 0.3, 4, 0.5)
mod = 0.6 + 0.4 * mod / np.abs(mod).max()
murmur = murmur / np.abs(murmur).max() * mod
murmur *= env_pts([(0, 0), (2.7, 0), (3.3, 0.035), (5.8, 0.035), (6.3, 0.0), (8.7, 0), (9.3, 0.04), (11.8, 0.04), (12.3, 0), (15, 0)])

# spoon against cup
def clink(vel):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f, a, tau in [(2650, 1.0, 0.35), (3980, 0.6, 0.22), (5770, 0.45, 0.16), (7420, 0.3, 0.1), (1320, 0.25, 0.25)]:
        s += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / tau)
    s[:int(0.002 * SR)] *= np.linspace(0, 1, int(0.002 * SR))
    return s * vel


spoon = np.zeros(N)
add(spoon, clink(0.05), 4.55)
add(spoon, clink(0.03), 4.78)
add(spoon, clink(0.012), 10.4)

# dusk breeze
breeze = band(noise(), 200, 2500, 0.4)
breeze /= np.abs(breeze).max()
breeze *= env_pts([(0, 0), (6, 0), (6.5, 0.02), (8.8, 0.02), (9.2, 0), (12, 0), (12.5, 0.025), (14.2, 0.015), (15, 0)])

# ---------------------------------------------------------------- reverb
def reverb(x, secs=2.4, wet=0.35, seed=0):
    r = np.random.default_rng(seed)
    n = int(secs * SR)
    ir = r.standard_normal(n) * np.exp(-np.arange(n) / SR / (secs / 6.9))
    ir = band(ir, 150, 6000)
    ir[:int(0.012 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    L = len(x) + n
    nfft = 1 << (L - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:len(x)]
    return x * (1 - wet) + y * wet * 3.0


music = piano * 1.0 + kt * 0.8
musL = reverb(music, 2.6, 0.38, 1)
musR = reverb(music, 2.6, 0.38, 2)
spL = reverb(spoon, 1.2, 0.3, 3)
spR = reverb(spoon, 1.2, 0.3, 4)
amb = hush + rumble + clacks + breeze
ambR = np.roll(amb, 311)
mur = murmur

L = musL + 0.9 * amb + mur + spL * 1.0
R = musR + 0.9 * ambR + np.roll(mur, 157) + spR * 0.85

# gentle high-pass to keep the low end clean
L = band(L, 38, SR / 2, 0.2)
R = band(R, 38, SR / 2, 0.2)

# master envelope: gentle fade in/out
master = env_pts([(0, 0), (0.6, 1), (14.2, 1), (15, 0)])
L *= master
R *= master
st = np.stack([L, R], 1)
st /= np.abs(st).max()
st *= 10 ** (-3 / 20)

pcm = (st * 32767).astype(np.int16)
out = sys.argv[1] if len(sys.argv) > 1 else 'audio.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out)
