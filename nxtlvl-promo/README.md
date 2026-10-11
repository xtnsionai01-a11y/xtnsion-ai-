# nxtlvl.ai promo video

A 34-second, 1920×1080, 60 fps SaaS-style motion graphics promo for **nxtlvl.ai**, a creative marketing company in India that offers motion editors and creative visuals, with a starter pack from ₹999.

**Final video:** [`nxtlvl-promo.mp4`](nxtlvl-promo.mp4) (H.264 + AAC, landscape 16:9)

## Storyboard

| Time | Scene | What happens |
| --- | --- | --- |
| 0:00–0:04 | Logo reveal | The sparkle star flares in with a lens streak, then flies into place as the `nxtlvl` letters rise in. |
| 0:04–0:08 | Hook | Kinetic type: "India's top creative marketing company." followed by "Motion editors. Creative visuals. Everything in between." |
| 0:08–0:14 | Services | Six glass cards with live mini animations: Motion Graphics, Video Editing, Creative Visuals, Social Media, Brand Identity, Ad Creatives. A cursor clicks Motion Graphics and the card expands. |
| 0:14–0:20 | Editor UI | The "nxtlvl Studio" motion editor: an ad builds itself on the canvas, the playhead runs, the cursor drags a layer, adds a keyframe and exports. A "Reel ready to post" toast follows. |
| 0:20–0:24 | Process | Brief → Create → Level up, linked by an animated progress line. |
| 0:24–0:30 | Pricing | A Starter Pack card counts up to **₹999**, ticks off its features, and the cursor clicks "Get started", which sets off a sparkle burst. |
| 0:30–0:34 | Outro | Logo, "Take your brand to the next level.", "Starter pack from ₹999" and nxtlvl.ai. |

The soundtrack is an original 120 BPM electronic track generated in code. Scene cuts, clicks, the count-up and the reveals all land on its beats and effects.

## Files

- `index.html`: the whole animation (HTML/CSS + GSAP). Every frame is a pure function of time through `window.seekTo(t)`. Open it in a browser for a silent, looping preview.
- `assets/`: logo letters extracted from the brand logo, plus GSAP.
- `music.py`: synthesises `music.wav` with numpy, with every sound effect timed to the picture.
- `render.cjs`: renders frames with Playwright/Chromium and encodes them with ffmpeg.

## Re-rendering

Requires Node 18+, Playwright (Chromium), Python 3 + numpy, and ffmpeg.

```bash
python3 music.py music.wav
node render.cjs --snap 2.6,10,18.7,27   # optional: stills in ./snaps
node render.cjs --out nxtlvl-promo.mp4 --fps 60 --workers 4 --audio music.wav
```

To change any copy (headline, prices, services, features), edit the arrays at the top of the `<script>` in `index.html` (`SVC`, `FEATS`, `CHIPS`, `STEPS`) and re-render.
