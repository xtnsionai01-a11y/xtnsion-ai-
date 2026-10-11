"""Synthesises the soundtrack for the nxtlvl.ai promo (34 s, 120 BPM) with numpy only.

Every hit is placed on the same timestamps the animation in index.html uses,
so cuts, clicks and reveals land on sound.  Output: music.wav (48 kHz, stereo, 16-bit).
"""
import sys
import wave
import numpy as np

SR = 48000
DUR = 34.0
N = int(SR * DUR)
rng = np.random.default_rng(42)
BEAT = 0.5          # 120 BPM
BAR = 2.0


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


class Bus:
    def __init__(self):
        self.l = np.zeros(N)
        self.r = np.zeros(N)

    def add(self, sig, at, gain=1.0, pan=0.0):
        if sig.ndim == 1:
            a = np.cos((pan + 1) * np.pi / 4)
            b = np.sin((pan + 1) * np.pi / 4)
            sl, sr_ = sig * a * np.sqrt(2), sig * b * np.sqrt(2)
        else:
            sl, sr_ = sig[0], sig[1]
        i = int(round(at * SR))
        if i >= N:
            return
        j = min(N, i + len(sl))
        self.l[i:j] += sl[:j - i] * gain
        self.r[i:j] += sr_[:j - i] * gain

    def stereo(self):
        return np.stack([self.l, self.r])


def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo:
        m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        m *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X * m, len(x))


def svf(x, cut, q=0.7, mode='lp'):
    """State-variable filter with per-sample cutoff (array or scalar)."""
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


def env_adsr(n, a=0.01, r=0.2, sus=1.0):
    e = np.full(n, sus)
    na, nr = int(a * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, sus, na)
    if nr and n > na:
        nr = min(nr, n - na)
        e[n - nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def norm_rms(x, target_db):
    rms = np.sqrt(np.mean(x[np.abs(x) > 1e-5] ** 2) + 1e-12)
    return x * (10 ** (target_db / 20) / rms)


# ---------------------------------------------------------------- harmony
# Fmaj7 - G - Em7 - Am7, one chord per bar; outro resolves to a lush Fmaj9.
CHORDS = [[53, 57, 60, 64], [55, 59, 62, 67], [52, 55, 59, 62], [57, 60, 64, 67]]
ROOTS = [41, 43, 40, 45]
OUTRO = [53, 57, 60, 64, 67, 72]


def chord_at(bar):
    return OUTRO if bar >= 15 else CHORDS[bar % 4]


def root_at(bar):
    return 41 if bar >= 15 else ROOTS[bar % 4]


# ---------------------------------------------------------------- instruments
def pad_note(m, d):
    t = tvec(d)
    out = np.zeros((2, len(t)))
    for v, (det, pan) in enumerate([(-0.11, -0.7), (0.0, 0.0), (0.12, 0.7)]):
        f0 = midi(m + det)
        s = np.zeros(len(t))
        ph = rng.uniform(0, 2 * np.pi, 14)
        for h in range(1, 15):
            if f0 * h > 9000:
                break
            s += np.sin(2 * np.pi * f0 * h * t + ph[h - 1]) / h * np.exp(-h * 0.32)
        s *= 1 + 0.15 * np.sin(2 * np.pi * (0.3 + v * 0.07) * t)
        a, b = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        out[0] += s * a
        out[1] += s * b
    return out * env_adsr(len(t), a=0.35, r=0.7)


def kick():
    t = tvec(0.5)
    f = 46 + 120 * np.exp(-t * 30)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 6.5)
    click = rng.standard_normal(len(t)) * np.exp(-t * 400) * 0.35
    return np.tanh((s + click) * 1.6)


def clap():
    t = tvec(0.35)
    n = rng.standard_normal(len(t))
    e = np.zeros(len(t))
    for off in (0, 0.011, 0.022):
        e += np.where(t >= off, np.exp(-(t - off) * 60), 0) * 0.6
    e += np.where(t >= 0.03, np.exp(-(t - 0.03) * 14), 0)
    return fft_filter(n * e, lo=900, hi=6500)


def hat(open_=False):
    t = tvec(0.25 if open_ else 0.08)
    n = rng.standard_normal(len(t))
    return fft_filter(n, lo=7000) * np.exp(-t * (14 if open_ else 70))


def pluck(m, d=0.4):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for h in range(1, 10, 2):
        s += np.sin(2 * np.pi * f * h * t) / (h * h) * np.exp(-t * (9 + h * 3))
    s += 0.35 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 16)
    return s * env_adsr(len(t), a=0.002, r=0.05)


def bass_note(m, d):
    t = tvec(d)
    f = midi(m)
    s = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(4 * np.pi * f * t) + 0.08 * np.sin(6 * np.pi * f * t)
    return np.tanh(s * 1.3) * env_adsr(len(t), a=0.008, r=0.06)


def bell(m, d=2.2):
    t = tvec(d)
    f = midi(m)
    s = np.zeros(len(t))
    for ratio, amp, dec in [(1, 1, 2.2), (2.0, .5, 3.5), (2.76, .35, 5), (5.4, .2, 8), (8.93, .1, 12)]:
        if f * ratio < 12000:
            s += amp * np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * dec)
    return s * env_adsr(len(t), a=0.002, r=0.1)


def riser(d, f0=300, f1=9000):
    t = tvec(d)
    p = t / d
    n = rng.standard_normal(len(t))
    cut = f0 * (f1 / f0) ** (p ** 1.6)
    s = svf(n, cut, q=2.2, mode='bp') * (p ** 1.8)
    tone = np.sin(2 * np.pi * np.cumsum(220 * 4 ** (p ** 1.5)) / SR) * p ** 2 * 0.15
    return s + tone


def whoosh(d=0.7):
    t = tvec(d)
    p = t / d
    n = rng.standard_normal(len(t))
    cut = 400 + 5000 * np.sin(np.pi * p) ** 2
    s = svf(n, cut, q=1.4, mode='bp')
    e = np.sin(np.pi * np.clip(p * 1.1, 0, 1)) ** 2
    return s * e


def impact(d=2.5):
    t = tvec(d)
    f = 34 + 60 * np.exp(-t * 9)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.0)
    n = rng.standard_normal(len(t))
    crash = svf(n, 2500 * np.exp(-t * 2.5) + 300, q=0.8) * np.exp(-t * 3.0)
    air = fft_filter(n, lo=5000) * np.exp(-t * 4.0) * 0.4
    return np.tanh(boom * 1.4) + crash * 0.8 + air


def ui_click(pitch=2400):
    t = tvec(0.06)
    blip = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 90)
    tick = fft_filter(rng.standard_normal(len(t)), lo=3000) * np.exp(-t * 500)
    return blip * 0.7 + tick * 0.5


def pop(f0=700, f1=1300, d=0.09):
    t = tvec(d)
    f = f0 + (f1 - f0) * (1 - np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45)


# ---------------------------------------------------------------- arrangement
pad, bass, drums, arp, fx, verb_send = Bus(), Bus(), Bus(), Bus(), Bus(), Bus()
kick_times = []

for bar in range(17):
    t0 = bar * BAR
    ch = chord_at(bar)
    d = 4.2 if bar == 15 else BAR + 0.6
    if bar == 16:
        continue
    for m in ch:
        pad.add(pad_note(m, d), t0)

    in_main = 4.0 <= t0 < 20.0 or 24.0 <= t0 < 30.0
    in_break = 20.0 <= t0 < 24.0
    for b in range(4):
        tb = t0 + b * BEAT
        if in_main:
            kick_times.append(tb)
            drums.add(kick(), tb, 1.0)
            if (8.0 <= tb < 20.0 or 24.0 <= tb < 30.0) and b in (1, 3):
                drums.add(clap(), tb, 0.55, pan=0.05)
                verb_send.add(clap(), tb, 0.25)
        if in_main or in_break:
            drums.add(hat(), tb + 0.25, 0.42, pan=0.25)
            if 24.0 <= tb < 30.0:
                drums.add(hat(), tb + 0.125, 0.18, pan=-0.25)
                drums.add(hat(), tb + 0.375, 0.18, pan=-0.25)
        # bass: pumping eighths on the off-beats + root on the beat
        if in_main:
            r = root_at(bar)
            bass.add(bass_note(r, 0.22), tb + 0.0, 0.8)
            bass.add(bass_note(r + 12 if b == 3 else r, 0.2), tb + 0.25, 1.0)

    # 16th-note arpeggio from bar 4 (8 s), thinner in the break
    if 8.0 <= t0 < 30.0:
        pattern = [0, 1, 2, 3, 4, 3, 2, 1]
        notes = [m + 12 for m in ch] + [ch[0] + 24]
        for k in range(16):
            m = notes[pattern[k % 8]]
            if in_break and k % 2:
                continue
            g = 0.55 if k % 4 == 0 else 0.38
            arp.add(pluck(m), t0 + k * 0.125, g, pan=0.35 if k % 2 else -0.35)
            verb_send.add(pluck(m), t0 + k * 0.125, g * 0.6)
    elif 4.0 <= t0 < 8.0:
        for k in range(8):
            m = ch[[0, 2, 1, 3][k % 4]] + 12
            arp.add(pluck(m), t0 + k * 0.25, 0.45, pan=0.3 if k % 2 else -0.3)
            verb_send.add(pluck(m), t0 + k * 0.25, 0.3)

# final hit
kick_times.append(30.0)
drums.add(kick(), 30.0, 1.0)
bass.add(bass_note(29, 3.4) * np.exp(-tvec(3.4) * 0.8), 30.0, 0.9)

# ---------------------------------------------------------------- sound design on picture cues
fx.add(bell(84, 3.0), 0.28, 0.5, pan=0.1); verb_send.add(bell(84, 3.0), 0.28, 0.9)
fx.add(bell(91, 2.5), 0.32, 0.25, pan=-0.2); verb_send.add(bell(91, 2.5), 0.32, 0.5)
fx.add(whoosh(0.8), 0.25, 0.5, pan=-0.3)
fx.add(whoosh(1.0), 0.95, 0.35, pan=0.4)                     # star flies into the logo
for i, m in enumerate([72, 76, 79, 84, 88, 91]):              # letters land
    fx.add(pluck(m, 0.5), 1.15 + i * 0.065, 0.28, pan=-0.5 + i * 0.2)
    verb_send.add(pluck(m, 0.5), 1.15 + i * 0.065, 0.35)
fx.add(bell(96, 2.0), 2.55, 0.22, pan=0.4); verb_send.add(bell(96, 2.0), 2.55, 0.5)

for at, d in [(3.0, 1.0), (23.0, 1.0), (29.0, 1.0)]:
    fx.add(riser(d), at, 0.55)
for at, g in [(4.0, 1.0), (24.0, 1.0), (30.0, 1.15)]:
    fx.add(impact(), at, g)
    verb_send.add(impact() * 0.5, at, 0.4)
fx.add(impact(1.5) * 0.5, 14.0, 0.5)

for at, pan in [(7.55, -0.5), (12.5, 0.4), (19.6, -0.4), (23.55, 0.3), (29.45, -0.3)]:
    fx.add(whoosh(0.7), at, 0.55, pan=pan)

for at, p in [(12.3, 2400), (16.55, 2100), (17.32, 1800), (17.98, 2400), (27.72, 2400)]:
    fx.add(ui_click(p), at, 0.5, pan=0.2)
for i in range(4):                                            # feature ticks
    fx.add(pop(800 + i * 120, 1400 + i * 150), 25.55 + i * 0.25, 0.35, pan=-0.2)
for i, at in enumerate([20.45, 21.55, 22.65]):                # process nodes
    m = [76, 79, 84][i]
    fx.add(pluck(m, 0.8), at, 0.6); verb_send.add(pluck(m, 0.8), at, 0.6)
    fx.add(pop(600, 1100), at, 0.25)
# price count-up ticks (eased like the on-screen counter)
for k in range(1, 26):
    p = k / 25
    at = 25.0 + 1.3 * (1 - (1 - p) ** (1 / 3))
    fx.add(ui_click(1400 + 1600 * p) * 0.6, at, 0.35, pan=0.1)
fx.add(bell(88, 2.0), 26.25, 0.35); verb_send.add(bell(88, 2.0), 26.25, 0.6)
fx.add(bell(84, 1.8), 19.05, 0.3); fx.add(bell(91, 1.8), 19.12, 0.25); verb_send.add(bell(91, 1.8), 19.1, 0.5)
for i, m in enumerate([84, 88, 91, 96]):                      # CTA sparkle burst
    fx.add(bell(m, 1.6), 27.76 + i * 0.05, 0.2, pan=-0.4 + i * 0.25)
    verb_send.add(bell(m, 1.6), 27.76 + i * 0.05, 0.4)
fx.add(bell(91, 2.5), 30.42, 0.3); verb_send.add(bell(91, 2.5), 30.42, 0.7)
fx.add(whoosh(1.1), 31.65, 0.3, pan=0.5)                      # logo shine
fx.add(bell(96, 2.0), 32.6, 0.2); verb_send.add(bell(96, 2.0), 32.6, 0.5)

# ---------------------------------------------------------------- mix
tt = np.arange(N) / SR
duck = np.ones(N)
for k in kick_times:
    i = int(k * SR)
    seg = tt[i:] - k
    duck[i:] = np.minimum(duck[i:], 1 - 0.6 * np.exp(-seg / 0.11))

pad_st = pad.stereo()
pad_st = np.stack([fft_filter(ch, lo=120, hi=5200) for ch in pad_st])
pad_auto = np.interp(tt, [0, 3.8, 4.0, 20, 20.5, 23.8, 24, 30, 30.2, 34], [0.0, 0.85, 0.75, 0.75, 0.95, 1.0, 0.7, 0.7, 0.85, 0.8])
pad_st *= pad_auto * duck
bass_st = bass.stereo() * duck
arp_st = np.stack([fft_filter(ch, lo=250) for ch in arp.stereo()]) * (0.6 + 0.4 * duck)

# simple dotted-eighth echo on the arp
dly = int(0.375 * SR)
echo = np.zeros_like(arp_st)
for n_rep, g in enumerate([0.32, 0.16, 0.08], start=1):
    s = dly * n_rep
    echo[0, s:] += arp_st[1, :-s] * g
    echo[1, s:] += arp_st[0, :-s] * g
arp_st = arp_st + echo

stems = {
    'pad': norm_rms(pad_st, -21),
    'bass': norm_rms(bass_st, -20),
    'drums': norm_rms(drums.stereo(), -19),
    'arp': norm_rms(arp_st, -27),
    'fx': norm_rms(fx.stereo(), -22),
}

# reverb: FFT convolution with a synthetic decaying-noise impulse
ir_t = tvec(2.6)
ir = np.stack([rng.standard_normal(len(ir_t)), rng.standard_normal(len(ir_t))]) * np.exp(-ir_t * 2.6)
ir = np.stack([fft_filter(c, lo=200, hi=7000) for c in ir])
ir /= np.sqrt(np.sum(ir ** 2, axis=1, keepdims=True))
send = verb_send.stereo()
L = N + len(ir_t)
nfft = 1 << (L - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[c], nfft) * np.fft.rfft(ir[c], nfft), nfft)[:N] for c in range(2)])
wet = norm_rms(wet, -27)

mix = sum(stems.values()) + wet
mix = np.stack([fft_filter(c, lo=28) for c in mix])

# master: gentle glue + soft clip, fades
mix = np.tanh(mix * 1.15) / np.tanh(1.15)
fade = np.ones(N)
fi = int(0.05 * SR)
fade[:fi] = np.linspace(0, 1, fi)
fo0 = int(33.2 * SR)
fade[fo0:] = np.linspace(1, 0, N - fo0) ** 1.5
mix *= fade
mix *= 10 ** (-2.5 / 20) / np.max(np.abs(mix))

out = sys.argv[1] if len(sys.argv) > 1 else 'music.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix.T * 32767).astype('<i2').tobytes())
print('wrote', out, f'{DUR}s')
