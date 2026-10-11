"""Synthesises the soundtrack + sound design for the nxtlvl.ai promo (33 s, 128 BPM), numpy only.

Every cue below is written in beats on the same grid the animation in index.html uses
(bt(n) = n * 60/128 s), so hits, whooshes, clicks and the price drop land on picture.
Output: music.wav (48 kHz, stereo, 16-bit).
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 33.0
N = int(SR * DUR)
BPM = 128
B = 60 / BPM
rng = np.random.default_rng(7)


def bt(n):
    return n * B


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def wob(k):
    """Deterministic 0..1 pseudo-random value."""
    return float(np.sin(k * 12.9898) * 0.5 + 0.5)


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, sig, at, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            a, b = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            sig = np.stack([sig * a, sig * b]) * np.sqrt(2)
        i = int(round(at * SR))
        if i >= N or i + sig.shape[1] <= 0:
            return
        s0 = max(0, -i)
        j = min(N, i + sig.shape[1])
        self.x[:, max(i, 0):j] += sig[:, s0:j - i] * gain


def fft_filter(x, lo=None, hi=None, order=4):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** order)
    if hi:
        m *= 1 / (1 + (f / hi) ** order)
    return np.fft.irfft(X * m, len(x))


def svf(x, cut, q=0.7, mode='lp'):
    """State-variable filter with per-sample cutoff."""
    cut = np.broadcast_to(np.asarray(cut, float), x.shape)
    g = np.tan(np.pi * np.clip(cut, 20, SR * 0.45) / SR)
    k = 1 / q
    ic1 = ic2 = 0.0
    out = np.empty_like(x)
    for n in range(len(x)):
        gn = g[n]
        a1 = 1 / (1 + gn * (gn + k))
        v3 = x[n] - ic2
        v1 = a1 * ic1 + gn * a1 * v3
        v2 = ic2 + gn * v1
        ic1 = 2 * v1 - ic1
        ic2 = 2 * v2 - ic2
        out[n] = v2 if mode == 'lp' else (v1 if mode == 'bp' else x[n] - k * v1 - v2)
    return out


def adsr(n, a=0.01, r=0.1):
    e = np.ones(n)
    na, nr = min(int(a * SR), n), min(int(r * SR), n)
    e[:na] = np.linspace(0, 1, na)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def norm_rms(x, db):
    v = x[np.abs(x) > 1e-5]
    return x * (10 ** (db / 20) / (np.sqrt(np.mean(v ** 2)) + 1e-12))


def saw(f, t, hmax=18, bright=0.22, phase=0.0):
    h = np.arange(1, hmax + 1)
    h = h[f * h < 15000]
    amp = (1 / h) * np.exp(-h * bright)
    return (np.sin(2 * np.pi * f * t[:, None] * h[None, :] + phase * h[None, :]) * amp).sum(1)


# ------------------------------------------------------------------ harmony: Am7 - Fmaj7 - C - G, one chord per bar
PROG = [[57, 60, 64, 67], [53, 57, 60, 64], [55, 60, 64, 67], [55, 59, 62, 67]]
ROOT = [33, 29, 36, 31]
FINAL = [48, 55, 64, 71, 74, 79]          # Cmaj9, the resolution on the last hit


def chord(bar):
    return PROG[bar % 4]


def root(bar):
    return ROOT[bar % 4]


# ------------------------------------------------------------------ instruments
def pad_note(m, d, bright=0.3):
    t = tvec(d)
    out = np.zeros((2, len(t)))
    for det, pan in [(-0.12, -0.75), (0.0, 0.0), (0.13, 0.75)]:
        s = saw(midi(m + det), t, hmax=14, bright=bright, phase=rng.uniform(0, 6.28))
        a, b = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        out += np.stack([s * a, s * b])
    return out * adsr(len(t), a=0.25, r=0.5)


def stab(notes, d=0.26, bright=0.12):
    t = tvec(d)
    out = np.zeros((2, len(t)))
    for m in notes:
        for det, pan in [(-0.18, -0.9), (-0.07, -0.4), (0.0, 0.0), (0.08, 0.4), (0.17, 0.9)]:
            s = saw(midi(m + 12 + det), t, hmax=16, bright=bright, phase=rng.uniform(0, 6.28))
            a, b = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            out += np.stack([s * a, s * b])
    return out * np.exp(-t * 7) * adsr(len(t), a=0.004, r=0.05)


def kick(punch=1.0):
    t = tvec(0.5)
    f = 44 + 140 * np.exp(-t * 32)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6.0)
    click = fft_filter(rng.standard_normal(len(t)), lo=1500) * np.exp(-t * 350) * 0.5
    return np.tanh((s + click) * 1.8 * punch)


def clap():
    t = tvec(0.35)
    n = rng.standard_normal(len(t))
    e = np.zeros(len(t))
    for off in (0, 0.01, 0.021):
        e += np.where(t >= off, np.exp(-(t - off) * 70), 0) * 0.6
    e += np.where(t >= 0.03, np.exp(-(t - 0.03) * 13), 0)
    return fft_filter(n * e, lo=900, hi=7000)


def snare():
    t = tvec(0.2)
    body = np.sin(2 * np.pi * np.cumsum(190 + 60 * np.exp(-t * 40)) / SR) * np.exp(-t * 25)
    nz = fft_filter(rng.standard_normal(len(t)), lo=1500, hi=9000) * np.exp(-t * 22)
    return body * 0.5 + nz


def hat(open_=False):
    t = tvec(0.28 if open_ else 0.07)
    return fft_filter(rng.standard_normal(len(t)), lo=7500) * np.exp(-t * (12 if open_ else 80))


def crash(d=1.8):
    t = tvec(d)
    n = fft_filter(rng.standard_normal(len(t)), lo=4500)
    ring = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (3215, 4471, 5831, 6922)) * 0.04
    return (n + ring) * np.exp(-t * 2.6)


def bass_note(m, d):
    t = tvec(d)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * saw(f * 2, t, hmax=6, bright=0.5)
    return np.tanh(s * 1.4) * adsr(len(t), a=0.004, r=0.04)


def pluck(m, d=0.35):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for h in range(1, 10, 2):
        s += np.sin(2 * np.pi * f * h * t) / (h * h) * np.exp(-t * (11 + h * 3))
    s += 0.35 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 18)
    return s * adsr(len(t), a=0.002, r=0.04)


def bell(m, d=2.0):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for ratio, amp, dec in [(1, 1, 2.4), (2.0, .5, 3.5), (2.76, .35, 5), (5.4, .2, 8), (8.93, .1, 12)]:
        if f * ratio < 12000:
            s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec)
    return s * adsr(len(t), a=0.002, r=0.1)


def riser(d, f0=300, f1=9000):
    t = tvec(d)
    p = t / d
    s = svf(rng.standard_normal(len(t)), f0 * (f1 / f0) ** (p ** 1.6), q=2.4, mode='bp') * p ** 1.8
    tone = np.sin(2 * np.pi * np.cumsum(180 * 5 ** (p ** 1.5)) / SR) * p ** 2 * 0.18
    return s + tone


def whoosh(d=0.6, peak=5500, rev=False):
    t = tvec(d)
    p = t / d
    s = svf(rng.standard_normal(len(t)), 350 + peak * np.sin(np.pi * p) ** 2, q=1.6, mode='bp')
    s *= np.sin(np.pi * np.clip(p * 1.1, 0, 1)) ** 2
    return s[::-1].copy() if rev else s


def swish(d=0.32):
    t = tvec(d)
    p = t / d
    s = svf(rng.standard_normal(len(t)), 1500 + 9000 * p ** 0.6, q=2.0, mode='bp')
    return s * np.sin(np.pi * p) ** 1.5


def impact(d=2.6, big=1.0):
    t = tvec(d)
    boom = np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-t * 8)) / SR) * np.exp(-t * 1.8)
    n = rng.standard_normal(len(t))
    body = svf(n, 2600 * np.exp(-t * 3) + 250, q=0.8) * np.exp(-t * 3.2)
    air = fft_filter(n, lo=5000) * np.exp(-t * 4.5) * 0.35
    return np.tanh(boom * 1.5 * big) + body * 0.75 + air


def thwack():
    t = tvec(0.25)
    body = np.sin(2 * np.pi * np.cumsum(140 + 260 * np.exp(-t * 30)) / SR) * np.exp(-t * 18)
    nz = fft_filter(rng.standard_normal(len(t)), lo=700, hi=5500) * np.exp(-t * 28)
    return np.tanh(body * 1.5 + nz * 0.9)


def sub_drop(d=1.2):
    t = tvec(d)
    return np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-t * 3)) / SR) * np.exp(-t * 2.2) * adsr(len(t), a=0.005, r=0.2)


def ui_click(p=2400):
    t = tvec(0.06)
    return np.sin(2 * np.pi * p * t) * np.exp(-t * 90) * 0.7 + fft_filter(rng.standard_normal(len(t)), lo=3000) * np.exp(-t * 500) * 0.5


def tick(p=3000):
    t = tvec(0.025)
    return np.sin(2 * np.pi * p * t) * np.exp(-t * 260) + fft_filter(rng.standard_normal(len(t)), lo=4000) * np.exp(-t * 700) * 0.4


def pop(f0=700, f1=1300, d=0.09):
    t = tvec(d)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45)


def bleep(f, d=0.03):
    t = tvec(d)
    return np.sign(np.sin(2 * np.pi * f * t)) * 0.5 * adsr(len(t), a=0.001, r=0.005)


def thump():
    t = tvec(0.16)
    return np.sin(2 * np.pi * np.cumsum(60 + 90 * np.exp(-t * 35)) / SR) * np.exp(-t * 20)


def stutter(notes, dur, at, bus, gain=0.6):
    """Glitch stutter: a tiny grain of a chord stab retriggered faster and lower."""
    grain = stab(notes, d=0.05)
    n, tt = 0, 0.0
    while tt < dur:
        idx = np.arange(0, grain.shape[1] - 1, 1 - n * 0.045)
        g = np.stack([np.interp(idx, np.arange(grain.shape[1]), c) for c in grain])
        bus.add(g * adsr(g.shape[1], a=0.001, r=0.008), at + tt, gain * (0.8 if n % 2 else 1.0))
        tt += 0.042 if n < 6 else 0.028
        n += 1


# ------------------------------------------------------------------ arrangement
pad, bass, drums, stabs, arp, fx, send = Bus(), Bus(), Bus(), Bus(), Bus(), Bus(), Bus()
kicks = []

for bar in range(17):
    b0 = bar * 8
    t0 = bt(b0)
    final = bar >= 16
    notes = FINAL if final else chord(bar)
    d = (DUR - t0) if final else bt(8) + 0.4
    for m in notes:
        pad.add(pad_note(m, d, bright=0.55 if bar < 1 else 0.3), t0, 1.3 if final else 1.0)
    if final:
        bass.add(bass_note(24, DUR - t0) * np.exp(-tvec(DUR - t0) * 0.7), t0, 1.0)
        continue

    groove = 8 <= b0 < 48 or 52 <= b0 < 64
    for beat in range(8):
        bb = b0 + beat
        tb = bt(bb)
        if groove:
            kicks.append(tb)
            drums.add(kick(), tb, 1.0)
            if beat % 2 == 1:
                drums.add(clap(), tb, 0.55, pan=0.04)
                send.add(clap(), tb, 0.25)
            drums.add(hat(open_=True), tb + B / 2, 0.32, pan=0.25)
            if bb >= 16:
                for q in (0.25, 0.75):
                    drums.add(hat(), tb + q * B, 0.16, pan=-0.3)
            r = root(bar)
            bass.add(bass_note(r, B * 0.22), tb, 0.75)
            bass.add(bass_note(r + 12 if beat % 4 == 3 else r, B * 0.45), tb + B / 2, 1.0)
    # syncopated chord stabs (16th positions) from the services section on
    if (16 <= b0 < 48) or (52 <= b0 < 60):
        for s16 in ((0, 3, 6, 10, 12, 14) if b0 >= 52 else (0, 3, 6, 10, 12)):
            tt = t0 + s16 * B / 4
            st = stab(notes)
            stabs.add(st, tt, 1.0)
            send.add(st * 0.4, tt, 0.6)
    # 16th pluck arpeggio from the editor section on
    if 28 <= b0 < 48 or 52 <= b0 < 64:
        up = 12 if b0 >= 40 else 0
        pat = [0, 1, 2, 3, 2, 1, 3, 2]
        for k in range(32):
            m = notes[pat[k % 8]] + 12 + up
            g = 0.55 if k % 4 == 0 else 0.36
            pl = pluck(m)
            arp.add(pl, t0 + k * B / 4, g, pan=0.35 if k % 2 else -0.35)
            send.add(pl, t0 + k * B / 4, g * 0.5)

# ------------------------------------------------------------------ intro (b0-b8): star ignite, word hammers, logo slam
fx.add(impact(2.2, 0.6), 0.05, 0.6)
fx.add(bell(84, 2.5), 0.06, 0.45); send.add(bell(84, 2.5), 0.06, 0.9)
fx.add(bell(91, 2.0), 0.1, 0.25, pan=0.3); send.add(bell(91, 2.0), 0.1, 0.5)
fx.add(whoosh(0.6), 0.0, 0.5, pan=-0.3)
fx.add(riser(0.85, 400, 6000), bt(2) - 0.85, 0.35)
for i in range(4):                                      # MOTION. VISUALS. BRANDS. NEXT LEVEL.
    tb = bt(2 + i)
    kicks.append(tb)
    drums.add(kick(1.2), tb, 1.1)
    fx.add(thwack(), tb, 0.85)
    fx.add(sub_drop(0.6), tb, 0.5)
    st = stab(chord(0), d=0.4)
    stabs.add(st, tb, 1.3)
    send.add(st, tb, 0.5)
    fx.add(swish(0.18), tb - 0.17, 0.35, pan=(-0.6, 0.6, -0.3, 0.3)[i])
fx.add(crash(1.5), bt(4), 0.5)
fx.add(impact(2.4, 1.0), bt(6) + 0.3, 1.0)
fx.add(crash(2.0), bt(6) + 0.3, 0.55)
fx.add(sub_drop(1.2), bt(6) + 0.3, 0.7)
kicks.append(bt(6) + 0.3)
fx.add(whoosh(0.45, 7000), bt(6) - 0.12, 0.45, pan=0.6)     # star flies in
stutter(chord(0), 0.16, bt(6) + 0.28, fx, 0.45)
for i, m in enumerate([84, 88, 91, 96]):
    fx.add(bell(m, 1.6), bt(6) + 0.32 + i * 0.04, 0.16, pan=-0.4 + i * 0.25)
    send.add(bell(m, 1.6), bt(6) + 0.32, 0.25)
for k in range(12):                                      # tagline scramble ticks
    fx.add(tick(2500 + 900 * wob(k)), bt(6.6) + k * 0.045, 0.18, pan=0.2)
for k in range(16):                                      # snare build into the hook
    drums.add(snare(), bt(6.6) + k * B * 0.0825, 0.12 + 0.03 * k)
fx.add(riser(bt(8) - bt(6.8), 300, 10000), bt(6.8), 0.55)
fx.add(crash(1.2)[::-1].copy(), bt(8) - 1.2, 0.35)        # reverse cymbal
fx.add(whoosh(0.55, 6500), bt(7.4), 0.55, pan=0.3)        # star wipe

# ------------------------------------------------------------------ hook (b8-b16)
fx.add(impact(2.4, 1.0), bt(8), 0.9); fx.add(crash(2.0), bt(8), 0.5)
for i in range(5):                                       # words fly in
    fx.add(swish(0.16), bt(8.5 + i * 0.5) - 0.12, 0.3, pan=-0.5 + i * 0.25)
    fx.add(thump(), bt(8.5 + i * 0.5), 0.35)
fx.add(pop(600, 1200), bt(10.75), 0.35)
fx.add(whoosh(0.4, 7000), bt(11.35), 0.55)
stutter(chord(2), 0.18, bt(11.4), fx, 0.4)
fx.add(swish(0.5), bt(12) - 0.05, 0.5, pan=0.7); fx.add(swish(0.5), bt(12.1) - 0.05, 0.4, pan=-0.7)
fx.add(pop(500, 1100, 0.12), bt(12.15), 0.45)
for b in (13, 13.75, 14.5):                              # slot machine
    for k in range(5):
        fx.add(tick(2200 + k * 250), bt(b) - 0.2 + k * 0.04, 0.25, pan=0.2)
    fx.add(bell(91, 0.8), bt(b) + 0.02, 0.18)
    fx.add(pop(900, 1500), bt(b), 0.3)
fx.add(swish(0.55), bt(15.55), 0.8, pan=-0.2)            # whip pan
fx.add(whoosh(0.5, 8000), bt(15.6), 0.4, pan=0.5)

# ------------------------------------------------------------------ services (b16-b28)
fx.add(crash(1.8), bt(16), 0.45)
for i in range(6):
    fx.add(pop(500 + i * 90, 1000 + i * 160), bt(16.2) + i * 0.09, 0.32, pan=-0.6 + i * 0.24)
fx.add(ui_click(2400), bt(25.5), 0.55)
fx.add(riser(0.85, 500, 12000), bt(26.4), 0.6)
fx.add(whoosh(0.7, 8000), bt(26.5), 0.5)
fx.add(impact(2.2, 0.9), bt(27.6), 0.85)
kicks.append(bt(27.6))

# ------------------------------------------------------------------ editor (b28-b40)
fx.add(whoosh(0.9, 4500), bt(32), 0.55, pan=-0.3)        # layers explode
for i in range(3):
    fx.add(ui_click(1600 + i * 400) * 0.8, bt(32.1 + i * 0.1) + 0.35, 0.4, pan=0.3)
for i in range(4):
    fx.add(pop(800 + i * 150, 1400 + i * 200), bt(33 + i * 0.5), 0.3, pan=0.4)
fx.add(whoosh(0.75, 4500, rev=True), bt(35.25) - 0.1, 0.55)   # layers collapse
fx.add(impact(1.8, 0.8), bt(36), 0.7)
kicks.append(bt(36))
fx.add(ui_click(2400), bt(37.5), 0.55)
fx.add(pop(600, 1200, 0.12), bt(37.75), 0.4)
for i, m in enumerate([84, 88, 91]):
    fx.add(bell(m, 1.4), bt(38.9) + i * 0.05, 0.22)
    send.add(bell(m, 1.4), bt(38.9), 0.4)
stutter(chord(9), bt(40) - bt(39.4), bt(39.4), fx, 0.5)   # glitch transition
for k in range(16):
    fx.add(bleep(600 + 2400 * wob(k + 40)), bt(39.4) + k * 0.05, 0.12, pan=np.sin(k) * 0.6)

# ------------------------------------------------------------------ creative wall (b40-b48)
fx.add(impact(2.2, 1.0), bt(40), 0.85); fx.add(crash(1.8), bt(40), 0.5)
fx.add(whoosh(0.8, 5000), bt(40), 0.45)
for i in range(5):
    fx.add(thump(), bt(41 + i * 0.5), 0.4)
    fx.add(swish(0.14), bt(41 + i * 0.5) - 0.1, 0.25, pan=-0.4 + i * 0.2)
fx.add(riser(1.0, 600, 12000), bt(47.5) - 0.7, 0.5)
fx.add(whoosh(0.35, 9000), bt(47.5), 0.6)

# ------------------------------------------------------------------ process build (b48-b52)
for i in range(4):
    tb = bt(48 + i)
    kicks.append(tb)
    drums.add(kick(1.15), tb, 1.0)
    fx.add(thwack(), tb, 0.8)
    stabs.add(stab(chord(12), d=0.35), tb, 1.2)
    fx.add(swish(0.16), tb - 0.14, 0.35, pan=(-0.5, 0.5, 0, 0.3)[i])
fx.add(crash(1.0), bt(50), 0.4)
roll, tt = [], bt(48)
while tt < bt(51.7):                                     # accelerating snare roll
    p = (tt - bt(48)) / (bt(51.7) - bt(48))
    roll.append(tt)
    tt += B * (0.5 if p < 0.25 else 0.25 if p < 0.55 else 0.125 if p < 0.8 else 0.0625)
for k, r in enumerate(roll):
    drums.add(snare(), r, 0.18 + 0.5 * k / len(roll))
fx.add(riser(bt(51.7) - bt(48), 250, 12000), bt(48), 0.6)
for k in range(10):                                      # price scramble bleeps
    fx.add(bleep(900 + 2200 * wob(k + 90), 0.025), bt(51.6) + k * 0.034, 0.18)

# ------------------------------------------------------------------ pricing drop (b52-b60)
fx.add(impact(2.8, 1.25), bt(52), 1.15); fx.add(crash(2.4), bt(52), 0.65)
fx.add(sub_drop(1.5), bt(52), 0.9)
stutter(chord(13), 0.1, bt(52), fx, 0.4)
for col, dur in enumerate((0.75, 0.87, 0.99)):           # rolling digits
    for k in range(1, 20):
        p = 1 - (1 - k / 19) ** 0.25
        fx.add(tick(2600 + col * 500), bt(52) + p * dur, 0.16, pan=(-0.4, 0, 0.4)[col])
for i, m in enumerate([84, 88, 91, 96, 100]):            # confetti shimmer
    fx.add(bell(m, 2.0), bt(52) + 0.05 + i * 0.05, 0.2, pan=-0.6 + i * 0.3)
    send.add(bell(m, 2.0), bt(52) + 0.05 + i * 0.05, 0.35)
fx.add(pop(500, 1000), bt(52.4), 0.3); fx.add(pop(600, 1250), bt(52.7), 0.35)
fx.add(whoosh(0.55, 5000), bt(54) - 0.05, 0.5)
for i in range(4):
    fx.add(pop(800 + i * 140, 1500 + i * 220), bt(55 + i * 0.5) + 0.08, 0.38, pan=-0.2)
fx.add(ui_click(2400), bt(58.25), 0.6)
for i, m in enumerate([88, 91, 96, 100]):
    fx.add(bell(m, 1.5), bt(58.28) + i * 0.04, 0.2, pan=-0.4 + i * 0.25)
    send.add(bell(m, 1.5), bt(58.28), 0.35)
fx.add(riser(bt(60) - bt(59.0), 400, 11000), bt(59.0), 0.55)
fx.add(whoosh(0.5, 6000), bt(59.4), 0.5)

# ------------------------------------------------------------------ outro (b60-)
fx.add(impact(2.6, 1.1), bt(60), 1.0); fx.add(crash(2.2), bt(60), 0.55)
fx.add(whoosh(0.45, 7000), bt(60.2) - 0.05, 0.4, pan=0.6)
fx.add(impact(2.0, 0.8), bt(60) + 0.5, 0.6)
kicks.append(bt(60) + 0.5)
fx.add(bell(91, 2.2), bt(60) + 0.55, 0.3); send.add(bell(91, 2.2), bt(60) + 0.55, 0.6)
for i in range(7):
    fx.add(tick(1800 + i * 120) * 0.7, bt(62) + i * 0.05, 0.18)
fx.add(pop(600, 1200), bt(63), 0.35); fx.add(pop(700, 1400), bt(63) + 0.1, 0.35)
fx.add(impact(3.0, 1.0), bt(64), 0.9); fx.add(crash(3.0), bt(64), 0.5)
kicks.append(bt(64))
for i, m in enumerate([84, 88, 91, 96]):
    fx.add(bell(m, 2.6), bt(64) + i * 0.06, 0.24, pan=-0.4 + i * 0.25)
    send.add(bell(m, 2.6), bt(64) + i * 0.06, 0.6)
fx.add(whoosh(0.9, 6000), bt(64), 0.35, pan=0.5)

# ------------------------------------------------------------------ mix
tt = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    i = int(k * SR)
    duck[i:] = np.minimum(duck[i:], 1 - 0.62 * np.exp(-(tt[i:] - k) / 0.1))

gap = np.ones(N)                                         # the silent beat before the price drop
g0, g1 = int(bt(51.72) * SR), int(bt(52) * SR)
gap[g0:g1] = 0.0
gap[g0 - 480:g0] = np.linspace(1, 0, 480)

pad_auto = np.interp(tt, [0, bt(2), bt(8), bt(48), bt(51.7), bt(52), bt(64), DUR], [0.35, 0.8, 0.7, 0.7, 1.0, 0.7, 1.0, 1.0])
pad_x = np.stack([fft_filter(c, lo=150, hi=6000) for c in pad.x]) * pad_auto * duck
bass_x = bass.x * duck
stab_x = np.stack([fft_filter(c, lo=250, hi=9000) for c in stabs.x]) * (0.45 + 0.55 * duck)
arp_x = np.stack([fft_filter(c, lo=300) for c in arp.x]) * (0.6 + 0.4 * duck)
dly = int(0.75 * B * SR)
echo = np.zeros_like(arp_x)
for n_rep, g in enumerate([0.3, 0.15, 0.07], start=1):
    s = dly * n_rep
    echo[0, s:] += arp_x[1, :-s] * g
    echo[1, s:] += arp_x[0, :-s] * g
arp_x = arp_x + echo

stems = [norm_rms(pad_x, -22.5), norm_rms(bass_x, -19.5), norm_rms(drums.x, -18.5),
         norm_rms(stab_x, -23), norm_rms(arp_x, -27.5), norm_rms(fx.x, -20.5)]

ir_t = tvec(2.4)
ir = np.stack([fft_filter(rng.standard_normal(len(ir_t)), lo=200, hi=7000) for _ in range(2)]) * np.exp(-ir_t * 2.8)
ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
nfft = 1 << (N + len(ir_t) - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send.x[c], nfft) * np.fft.rfft(ir[c], nfft), nfft)[:N] for c in range(2)])

mix = sum(stems) * gap + norm_rms(wet, -26)
mix = np.stack([fft_filter(c, lo=28) for c in mix])
mix = np.tanh(mix * 1.25) / np.tanh(1.25)
fade = np.ones(N)
fade[:240] = np.linspace(0, 1, 240)
fo = int((DUR - 0.65) * SR)
fade[fo:] = np.linspace(1, 0, N - fo) ** 1.6
mix *= fade
mix *= 10 ** (-1.5 / 20) / np.max(np.abs(mix))

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype('<i2').tobytes())
print('wrote', out, f'{DUR}s')
