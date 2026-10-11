# nxtlvl social promo video

A smooth, glass-style SaaS motion graphics ad for **nxtlvl** ([nxtlvlsocial.com](https://nxtlvlsocial.com)), a creative marketing company in India that offers motion editors and creative visuals, with a starter pack from ₹999.

**Final video:** [`nxtlvl-promo.mp4`](nxtlvl-promo.mp4) (36 s, 1920×1080, 60 fps with real motion blur, H.264 + AAC)

Earlier cuts are kept for comparison: [`nxtlvl-promo-v2.mp4`](nxtlvl-promo-v2.mp4) (fast, glitchy 128 BPM edit) and [`nxtlvl-promo-v1.mp4`](nxtlvl-promo-v1.mp4) (first version).

## Look and feel (v3)

- **Frosted glass UI.** Every panel, card, chip, window, phone bezel and notification is real backdrop-blur glass with a specular edge and a moving light sheen.
- **Glossy 3D shapes** (spheres, rings, a pill and the brand star) float behind the glass, so the frosted blur always has color behind it. They glide to a new arrangement for each scene.
- **No hard cuts.** Scenes flow into each other through shared-element morphs: the logo panel becomes the headline card, the chips become the service cards, a card becomes the app window, and the pricing card becomes the outro panel. There is also a glass-slab wipe.
- **Smooth motion.** Expo/power easing, blur-in reveals, a slowly floating camera, and real motion blur: frames are rendered at 120 fps and blended in pairs down to 60 fps.

## Storyboard

| Time | Scene |
| --- | --- |
| 0:00 | A glass panel materialises among floating shapes. The `nxtlvl` letters rise, the star sparkles in, and the tagline fades up. |
| 0:03.5 | The panel morphs into the hook card: "India's top creative marketing company." Six service chips float in around it. |
| 0:07 | The headline swaps to "Make your brand impossible to ignore." |
| 0:09.5 | The chips morph into a glass bento of live service cards: Motion Graphics, Reels & Shorts, Creative Visuals, Video Editing, Brand Identity and Ad Creatives. A glowing spotlight tours each card behind the glass. |
| 0:15.3 | The Motion Graphics card expands into the "nxtlvl Studio" window, which tilts into 3D. Callouts read "Expert motion editors", "Premium, smooth motion", "On-brand, every frame" and "Ready for every format". The ad explodes into its layers in 3D and reassembles, then exports with a "Reel ready to post" toast. |
| 0:21.7 | A glass slab sweeps across the screen and reveals the next scene. |
| 0:22 | "Content built for every feed." Three glass phones play a reel, a story ad and a feed carousel, with notification toasts. |
| 0:27 | The pricing card rises. The price counts up to **₹999**, features check in, service chips orbit, and the cursor clicks "Get started", which sets off a sparkle burst. |
| 0:31.3 | The pricing card morphs into the outro panel: logo, "Take your brand to the next level.", "Starter pack from ₹999" and **nxtlvlsocial.com**. |

The soundtrack is a 120 BPM glassy future-house bed with chimes, whooshes, bubble pops and notification dings, all generated in code and timed to the animation.

## Files

- `index.html`: the whole animation (HTML/CSS + GSAP). Every frame is a pure function of time through `window.seekTo(t)`. Open it in a browser for a silent, looping preview.
- `assets/`: logo letters extracted from the brand logo, plus GSAP.
- `music.py`: synthesises `music.wav` (music and every sound effect) with numpy.
- `render.cjs`: renders frames with headless Chromium across parallel workers and encodes them with ffmpeg. `--mb 2` captures two sub-frames per output frame and blends them into motion blur.

## Re-rendering

Requires Node 18+, Playwright (Chromium), Python 3 + numpy, and ffmpeg.

```bash
python3 music.py music.wav
node render.cjs --snap 2.6,12.6,19.5,25.5,29.8,35   # optional: stills in ./snaps
node render.cjs --out nxtlvl-promo.mp4 --fps 60 --mb 2 --workers 4 --audio music.wav
```

To change copy (headlines, services, features, price, website), edit the scene markup and the strings in `build()` in `index.html`, then re-render. If you move a cue in the timeline, move the matching cue in `music.py`.
