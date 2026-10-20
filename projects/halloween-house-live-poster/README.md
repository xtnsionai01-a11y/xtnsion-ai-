# Halloween House — live poster

The *Halloween House* invite poster brought to life as a 12-second seamless loop
with sound, for Reels, Stories, WhatsApp status and the Instagram feed.

| File | Use |
| --- | --- |
| `output/halloween-house-live-poster_9x16.mp4` | Reels, Stories, WhatsApp status (1080×1920, 60 fps) |
| `output/halloween-house-live-poster_4x5.mp4` | Instagram feed post (1080×1350, 60 fps) |
| `index.html` | The same poster running live in a browser, with a sound toggle |

## What moves

| Time | Moment |
| --- | --- |
| 0.0 s | A distant church bell tolls; the orange divider glows |
| 0.25–1.7 s | TRICK OR TREAT lights up letter by letter with glassy sparkles; a gleam sweeps across HALLOWEEN |
| 0.4–5.8 s | The moon warms from orange to amber and back |
| 0.8–4.0 s | A gust sways the trees and foliage (they sway gently all the time) |
| 1.2 s | An owl hoots |
| 2.4 s | The front door creaks open and the porch light swells |
| 2.7 s | A shimmer runs along INVITE ONLY HOUSEPARTY |
| 3.3–5.9 s | A figure walks past the gable window, pauses, moves on |
| 5.0–6.0 s | The title trembles, buzzes and flickers out letter by letter |
| 6.0 s | Lightning: a double flash lights up the house, with thunder; the title slams back on white-hot, HALLOWEEN bounces in from above, HOUSE glitches |
| 6.2–9.5 s | A swarm of bats bursts from behind the roof, two swoop at the camera |
| 6.0–11.8 s | The moon turns blood red, then fades back to orange |
| 9.45–11 s | Save the date: the divider retracts and redraws, the date glows from its centre out with a chime |
| always | HALLOWEEN floats on a slow wave, HOUSE flickers like candlelight, bats circle the house, candlelit windows flicker, mist drifts through the garden, fireflies blink, clouds pass over the moon, slow push-in, film grain |

Every motion completes a whole number of cycles per loop, so the video repeats
with no visible or audible seam.

## How it is built

- `src/shader.js`: a three.js fragment shader that animates the original
  artwork in place, using masks for the moon, foliage, lights and lettering.
- `src/main.js`: the GSAP timeline that choreographs every moment above,
  shared by live playback and the frame-by-frame render.
- `src/text.js`: per-letter text animation. The lettering stays the artwork's
  own; each of its 59 letters is lifted off and redrawn with its own offset,
  opacity and brightness, choreographed with GSAP staggers.
- `src/bats.js`: wing-flapping bat silhouettes and fireflies on canvas.
- `tools/build_masks.py`: generates `assets/masks*.png`, `assets/noise.png` and
  the per-letter lookup (`assets/letters.png`, `assets/letters.json`) from the poster.
- `tools/build_audio.py`: mixes the soundtrack from the ElevenLabs sound effects
  in `assets/sfx/` plus synthesised wind, drone, crickets, riser, sub hit, and the
  buzz, crackle and sparkles that follow the lettering.
- `tools/render.mjs`: renders frames in headless Chromium and pipes them to FFmpeg.
- `tools/export.sh`: muxes video and audio into the delivery formats.

## Rebuild

```sh
npm install
python3 tools/build_masks.py assets/poster.webp assets          # only if the artwork changes
python3 tools/build_audio.py assets/sfx assets/soundtrack.wav
node tools/render.mjs --fps 60 --out work/video_60fps.mp4      # about 8 minutes
tools/export.sh work/video_60fps.mp4 assets/soundtrack.wav output
```

Preview single frames with `node tools/render.mjs --stills 0,6.05,7.5`.
To view it live, serve the folder (for example `npx serve .`) and open `index.html`.
