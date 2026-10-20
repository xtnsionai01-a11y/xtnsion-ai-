"""Builds the 12 s seamless soundtrack for the live poster.

Procedural layers (wind, drone, crickets, riser, sub hit) are synthesised to be
exactly periodic, and every one-shot effect is mixed into a circular buffer, so
the end of the loop flows straight back into its start. Event times match the
GSAP timeline in src/main.js.

usage: python3 tools/build_audio.py <sfx dir> <output.wav>
Optional SFX files in <sfx dir> (mp3, generated with ElevenLabs Sound Effects):
thunder_long, bats, owl, door, bell, ambience. Missing ones are skipped or
synthesised.
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
LOOP = 12.0
N = int(SR * LOOP)
rng = np.random.default_rng(31)
t = np.arange(N) / SR
SFX = Path(sys.argv[1])
OUT = Path(sys.argv[2])


def load(name):
    f = SFX / f"{name}.mp3"
    if not f.exists():
        return None
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-f", "s16le", "-ac", "2",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).reshape(-1, 2).astype(np.float64) / 32768


def place(buf, sound, at, gain=1.0, pan=0.0, fade_out=0.0):
    """Mixes `sound` into the circular stereo buffer starting at `at` seconds."""
    s = sound.copy() if sound.ndim == 2 else np.stack([sound, sound], 1)
    if fade_out:
        n = min(len(s), int(fade_out * SR))
        s[-n:] *= np.linspace(1, 0, n)[:, None] ** 2
    lg, rg = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    s = s * gain * np.array([lg, rg]) * np.sqrt(2)
    idx = (int(round(at * SR)) + np.arange(len(s))) % N
    np.add.at(buf, idx, s)


def shaped_noise(lo, hi, slope=1.0, seed=0):
    """Periodic band-limited noise (FFT synthesis is circular by construction)."""
    r = np.random.default_rng(seed)
    spec = r.standard_normal(N // 2 + 1) + 1j * r.standard_normal(N // 2 + 1)
    f = np.fft.rfftfreq(N, 1 / SR)
    band = np.clip((f - lo * 0.7) / (lo * 0.3), 0, 1) * np.clip((hi * 1.3 - f) / (hi * 0.3), 0, 1)
    spec *= band / np.maximum(f, 1) ** (slope / 2)
    x = np.fft.irfft(spec, N)
    return x / (np.abs(x).max() + 1e-12)


def periodic_lfo(cycles_max, seed):
    """Smooth random modulation in [0, 1] that loops."""
    r = np.random.default_rng(seed)
    x = np.zeros(N)
    for k in range(1, cycles_max + 1):
        x += r.standard_normal() / k * np.sin(2 * np.pi * k * t / LOOP + r.uniform(0, 2 * np.pi))
    return (x - x.min()) / (x.max() - x.min())


def ease_track(points):
    """Piecewise sine-eased curve through (time, value) points, like the GSAP tweens."""
    y = np.empty(N)
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        m = (t >= t0) & (t <= t1)
        k = (t[m] - t0) / max(t1 - t0, 1e-9)
        y[m] = v0 + (v1 - v0) * (0.5 - 0.5 * np.cos(np.pi * k))
    return y


def highpass(x, fc):
    spec = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    spec *= (1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** 4))[:, None]
    return np.fft.irfft(spec, len(x), axis=0)


def reverb(x, seconds=2.6, seed=7):
    """Circular convolution with a decaying stereo noise tail."""
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    env = np.exp(-np.arange(n) / SR * 6.9 / seconds)
    ir = r.standard_normal((n, 2)) * env[:, None]
    ir[:, 0] = np.convolve(ir[:, 0], np.ones(8) / 8, "same")  # soften the tail
    ir[:, 1] = np.convolve(ir[:, 1], np.ones(8) / 8, "same")
    ir /= np.sqrt((ir ** 2).sum(0))
    pad = np.zeros((N, 2))
    pad[:n] = ir
    return np.fft.irfft(np.fft.rfft(x, axis=0) * np.fft.rfft(pad, axis=0), N, axis=0)


mix = np.zeros((N, 2))
verb = np.zeros((N, 2))

# --- wind: broadband air plus two whistling resonances, swelling with the gusts
gust = ease_track([(0, .35), (.8, .35), (2.2, 1), (4.0, .35), (6.2, .35), (6.8, 1.25),
                   (6.9, 1.25), (10.9, .35), (12, .35)])
wobble = periodic_lfo(9, 1)
air = np.stack([shaped_noise(120, 2400, 1.2, 11), shaped_noise(120, 2400, 1.2, 12)], 1)
howl = np.stack([shaped_noise(380, 470, 0, 13) + 0.6 * shaped_noise(600, 690, 0, 14),
                 shaped_noise(400, 490, 0, 15) + 0.6 * shaped_noise(620, 710, 0, 16)], 1)
wind_amp = (0.35 + 0.65 * gust / 1.25) * (0.75 + 0.25 * wobble)
mix += air * (0.07 * wind_amp)[:, None]
mix += howl * (0.035 * wind_amp ** 1.6)[:, None]

# --- ominous drone: whole-cycle frequencies so the loop seam is inaudible
drone = np.zeros(N)
for cycles, amp in [(660, 1.0), (699, 0.45), (989, 0.35), (1320, 0.25), (2797, 0.08)]:
    f = cycles / LOOP
    drone += amp * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
drone *= 0.6 + 0.4 * periodic_lfo(4, 2)
mix += np.stack([drone, np.roll(drone, 900)], 1) * 0.032

# --- crickets in the garden, sparse and soft
cr_t = np.arange(int(0.09 * SR)) / SR
pulses = (np.sin(2 * np.pi * 33 * cr_t) > 0.2).astype(float)
chirp = np.sin(2 * np.pi * 4650 * cr_t) * pulses * np.hanning(len(cr_t))
for i, at in enumerate(np.arange(0.3, LOOP, 0.83)):
    if 5.9 < at < 8.3:
        continue  # the storm hushes the crickets
    place(mix, chirp, at + rng.uniform(-0.08, 0.08), 0.012 * rng.uniform(0.6, 1.0),
          pan=rng.uniform(-0.8, 0.8))

# --- tension riser into the lightning, then a sub-bass hit on the flash
rn = int(1.35 * SR)
riser_t = np.arange(rn) / SR
riser_noise = shaped_noise(300, 6000, 0.6, 21)[:rn]
riser = riser_noise * (riser_t / riser_t[-1]) ** 3 * 0.09
riser[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
place(mix, riser, 6.0 - 1.35, pan=0)
hn = int(2.2 * SR)
ht = np.arange(hn) / SR
freq = 34 + 40 * np.exp(-ht * 5)
hit = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-ht * 2.2)
hit = np.tanh(hit * 2.2) / np.tanh(2.2)
place(mix, hit, 6.0, gain=0.42)

# --- lettering: a buzz and crackle as the title's lights fail before the strike,
# glassy sparkles as letters light up (times follow src/text.js)
from scipy.signal import butter, lfilter
bn = int(1.02 * SR)
bt = np.arange(bn) / SR
saw = 2 * ((bt * 100) % 1) - 1
b_, a_ = butter(2, [180, 2400], "bandpass", fs=SR)
buzz = lfilter(b_, a_, saw) * (bt / bt[-1]) ** 2.2
buzz[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
place(mix, buzz / np.abs(buzz).max(), 4.95, gain=0.05, pan=0.0)
b_, a_ = butter(2, [1800, 7000], "bandpass", fs=SR)
for j in range(26):  # one crackle each time a letter cuts out or sputters back
    for dt in (0.0, 0.05, 0.11):
        n = int(rng.uniform(0.008, 0.025) * SR)
        burst = lfilter(b_, a_, rng.standard_normal(n)) * np.hanning(n)
        place(mix, burst / (np.abs(burst).max() + 1e-9), 5.33 + j * 0.017 + dt,
              gain=rng.uniform(0.04, 0.09), pan=rng.uniform(-0.5, 0.5))


def sparkle(freq, length=0.9):
    st = np.arange(int(length * SR)) / SR
    tone = sum(a * np.sin(2 * np.pi * freq * r * st) for r, a in [(1, 1), (2.76, 0.4), (5.4, 0.15)])
    return tone * np.exp(-st * 6) * np.minimum(st / 0.003, 1)


notes = [1568, 1760, 2093, 2349, 2637, 3136]
for k in range(12):  # TRICK OR TREAT, letter by letter
    place(mix, sparkle(notes[k % 6] * (1 if k < 6 else 2)), 0.33 + k * 0.055, gain=0.012,
          pan=-0.6 + k * 0.1)
    place(verb, sparkle(notes[k % 6]), 0.33 + k * 0.055, gain=0.02)
for k in range(7):  # the date glows from its centre outwards
    place(mix, sparkle(notes[(k + 2) % 6] * 1.5, 1.4), 9.82 + k * 0.04, gain=0.02,
          pan=(-1) ** k * k * 0.12)
    place(verb, sparkle(notes[(k + 2) % 6] * 1.5, 1.4), 9.82 + k * 0.04, gain=0.035)

# --- recorded effects -----------------------------------------------------------
fx = {name: load(name) for name in ["thunder_long", "bats", "owl", "door", "bell", "ambience"]}

if fx["ambience"] is not None:
    amb = fx["ambience"][:N]
    if len(amb) < N:
        amb = np.concatenate([amb, amb[:N - len(amb)]])
    # its own loop point lands under the thunder crack, where nothing can be heard
    place(mix, amb, 6.0, gain=0.38)

if fx["bell"] is not None:
    b = fx["bell"]
    on = np.argmax(np.abs(b).max(1) > 0.2 * np.abs(b).max()) / SR
    place(mix, b, 0.12 - on, gain=0.42, pan=-0.25, fade_out=1.0)
    place(verb, b, 0.12 - on, gain=0.25, pan=-0.25, fade_out=1.0)
else:
    bn = int(6 * SR)
    bt = np.arange(bn) / SR
    bell = np.zeros(bn)
    for ratio, amp, decay in [(0.5, .5, .6), (1, 1, .9), (1.19, .45, 1.4), (1.5, .35, 1.6),
                              (2, .4, 2.2), (2.7, .2, 3.2), (3.9, .12, 4.5)]:
        bell += amp * np.sin(2 * np.pi * 196 * ratio * bt) * np.exp(-bt * decay)
    bell *= np.minimum(bt / 0.004, 1)
    place(mix, bell / np.abs(bell).max(), 0.12, gain=0.26, pan=-0.25)
    place(verb, bell / np.abs(bell).max(), 0.12, gain=0.2, pan=-0.25)

if fx["owl"] is not None:
    o = fx["owl"]
    on = np.argmax(np.abs(o).max(1) > 0.2 * np.abs(o).max()) / SR
    place(mix, o, 1.25 - on, gain=0.55, pan=-0.55, fade_out=0.6)
    place(verb, o, 1.25 - on, gain=0.3, pan=-0.55, fade_out=0.6)

if fx["door"] is not None:
    d = fx["door"]
    on = np.argmax(np.abs(d).max(1) > 0.2 * np.abs(d).max()) / SR
    place(mix, d, 2.45 - on, gain=0.5, pan=0.1, fade_out=0.5)
    place(verb, d, 2.45 - on, gain=0.22, pan=0.1, fade_out=0.5)
else:
    # stick-slip friction: an irregular pulse train exciting wooden resonances
    from scipy.signal import butter, lfilter
    cn = int(1.9 * SR)
    ct = np.arange(cn) / SR
    wander = np.interp(ct, np.linspace(0, ct[-1], 14), rng.uniform(-1, 1, 14))
    rate = 70 + 120 * (ct / ct[-1]) ** 0.7 + 55 * wander
    phase = np.cumsum(rate / SR)
    ticks = np.diff(np.floor(phase), prepend=0) > 0
    pulses = ticks * rng.uniform(0.5, 1.0, cn)
    creak = np.zeros(cn)
    for fc, q, amp in [(310, 6, 1.0), (920, 8, 0.8), (1750, 10, 0.5), (2900, 12, 0.25)]:
        b, a = butter(2, [fc * (1 - 0.5 / q), fc * (1 + 0.5 / q)], "bandpass", fs=SR)
        creak += amp * lfilter(b, a, pulses)
    creak *= np.minimum(ct / 0.12, 1) * np.minimum((ct[-1] - ct) / 0.35, 1)
    creak /= np.abs(creak).max()
    place(mix, creak, 2.45, gain=0.2, pan=0.1)
    place(verb, creak, 2.45, gain=0.14, pan=0.1)

if fx["thunder_long"] is not None:
    th = fx["thunder_long"]
    on = np.argmax(np.abs(th).max(1) > 0.25 * np.abs(th).max()) / SR
    place(mix, th, 6.0 - on, gain=0.85, pan=0.15, fade_out=2.0)
    place(verb, th, 6.0 - on, gain=0.18, pan=0.15, fade_out=2.0)

if fx["bats"] is not None:
    b = fx["bats"]
    on = np.argmax(np.abs(b).max(1) > 0.25 * np.abs(b).max()) / SR
    burst = b * 1.6
    place(mix, burst, 6.25 - on, gain=1.0, pan=-0.2, fade_out=0.8)
    # a delayed, opposite-panned copy widens the swarm as bats scatter both ways
    place(mix, burst, 6.25 - on + 0.11, gain=0.55, pan=0.7, fade_out=0.8)
    # a couple of the circling bats flutter past the listener
    seg = b[int((on + 0.1) * SR):int((on + 0.7) * SR)]
    seg = seg * np.hanning(len(seg))[:, None]
    place(mix, seg, 3.15, gain=0.5, pan=0.6)
    place(mix, seg, 10.35, gain=0.42, pan=-0.6)

mix += reverb(verb) * 0.9

# --- master: high-pass, glue, gentle limiting -----------------------------------
mix = highpass(mix, 28)
rms = np.sqrt((mix ** 2).mean())
mix *= 10 ** (-17 / 20) / rms
peak_ceiling = 10 ** (-1 / 20)
mix = np.tanh(mix / peak_ceiling * 0.95) * peak_ceiling
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}  rms {20 * np.log10(np.sqrt((mix ** 2).mean())):.1f} dBFS  "
      f"peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS  layers: "
      + ", ".join(k for k, v in fx.items() if v is not None))
