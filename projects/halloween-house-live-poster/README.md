# Halloween House — live poster

The *Halloween House* invite poster brought to life as a 12-second seamless loop
with sound, for Reels, Stories, WhatsApp status and the Instagram feed.

| File | Use |
| --- | --- |
| `output/halloween-house-live-poster_9x16.mp4` | Reels, Stories, WhatsApp status (1080×1920) |
| `output/halloween-house-live-poster_4x5.mp4` | Instagram feed post (1080×1350) |
| `index.html` | The same poster running live in a browser, with a sound toggle |

## What moves

| Time | Moment |
| --- | --- |
| 0.0 s | A distant church bell tolls; the orange divider glows |
| 0.4–5.8 s | The moon warms from orange to amber and back |
| 0.8–4.0 s | A gust sways the trees and foliage (they sway gently all the time) |
| 1.2 s | An owl hoots |
| 2.4 s | The front door creaks open and the porch light swells |
| 3.3–5.9 s | A figure walks past the gable window, pauses, moves on |
| 6.0 s | Lightning: a double flash lights up the house, with thunder |
| 6.2–9.5 s | A swarm of bats bursts from behind the roof, two swoop at the camera |
| 6.0–11.8 s | The moon turns blood red, then fades back to orange |
| always | Bats circle the house, candlelit windows flicker, mist drifts through the garden, fireflies blink, clouds pass over the moon, slow push-in, film grain |

Every motion completes a whole number of cycles per loop, so the video repeats
with no visible or audible seam.

## How it is built

- `src/shader.js`: a three.js fragment shader that animates the original
  artwork in place, using masks for the moon, foliage, lights and lettering.
- `src/main.js`: the GSAP timeline that choreographs every moment above,
  shared by live playback and the frame-by-frame render.
- `src/bats.js`: wing-flapping bat silhouettes and fireflies on canvas.
- `tools/build_masks.py`: generates `assets/masks*.png` and `assets/noise.png`
  from the poster.
- `tools/build_audio.py`: mixes the soundtrack from the ElevenLabs sound effects
  in `assets/sfx/` plus synthesised wind, drone, crickets, riser and sub hit.
- `tools/render.mjs`: renders frames in headless Chromium and pipes them to FFmpeg.
- `tools/export.sh`: muxes video and audio into the delivery formats.

## Rebuild

```sh
npm install
python3 tools/build_masks.py assets/poster.webp assets          # only if the artwork changes
python3 tools/build_audio.py assets/sfx assets/soundtrack.wav
node tools/render.mjs --fps 30 --out work/video_30fps.mp4      # about 8 minutes
tools/export.sh work/video_30fps.mp4 assets/soundtrack.wav output
```

Preview single frames with `node tools/render.mjs --stills 0,6.05,7.5`.
To view it live, serve the folder (for example `npx serve .`) and open `index.html`.
