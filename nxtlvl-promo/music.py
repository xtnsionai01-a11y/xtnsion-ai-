"""Synthesises the soundtrack + sound design for the nxtlvl social promo (36 s, 120 BPM), numpy only.

A smooth, glassy future-house bed: soft kick, airy claps, shakers, warm sub, lush pads and a
ping-pong pluck arp, plus UI sound design (glass chimes, whooshes, bubble pops, notification dings)
placed on the exact second marks the animation in index.html uses.
Output: music.wav (48 kHz, stereo, 16-bit).
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 36.0
N = int(SR * DUR)
B = 0.5                     # 120 BPM
BAR = 2.0
rng = np.random.default_rng(11)


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


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


# ------------------------------------------------------------------ harmony: Fmaj9 - Em7 - Dm9 - Cmaj9 (one per bar)
PROG = [[53, 57, 60, 64, 67], [52, 55, 59, 62, 67], [50, 53, 57, 60, 64], [48, 55, 59, 62, 64]]
ROOT = [41, 40, 38, 36]
FINAL = [48, 55, 59, 62, 64, 67, 71]       # Cmaj9 add 13, the resolution


def chord(bar):
    return PROG[bar % 4]


# ------------------------------------------------------------------ instruments
def pad_note(m, d, bright=0.4):
    t = tvec(d)
    out = np.zeros((2, len(t)))
    for det, pan in [(-0.1, -0.8), (0.0, 0.0), (0.11, 0.8)]:
        s = saw(midi(m + det), t, hmax=12, bright=bright, phase=rng.uniform(0, 6.28))
        s *= 1 + 0.12 * np.sin(2 * np.pi * (0.25 + 0.05 * pan) * t)
        a, b = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        out += np.stack([s * a, s * b])
    return out * adsr(len(t), a=0.6, r=0.8)


def kick():
    t = tvec(0.42)
    f = 46 + 110 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = fft_filter(rng.standard_normal(len(t)), lo=1200, hi=6000) * np.exp(-t * 400) * 0.18
    return np.tanh((s + click) * 1.3)


def clap():
    t = tvec(0.35)
    n = rng.standard_normal(len(t))
    e = np.zeros(len(t))
    for off in (0, 0.012, 0.024):
        e += np.where(t >= off, np.exp(-(t - off) * 80), 0) * 0.5
    e += np.where(t >= 0.03, np.exp(-(t - 0.03) * 16), 0)
    return fft_filter(n * e, lo=1100, hi=6500)


def shaker(acc=1.0):
    t = tvec(0.09)
    env = np.minimum(t / 0.012, 1) * np.exp(-t * 45)
    return fft_filter(rng.standard_normal(len(t)), lo=6500, hi=14000) * env * acc


def hat_open():
    t = tvec(0.3)
    return fft_filter(rng.standard_normal(len(t)), lo=8000) * np.exp(-t * 14)


def bass_note(m, d):
    t = tvec(d)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.18 * np.sin(4 * np.pi * f * t) + 0.06 * saw(f * 2, t, hmax=5, bright=0.6)
    return np.tanh(s * 1.15) * adsr(len(t), a=0.01, r=0.08)


def pluck(m, d=0.6):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for h in range(1, 8, 2):
        s += np.sin(2 * np.pi * f * h * t) / (h * h) * np.exp(-t * (7 + h * 3))
    s += 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 12)
    return s * adsr(len(t), a=0.003, r=0.05)


def bell(m, d=2.2):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for ratio, amp, dec in [(1, 1, 2.0), (2.0, .45, 3.2), (2.76, .3, 4.5), (5.4, .14, 7)]:
        if f * ratio < 11000:
            s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec)
    return s * adsr(len(t), a=0.004, r=0.1)


def ding(m1=88, m2=95):
    t = tvec(0.9)
    s = np.sin(2 * np.pi * midi(m1) * t) * np.exp(-t * 6) * (t < 0.12)
    t2 = np.clip(t - 0.11, 0, None)
    s = s + np.sin(2 * np.pi * midi(m2) * t2) * np.exp(-t2 * 4.5) * (t >= 0.11)
    return s * adsr(len(t), a=0.004, r=0.1)


def whoosh(d=0.8, peak=4500, rev=False):
    t = tvec(d)
    p = t / d
    s = svf(rng.standard_normal(len(t)), 300 + peak * np.sin(np.pi * p) ** 2, q=1.2, mode='bp')
    s *= np.sin(np.pi * np.clip(p * 1.05, 0, 1)) ** 2
    return s[::-1].copy() if rev else s


def glass_swish(d=1.0):
    """Airy whoosh with a scatter of quiet high chimes — the glass transition sound."""
    s = whoosh(d, 6000)
    for k in range(6):
        b = bell(96 + [0, 3, 7, 10, 12, 15][k], 0.9) * 0.05
        i = int((0.15 + 0.1 * k) * d * SR)
        s[i:i + len(b)] += b[:max(0, len(s) - i)]
    return s


def riser(d, f0=300, f1=7000):
    t = tvec(d)
    p = t / d
    s = svf(rng.standard_normal(len(t)), f0 * (f1 / f0) ** (p ** 1.5), q=1.6, mode='bp') * p ** 2
    return s


def soft_impact(d=2.4, big=0.7):
    t = tvec(d)
    boom = np.sin(2 * np.pi * np.cumsum(36 + 50 * np.exp(-t * 7)) / SR) * np.exp(-t * 2.2)
    n = rng.standard_normal(len(t))
    body = fft_filter(n, lo=120, hi=1800) * np.exp(-t * 4.0) * 0.5
    air = fft_filter(n, lo=4000, hi=12000) * np.exp(-t * 3.0) * 0.18
    return np.tanh(boom * 1.2 * big) + body + air


def pop(f0=500, f1=1100, d=0.1):
    t = tvec(d)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 50))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * adsr(len(t), a=0.003, r=0.02)


def ui_click(p=2200):
    t = tvec(0.05)
    return np.sin(2 * np.pi * p * t) * np.exp(-t * 110) * 0.6 + fft_filter(rng.standard_normal(len(t)), lo=3000) * np.exp(-t * 600) * 0.3


def tick(p=2600):
    t = tvec(0.03)
    return np.sin(2 * np.pi * p * t) * np.exp(-t * 220)


# ------------------------------------------------------------------ arrangement
pad, bass, drums, arp, fx, send = Bus(), Bus(), Bus(), Bus(), Bus(), Bus()
kicks = []
GROOVE = (4.0, 31.3)

for bar in range(18):
    t0 = bar * BAR
    final = t0 >= 32
    notes = FINAL if final else chord(bar)
    d = (DUR - t0) if final else BAR + 0.9
    if final and t0 > 32:
        break
    for m in notes:
        pad.add(pad_note(m, d, bright=0.55 if bar < 2 else 0.4), t0, 0.95 if final else 1.0)
    if final:
        bass.add(bass_note(36, DUR - t0) * np.exp(-tvec(DUR - t0) * 0.6), t0, 0.9)
        continue
    in_groove = GROOVE[0] <= t0 < GROOVE[1]
    for beat in range(4):
        tb = t0 + beat * B
        if in_groove and tb < GROOVE[1]:
            kicks.append(tb)
            drums.add(kick(), tb, 0.9)
            if beat % 2 == 1 and tb >= 10:
                drums.add(clap(), tb, 0.45, pan=0.05)
                send.add(clap(), tb, 0.45)
            drums.add(hat_open(), tb + B / 2, 0.22, pan=0.3)
            for q in range(4):
                drums.add(shaker(1.0 if q % 2 else 0.55), tb + q * B / 4, 0.13, pan=-0.35)
    if in_groove:
        r = ROOT[bar % 4]
        for pos, dur, g in ((0, 0.7, 1.0), (1.5, 0.4, 0.8), (2.0, 0.7, 0.9), (3.5, 0.4, 0.8)):
            bass.add(bass_note(r, dur), t0 + pos * B, g)
    # ping-pong pluck arp: 8ths in the body, 16ths through the pricing lift
    if 4.0 <= t0 < 32:
        pat = [0, 2, 4, 1, 3, 2, 4, 1]
        step = B / 4 if 26 <= t0 < 32 else B / 2
        n = int(BAR / step)
        for k in range(n):
            m = notes[pat[k % 8] % len(notes)] + 12
            g = 0.5 if k % 2 == 0 else 0.34
            pl = pluck(m)
            arp.add(pl, t0 + k * step, g, pan=0.45 if k % 2 else -0.45)
            send.add(pl, t0 + k * step, g * 0.6)

# ------------------------------------------------------------------ sound design on picture
def chime_run(at, notes, gap=0.07, gain=0.18, verb=0.4):
    for i, m in enumerate(notes):
        b = bell(m, 1.8)
        fx.add(b, at + i * gap, gain, pan=-0.5 + i / max(1, len(notes) - 1))
        send.add(b, at + i * gap, verb)

# intro
fx.add(whoosh(1.2, 3000), 0.1, 0.35, pan=-0.2)
chime_run(0.45, [84, 88, 91], 0.09, 0.16, 0.5)                 # glass panel appears
for i in range(6):                                           # letters rise
    p = pluck(72 + [0, 4, 7, 11, 12, 16][i], 0.8)
    fx.add(p, 0.9 + i * 0.07, 0.22, pan=-0.5 + i * 0.2); send.add(p, 0.9 + i * 0.07, 0.3)
chime_run(1.5, [91, 95, 98, 103], 0.06, 0.14, 0.5)              # star sparkle
for k in range(10):                                          # tagline shimmer
    fx.add(tick(3200 + k * 140), 1.75 + k * 0.045, 0.06, pan=-0.4 + k * 0.08)
fx.add(riser(1.2, 300, 6000), 2.8, 0.25)
fx.add(glass_swish(1.3), 3.3, 0.5)                           # panel morph
fx.add(soft_impact(2.4, 0.7), 4.0, 0.55)

# hook
chime_run(4.1, [79, 84], 0.08, 0.12, 0.3)
for i in range(6):                                           # chips pop in
    fx.add(pop(450 + i * 60, 950 + i * 90), 4.6 + i * 0.12, 0.28, pan=(-0.7, 0.7, -0.6, 0.6, -0.5, 0.5)[i])
fx.add(whoosh(0.8, 3500), 6.7, 0.3, pan=0.3)                    # headline swap
fx.add(whoosh(0.8, 3500, rev=True), 7.1, 0.25, pan=-0.3)
fx.add(glass_swish(1.3), 9.3, 0.55)                          # chips morph into cards
for i in range(6):
    fx.add(pop(380 + i * 50, 800 + i * 80, 0.12), 10.5 + i * 0.06, 0.22, pan=-0.6 + i * 0.24)

# services: spotlight tour pings
for i, at in enumerate([11.1, 11.8, 12.5, 13.2, 13.9, 14.6]):
    b = bell([84, 86, 88, 91, 93, 96][i], 1.4)
    fx.add(b, at, 0.16, pan=(-0.5, 0, 0.5, -0.5, 0.3, 0.6)[i]); send.add(b, at, 0.35)
fx.add(glass_swish(1.2), 15.2, 0.5)                          # card expands into the studio
fx.add(soft_impact(2.0, 0.55), 16.2, 0.4)

# studio
for i in range(4):
    fx.add(pop(500 + i * 70, 1000 + i * 120), 17.3 + i * 0.25, 0.2, pan=(-0.6, 0.6, -0.6, 0.6)[i])
fx.add(whoosh(1.2, 3000), 18.4, 0.4, pan=-0.3)                  # layers separate
for i in range(3):
    fx.add(ui_click(1500 + i * 300), 18.6 + i * 0.08 + 0.5, 0.25, pan=0.3)
for i in range(4):
    fx.add(pop(700 + i * 120, 1300 + i * 180, 0.08), 19.25 + i * 0.1, 0.18, pan=0.4)
fx.add(whoosh(1.0, 3000, rev=True), 19.9, 0.4)                  # layers reassemble
fx.add(ui_click(2200), 21.0, 0.4)
fx.add(pop(550, 1150, 0.12), 21.1, 0.3)
fx.add(ding(88, 95), 21.95, 0.3); send.add(ding(88, 95), 21.95, 0.4)

# glass slab wipe
fx.add(glass_swish(1.3), 21.65, 0.65, pan=0.0)
fx.add(whoosh(1.2, 7000), 21.75, 0.25, pan=0.5)

# phones + notifications
fx.add(whoosh(1.0, 2500), 22.1, 0.35)
for i, at in enumerate([23.4, 23.95, 24.5, 25.05]):
    d = ding(*[(86, 93), (88, 95), (84, 91), (89, 96)][i])
    fx.add(d, at, 0.22, pan=(-0.6, 0.6, -0.6, 0.6)[i]); send.add(d, at, 0.3)
fx.add(whoosh(0.9, 3000), 26.35, 0.35)
fx.add(riser(1.0, 400, 7000), 25.9, 0.22)

# pricing
fx.add(whoosh(1.2, 2600), 26.9, 0.4)
fx.add(soft_impact(2.2, 0.6), 27.1, 0.4)
for k in range(1, 26):                                       # eased count-up ticks
    p = k / 25
    at = 27.5 + 1.5 * (1 - (1 - p) ** (1 / 3))
    fx.add(tick(1800 + 1400 * p), at, 0.07, pan=0.1)
chime_run(29.0, [88, 95], 0.07, 0.14, 0.4)
for i in range(4):                                           # features tick in
    fx.add(pop(700 + i * 90, 1350 + i * 160), 28.55 + i * 0.4, 0.26, pan=-0.2)
fx.add(ui_click(2300), 30.6, 0.45)
chime_run(30.62, [91, 95, 98, 103, 107], 0.05, 0.12, 0.45)       # sparkle burst
fx.add(glass_swish(1.4), 31.2, 0.55)                         # card morphs into the outro panel

# outro
fx.add(soft_impact(3.0, 0.8), 32.2, 0.5)
for i in range(6):
    p = pluck(72 + [0, 4, 7, 11, 12, 16][i], 0.9)
    fx.add(p, 32.25 + i * 0.06, 0.2, pan=-0.5 + i * 0.2); send.add(p, 32.25 + i * 0.06, 0.35)
chime_run(32.75, [91, 95, 98, 103], 0.06, 0.14, 0.55)
fx.add(pop(500, 1000), 33.6, 0.25); fx.add(pop(600, 1200), 33.74, 0.25)
fx.add(whoosh(1.2, 6000), 34.2, 0.22, pan=0.4)
chime_run(34.8, [96, 103], 0.08, 0.12, 0.5)

# ------------------------------------------------------------------ mix
tt = np.arange(N) / SR
duck = np.ones(N)
for k in kicks:
    i = int(k * SR)
    duck[i:] = np.minimum(duck[i:], 1 - 0.45 * np.exp(-(tt[i:] - k) / 0.12))

pad_auto = np.interp(tt, [0, 3.5, 4.0, 31.0, 32.0, DUR], [0.55, 0.9, 0.75, 0.75, 1.0, 1.0])
pad_x = np.stack([fft_filter(c, lo=140, hi=5200) for c in pad.x]) * pad_auto * duck
bass_x = np.stack([fft_filter(c, hi=900) for c in bass.x]) * duck
arp_x = np.stack([fft_filter(c, lo=300, hi=9000) for c in arp.x]) * (0.7 + 0.3 * duck)
dly = int(0.75 * B * SR)
echo = np.zeros_like(arp_x)
for n_rep, g in enumerate([0.35, 0.2, 0.1, 0.05], start=1):
    s = dly * n_rep
    echo[0 if n_rep % 2 else 1, s:] += arp_x[1 if n_rep % 2 else 0, :-s] * g
arp_x = arp_x + echo

stems = [norm_rms(pad_x, -21.5), norm_rms(bass_x, -20.5), norm_rms(drums.x, -21.0),
         norm_rms(arp_x, -25.5), norm_rms(fx.x, -22.5)]

ir_t = tvec(3.0)
ir = np.stack([fft_filter(rng.standard_normal(len(ir_t)), lo=250, hi=6500) for _ in range(2)]) * np.exp(-ir_t * 2.0)
ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
nfft = 1 << (N + len(ir_t) - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send.x[c], nfft) * np.fft.rfft(ir[c], nfft), nfft)[:N] for c in range(2)])

mix = sum(stems) + norm_rms(wet, -24.5)
mix = np.stack([fft_filter(c, lo=30) for c in mix])
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
fade = np.ones(N)
fi = int(0.8 * SR)
fade[:fi] = np.linspace(0, 1, fi) ** 1.5
fo = int((DUR - 0.8) * SR)
fade[fo:] = np.linspace(1, 0, N - fo) ** 1.5
mix *= fade
mix *= 10 ** (-3.2 / 20) / np.max(np.abs(mix))

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype('<i2').tobytes())
print('wrote', out, f'{DUR}s')
