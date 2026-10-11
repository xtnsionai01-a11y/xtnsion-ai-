# nxtlvl.ai promo video

A fast, beat-synced, SaaS-style motion graphics promo for **nxtlvl.ai**, a creative marketing company in India that offers motion editors and creative visuals, with a starter pack from ₹999.

**Final video:** [`nxtlvl-promo.mp4`](nxtlvl-promo.mp4) (33 s, 1920×1080, 60 fps, H.264 + AAC)
**First version:** [`nxtlvl-promo-v1.mp4`](nxtlvl-promo-v1.mp4) (calmer 34 s cut, kept for comparison)

## Storyboard (v2)

Every cut lands on a 128 BPM beat grid. The soundtrack and sound effects are generated on the same grid.

| Time | Scene | Motion and transitions |
| --- | --- | --- |
| 0:00 | Star ignite | The sparkle star flares in with a shockwave, light rays and a white flash. |
| 0:01 | Word hammers | **MOTION. VISUALS. BRANDS. NEXT LEVEL.**, one word per beat, each in a different style (solid, outline, inverted, gradient). Speed lines and camera shake on every hit. |
| 0:03 | Logo slam | `nxtlvl` letters slam in, the star flies in, then a shockwave, RGB glitch, synthwave floor grid and a scrambled tagline. |
| 0:03.5 | **Star wipe** | The logo star grows to fill the screen, and the next scene is revealed through a star-shaped mask. |
| 0:04 | Hook | "India's top creative marketing company." flies in word by word, then the words explode outward with a glitch. |
| 0:05.6 | Slot machine | "We make [Reels → Ads → Visuals → Brands] that stop the scroll." Two crossing marquee bands scroll the services. |
| 0:07.3 | **Whip pan** | A horizontal motion-blur whip pan into the services scene. |
| 0:07.5 | Bento grid | A 3D-tilted bento of six live tiles: motion paths, a playing reel with floating hearts, scrolling creative thumbnails, a video timeline, brand construction lines and a growth chart. |
| 0:12 | **Zoom-through** | The cursor clicks Motion Graphics and the camera dives through the tile into the next scene. |
| 0:13 | 3D editor | "Pro motion editors, on demand." A 3D-tilted studio window builds an ad, then **explodes into its layers in 3D** (background, product, type, FX) and snaps back. The cursor exports, and a "Reel ready to post" toast appears. |
| 0:18.5 | **Glitch cut** | RGB split, scanlines and slice displacement. |
| 0:18.75 | Creative wall | An endless 3D wall of ad creatives scrolling in opposite directions behind "Visuals people can't scroll past." |
| 0:22.5 | Process | **Brief. Create. Launch. Level up.**, one per beat, with a story-style progress bar and a snare roll build. |
| 0:24 | Silence, then the drop | "STARTING AT ₹???" scrambles, the audio cuts for half a beat, then **₹999** slams in with rolling slot digits, a shockwave, confetti and a camera shake. |
| 0:25.3 | Pricing card | The price morphs into the Starter Pack card. Features tick in on the beat, service chips orbit the card in 3D, and the cursor clicks "Get started", which sets off a sparkle burst. |
| 0:27.8 | **Circle wipe** | The button explodes into a purple circle wipe. |
| 0:28 | Outro | Logo slam, light rays, floor grid, "Take your brand to the next level.", "Starter pack from ₹999" and nxtlvl.ai, then a final hit with a logo shine. |

## Files

- `index.html`: the whole animation (HTML/CSS + GSAP). Every frame is a pure function of time through `window.seekTo(t)`. Open it in a browser for a silent, looping preview.
- `assets/`: logo letters extracted from the brand logo, plus GSAP.
- `music.py`: synthesises `music.wav` (128 BPM track and all sound effects) with numpy. Every cue is written in beats so it lines up with the picture.
- `render.cjs`: renders frames with Playwright/Chromium across parallel browsers and encodes them with ffmpeg.

## Re-rendering

Requires Node 18+, Playwright (Chromium), Python 3 + numpy, and ffmpeg.

```bash
python3 music.py music.wav
node render.cjs --snap 2.6,10,16.3,25.1   # optional: stills in ./snaps
node render.cjs --out nxtlvl-promo.mp4 --fps 60 --workers 4 --audio music.wav
```

To change any copy (headline, prices, services, features), edit the strings in `index.html` (the scene markup and the arrays in `build()`) and re-render. If you move a beat in the timeline, move the matching cue in `music.py`.
