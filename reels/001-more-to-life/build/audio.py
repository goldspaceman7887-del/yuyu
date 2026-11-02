"""ゆとりば Reel 001 — synthesized 15 s soundtrack following production-package.md §12.
Felt piano + environmental sound. Writes soundtrack_raw.wav (48 kHz stereo); loudness is set by ffmpeg."""
import numpy as np, wave, sys

SR, DUR = 48000, 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)
t_all = np.arange(N) / SR


def band(x, lo, hi, soft=0.15):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo > 0: m *= 1 / (1 + np.exp(np.clip(-(f - lo) / (lo * soft), -60, 60)))
    if hi < SR / 2: m *= 1 / (1 + np.exp(np.clip((f - hi) / (hi * soft), -60, 60)))
    return np.fft.irfft(X * m, len(x))


def noise(sec): return rng.standard_normal(int(sec * SR))


def env(n, a, d, shape=1.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d) if d else np.minimum(1, t / max(a, 1e-4))
    return e ** shape


def put(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if j <= i: return
    s = sig[:j - i] * gain
    L[i:j] += s * np.cos((pan + 1) * np.pi / 4) * 1.414
    R[i:j] += s * np.sin((pan + 1) * np.pi / 4) * 1.414


def fade(sig, a=0.05, b=0.05):
    n = len(sig); e = np.ones(n)
    na, nb = int(a * SR), int(b * SR)
    if na: e[:na] = np.linspace(0, 1, na)
    if nb: e[-nb:] = np.linspace(1, 0, nb)
    return sig * e


# ---------------- felt piano ----------------
PIANO_L = np.zeros(N); PIANO_R = np.zeros(N)
NOTE = {}
for o in range(1, 8):
    for k, nm in enumerate(['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']):
        NOTE[f'{nm}{o}'] = 440 * 2 ** ((o - 4) + (k - 9) / 12)


def piano(name, at, vel=0.5, length=4.0, pan=0.0):
    f0 = NOTE[name]; n = int(length * SR); t = np.arange(n) / SR
    y = np.zeros(n); B = 0.00035
    bright = 0.5 + vel * 0.6
    for k in range(1, 11):
        fk = f0 * k * np.sqrt(1 + B * k * k)
        if fk > 9000: break
        amp = (1 / k ** 1.6) * (bright ** (k - 1))
        dec = 1 / (0.55 + 0.35 * k + f0 / 900)
        y += amp * np.sin(2 * np.pi * fk * t + rng.random() * 6.28) * np.exp(-t / (dec * (3.2 if length > 3 else 1.6)))
    att = np.minimum(1, t / 0.012)
    y *= att
    thump = band(noise(0.05), 80, 900) * env(int(0.05 * SR), 0.002, 0.012) * 0.25
    y[:len(thump)] += thump
    y *= vel / max(1e-6, np.abs(y).max())
    y = fade(y, 0, 0.3)
    i = int(at * SR); j = min(N, i + n)
    PIANO_L[i:j] += y[:j - i] * np.cos((pan + 1) * np.pi / 4) * 1.414
    PIANO_R[i:j] += y[:j - i] * np.sin((pan + 1) * np.pi / 4) * 1.414


# 0.40 first note, 1.25 open fifth
piano('Db4', 0.40, 0.42, 3.0)
piano('Db3', 1.25, 0.30, 3.0, -0.2); piano('Ab3', 1.27, 0.26, 3.0, 0.2)
# 2.50–4.50 routine motif (3 notes, repeating), stops unresolved on Eb4
for i, nm in enumerate(['Ab4', 'F4', 'Db4', 'Ab4', 'F4', 'Db4']):
    piano(nm, 2.55 + i * 0.33, 0.22, 1.2, 0.15 if i % 2 else -0.15)
piano('Eb4', 4.55, 0.25, 2.0)
# 5.00 low sustained Bbm(add9)
for k, (nm, v) in enumerate([('Bb2', .17), ('F3', .13), ('Db4', .11), ('C5', .08)]):
    piano(nm, 5.02 + k * 0.05, v, 2.6, -0.3 + k * 0.2)
# 8.00 single high note with 「人生は、」 then sparse melody
piano('Ab5', 8.00, 0.30, 3.5, 0.1)
for at, nm in [(8.9, 'F5'), (9.65, 'Eb5'), (10.4, 'Db5'), (11.05, 'Eb5')]:
    piano(nm, at, 0.22, 2.8, 0.05)
piano('Db4', 8.9, 0.12, 3.5, -0.2); piano('Gb3', 10.4, 0.12, 3.0, -0.2)
# 11.50 warm low note, 12.25 two-voice phrase, 13.30 unresolved Gbmaj7 (rolled)
piano('Gb2', 11.50, 0.30, 3.5, -0.1)
piano('Bb4', 12.30, 0.22, 2.5, 0.1); piano('Gb3', 12.30, 0.16, 2.5, -0.2)
piano('Ab4', 12.90, 0.20, 2.5, 0.1); piano('Db4', 12.90, 0.15, 2.5, -0.2)
for k, nm in enumerate(['Gb3', 'Bb3', 'Db4', 'F4']):
    piano(nm, 13.30 + k * 0.07, 0.20 - k * 0.02, 2.0, -0.3 + k * 0.2)


def reverb(x, sec=1.6, seed=0):
    r = np.random.default_rng(seed); n = int(sec * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (sec / 5)); ir = band(ir, 200, 6000); ir[0] = 0; ir /= np.abs(ir).sum() ** 0.5 * 18
    m = len(x) + n; F = 1 << (m - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(ir, F), F)[:len(x)]


PL = band(PIANO_L, 40, 5500); PR = band(PIANO_R, 40, 5500)  # felt: soft top end
L += PL * 0.9 + reverb(PL, seed=1) * 0.55
R += PR * 0.9 + reverb(PR, seed=2) * 0.55

# ---------------- scene 1: train (0–2.5 s) ----------------
rumble = band(noise(2.7), 30, 260) * 0.17 + band(noise(2.7), 300, 1500) * 0.03
rumble *= 1 + 0.25 * np.sin(2 * np.pi * 1.7 * np.arange(len(rumble)) / SR)
put(fade(rumble, 0.02, 0.15), 0.0, 1.0)
for k, at in enumerate([0.05, 0.17, 0.95, 1.07, 1.85, 1.97]):  # gatan-goton
    clk = band(noise(0.12), 60, 700) * env(int(0.12 * SR), 0.001, 0.03)
    put(clk, at, 0.55 if k % 2 == 0 else 0.4, -0.1)
put(fade(band(noise(0.9), 200, 3000) * np.hanning(int(0.9 * SR)), 0.01, 0.1), 1.05, 0.06, 0.4)  # passing train outside
put(fade(np.sin(2 * np.pi * 660 * np.arange(int(.35 * SR)) / SR) * 0.5 + np.sin(2 * np.pi * 880 * np.arange(int(.35 * SR)) / SR) * 0.3, 0.02, 0.15), 0.6, 0.012)  # muffled PA tone

# ---------------- scene 2 (2.5–5.0 s) ----------------
whip = band(noise(0.18), 900, 9000) * np.hanning(int(0.18 * SR)) ** 2
put(whip, 2.36, 0.25, 0.5)  # page turn
for i in range(6):  # panel paper slides
    sl = band(noise(0.12), 1500, 7000) * np.hanning(int(0.12 * SR))
    put(sl, 2.54 + i * 0.167, 0.06, (-1) ** i * 0.3)
amb2 = band(noise(2.6), 150, 2500) * 0.035
put(fade(amb2, 0.1, 0.05), 2.45, 1.0)
for i in range(5):  # distant crossing chirp (piyo-piyo)
    n = int(0.09 * SR); tt = np.arange(n) / SR
    ch = np.sin(2 * np.pi * (2900 * tt - 3000 * tt * tt)) * np.hanning(n)
    put(band(ch, 1000, 3200), 2.62 + i * 0.36, 0.035, 0.6); put(band(ch, 1000, 3200), 2.62 + i * 0.36 + 0.13, 0.03, 0.6)
for i in range(10):  # faint keyboard
    k = band(noise(0.02), 1500, 6000) * env(int(0.02 * SR), 0.0005, 0.004)
    put(k, 3.0 + i * 0.11 + rng.random() * 0.03, 0.05, -0.5)
pen = band(noise(0.05), 2000, 8000) * env(int(0.05 * SR), 0.001, 0.008)
put(pen, 4.21, 0.4, 0.1); put(band(noise(0.12), 2500, 7000) * env(int(0.12 * SR), 0.005, 0.04), 4.22, 0.08, 0.1)
tick = band(noise(0.03), 1500, 5000) * env(int(0.03 * SR), 0.0003, 0.004)
put(tick, 4.33, 0.45, -0.3)

# ---------------- scene 3 (5.0–7.5 s) ----------------
rain = band(noise(2.3), 2000, 9000) * 0.03 + band(noise(2.3), 300, 1500) * 0.012
put(fade(rain, 0.25, 0.08), 5.0, 1.0, 0.0)
for i in range(30):
    d = band(noise(0.03), 2500, 9000) * env(int(0.03 * SR), 0.0005, 0.006)
    put(d, 5.05 + rng.random() * 2.15, 0.06 * rng.random(), rng.uniform(-.7, .7))
hum = np.sin(2 * np.pi * 100 * np.arange(int(2.25 * SR)) / SR) * 0.006
put(fade(hum, 0.2, 0.1), 5.0, 1.0)
nb = int(0.34 * SR)  # one subtle breath
breath = band(noise(0.34), 400, 2200) * (np.sin(np.linspace(0, np.pi, nb)) ** 1.5)
put(breath, 7.18, 0.09, 0.0)

# ---------------- scene 4 (7.5–11.5 s) ----------------
wn = 4.1; wind = band(noise(wn), 60, 900)
tw = np.arange(len(wind)) / SR
wind_env = np.interp(tw, [0, .5, 1.2, 3.6, 4.1], [0.15, 0.2, 0.6, 0.7, 0.0]) * (1 + 0.35 * np.sin(2 * np.pi * 0.4 * tw))
put(wind * wind_env * 0.05, 7.5, 1.0, -0.2)
put(band(noise(wn), 80, 1200) * wind_env * 0.03, 7.5, 1.0, 0.3)
far_train = band(noise(2.5), 40, 300) * np.hanning(int(2.5 * SR)) * 0.05
put(far_train, 8.6, 1.0, 0.5)
lap = band(noise(3.2), 150, 800) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.9 * np.arange(int(3.2 * SR)) / SR)) ** 2 * 0.03
put(fade(lap, 0.6, 0.3), 8.1, 1.0, -0.3)

# ---------------- scene 5 (11.5–15 s) ----------------
n = int(0.45 * SR); tt = np.arange(n) / SR  # door creak (soft)
creak = np.sign(np.sin(2 * np.pi * (240 + 90 * np.sin(2 * np.pi * 3 * tt)) * tt)) * np.hanning(n)
put(band(creak, 300, 1600) * 0.5, 11.48, 0.05, 0.2)
nb = int(1.6 * SR); tb = np.arange(nb) / SR  # small door bell (karan)
bell = sum(a * np.sin(2 * np.pi * fr * tb) * np.exp(-tb / d) for fr, a, d in [(2093, 1, .5), (2637 * 1.01, .6, .4), (3951, .35, .25), (5587, .2, .15)])
put(bell * np.minimum(1, tb / 0.002), 11.56, 0.05, 0.3); put(bell * np.minimum(1, tb / 0.002), 11.72, 0.025, 0.35)
cafe = band(noise(3.5), 250, 1400) * (1 + 0.6 * band(noise(3.5), 1, 6)) * 0.02
put(fade(cafe, 0.5, 0.6), 11.5, 1.0, 0.0)
pour = band(noise(1.1), 1800, 7000) * (0.6 + 0.4 * np.abs(band(noise(1.1), 5, 40)) * 4) * 0.03
put(fade(pour, 0.08, 0.2), 12.25, 1.0, 0.2)
page = band(noise(0.22), 1200, 7000) * np.hanning(int(0.22 * SR)) ** 2
put(page, 12.75, 0.06, 0.5)
cup = band(noise(0.06), 600, 4000) * env(int(0.06 * SR), 0.0005, 0.012)
put(cup, 13.45, 0.18, 0.1)
put(fade(band(noise(1.7), 4000, 10000) * 0.006, 0.3, 0.6), 13.3, 1.0)

# ---------------- master ----------------
mix = np.stack([L, R], 1)
end_fade = np.interp(t_all, [0, 14.2, 15.0], [1, 1, 0.25])  # not to silence: the loop stays seamless
mix *= end_fade[:, None]
mix = np.tanh(mix * 1.2) / 1.2
mix /= np.abs(mix).max() / 0.7
pcm = (mix * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'soundtrack_raw.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', mix.shape)
