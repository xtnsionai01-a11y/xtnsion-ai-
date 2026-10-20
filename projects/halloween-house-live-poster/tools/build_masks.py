"""Builds the effect masks and tileable noise used by the live poster shader.

All coordinates are in source-poster pixels (1024 x 1536).

masks1.png  R = foliage sway weight (already scaled by branch height)
            G = emissive light sources (windows, lamps, door, steps)
            B = moon disc (excluding the silhouettes in front of it)
masks2.png  R = "HOUSE" lettering
            G = soft bloom around the emissive lights
            B = cream lettering (title, tagline, date)
masks3.png  R = soft glow around "HOUSE"
            G = soft glow around the cream lettering
            B = illustrated scene area (what a lightning flash lights up)
masks4.png  R = "HALLOWEEN" region, G = "HOUSE" region, B = the three small lines
letters.png 1024 x 8 lookup, one row per text line: R = global letter index of
            each column, G = 255 where the line has a letter
letters.json  the text lines, their rows and letter ranges, for the animation
noise.png   three channels of tileable fBm noise (period = texture size)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

img = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)
H, W, _ = img.shape
R, G, B = img[..., 0], img[..., 1], img[..., 2]
lum = 0.2126 * R + 0.7152 * G + 0.0722 * B
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

MOON_C = (674.5, 853.4)
MOON_R = 147.1


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def poly(points, blur=0.0):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(points, fill=255)
    a = np.asarray(m).astype(np.float32) / 255
    return ndimage.gaussian_filter(a, blur) if blur else a


def rect(x0, y0, x1, y1, pad=0):
    a = np.zeros((H, W), np.float32)
    a[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = 1
    return a


# --- moon -------------------------------------------------------------------
dist = np.hypot(xx - MOON_C[0], yy - MOON_C[1])
disc = smoothstep(MOON_R + 1.5, MOON_R - 1.0, dist)
moon = disc * smoothstep(45, 115, R)

# --- emissive lights ---------------------------------------------------------
light_boxes = [
    (300, 918, 328, 988),    # small left window
    (378, 876, 416, 954),    # middle-left window
    (573, 834, 604, 908),    # gable window
    (358, 1038, 404, 1134),  # lower-left window
    (493, 1050, 514, 1080),  # wall lantern
    (556, 1018, 580, 1048),  # porch lantern
    (538, 1050, 575, 1166),  # open door
    (548, 1166, 668, 1204),  # lit steps
    (598, 1026, 646, 1172),  # porch columns catching light
]
boxes = np.zeros((H, W), np.float32)
for b in light_boxes:
    boxes = np.maximum(boxes, rect(*b, pad=2))
warm = smoothstep(55, 150, R) * smoothstep(1.15, 1.6, R / (G + 1))
bright = smoothstep(150, 220, lum)
emissive = boxes * np.maximum(warm, bright)

bloom = ndimage.gaussian_filter(emissive * (0.5 + R / 510), 14)
bloom /= bloom.max()

# --- foliage sway --------------------------------------------------------------
house = poly([(286, 1180), (286, 905), (380, 790), (600, 752), (750, 985),
              (750, 1180)], blur=3)
windows = ndimage.gaussian_filter(np.clip(boxes, 0, 1), 3)


def height(y0, y1, power=1.4):
    return np.clip((y0 - yy) / (y0 - y1), 0, 1) ** power


left_tree = poly([(95, 718), (480, 718), (480, 790), (300, 830), (292, 1000),
                  (275, 1185), (215, 1185), (95, 1060)], blur=8) * height(1185, 720)
roof_x = 600 + 0.665 * (yy - 757)  # right roof slope, peak (600,757) to eave
right_of_roof = smoothstep(4, 14, xx - roof_x)
right_foliage = poly([(630, 770), (780, 770), (845, 900), (845, 1005), (735, 1005)],
                     blur=6) * right_of_roof * np.clip((1010 - yy) / 210, 0.15, 1) ** 1.2
# Over the moon only pixels near a leaf may move, otherwise the craters wobble.
leaves = disc * smoothstep(110, 50, R)
near_leaf = ndimage.gaussian_filter(ndimage.maximum_filter(leaves, size=9), 2.5)
right_foliage *= np.where(dist < MOON_R + 2, np.clip(near_leaf * 1.4, 0, 1), 1)
right_bush = poly([(735, 950), (890, 950), (905, 1215), (725, 1215)], blur=8) \
    * height(1215, 960, 1.2) * 0.75
porch = poly([(520, 1030), (690, 1030), (700, 1215), (515, 1215)], blur=6)
shrubs = rect(110, 1075, 910, 1228) * height(1228, 1085, 1.0) * 0.45
shrubs = ndimage.gaussian_filter(shrubs, 6) * (1 - porch)

sway = np.maximum.reduce([left_tree * (1 - 0.85 * house), right_foliage, right_bush,
                          shrubs])
sway = np.clip(sway * (1 - windows), 0, 1)

# --- lettering -----------------------------------------------------------------
house_text = rect(270, 505, 775, 702) * smoothstep(90, 150, R) \
    * smoothstep(1.4, 1.9, R / (G + 1))
cream = (rect(115, 215, 910, 655) + rect(240, 1258, 790, 1300)
         + rect(300, 1360, 730, 1402)).clip(0, 1) * smoothstep(110, 170, lum) \
    * smoothstep(1.6, 1.25, R / (G + 1))


def save(name, chans):
    arr = np.stack([np.clip(c, 0, 1) for c in chans], -1)
    Image.fromarray((arr * 255 + 0.5).astype(np.uint8)).save(OUT / name)


save("masks1.png", [sway, emissive, moon])
save("masks2.png", [house_text, bloom, cream])

house_glow = ndimage.gaussian_filter(house_text, 10)
cream_glow = ndimage.gaussian_filter(cream, 8)
scene = ndimage.gaussian_filter(rect(60, 705, 965, 1240), 18)
save("masks3.png", [house_glow / house_glow.max(), cream_glow / cream_glow.max(), scene])


# --- per-letter lookup for the text animation -----------------------------------
# Lines whose letters are spaced apart are split on empty columns; the two
# display words have touching serifs, so their splits were placed by eye.
LINES = [
    # name, row, y range, mask, explicit splits (None = split on gaps)
    ("trick", 0, (215, 270), "cream", None),
    ("halloween", 1, (272, 655), "cream", [257, 335, 401, 462, 540, 650, 724, 798]),
    ("house", 2, (500, 705), "orange", [388, 487, 581, 676]),
    ("invite", 3, (1262, 1300), "cream", None),
    ("date", 4, (1365, 1400), "cream", None),
]
binary = {"cream": (lum > 90) & (R / (G + 1) < 1.45), "orange": (R > 90) & (R / (G + 1) > 1.5)}
lookup = np.zeros((8, W, 3), np.uint8)
regions = {}
bands = {}
meta = []
index = 0
for name, row, (y0, y1), kind, cuts in LINES:
    band = np.zeros((H, W), bool)
    band[y0:y1] = binary[kind][y0:y1]
    if name == "house":
        band[:, :270] = band[:, 770:] = False
    cols = np.nonzero(band.any(0))[0]
    x0, x1 = int(cols.min()), int(cols.max())
    if cuts is None:  # split halfway across each empty gap
        gaps, _ = ndimage.label(~band.any(0)[x0:x1 + 1])
        cuts = [x0 + int(np.mean(np.nonzero(gaps == g)[0])) for g in range(1, gaps.max() + 1)]
    edges = [x0 - 6] + cuts + [x1 + 7]
    letters = []
    for i in range(len(edges) - 1):
        lo, hi = max(edges[i], 0), min(edges[i + 1], W)
        lookup[row, lo:hi, 0] = index + i
        lookup[row, lo:hi, 1] = 255
        letters.append([lo, hi])
    meta.append({"name": name, "row": row, "first": index, "count": len(letters),
                 "letters": letters})
    index += len(letters)
    bands[name] = band
    region = ndimage.binary_fill_holes(ndimage.binary_dilation(band, iterations=6))
    regions[name] = ndimage.gaussian_filter(region.astype(np.float32), 1.2)

# HALLOWEEN and HOUSE nearly touch; keep each word's region off the other's ink
# so a moving letter never drags pieces of its neighbour along.
regions["halloween"] *= 1 - ndimage.binary_dilation(bands["house"], iterations=2)
regions["house"] *= 1 - ndimage.binary_dilation(bands["halloween"], iterations=2)
small = np.maximum.reduce([regions["trick"], regions["invite"], regions["date"]])
save("masks4.png", [regions["halloween"], regions["house"], small])
Image.fromarray(lookup).save(OUT / "letters.png")
(OUT / "letters.json").write_text(json.dumps({"lines": meta, "total": index}, indent=1))

# --- tileable noise ----------------------------------------------------------
def fbm_tile(n, beta, lo, hi, seed):
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)[:, None] ** 2 + np.fft.fftfreq(n)[None, :] ** 2
    f = np.sqrt(f) * n
    amp = np.where((f >= lo) & (f <= hi), 1 / np.maximum(f, 1) ** beta, 0)
    spec = np.fft.fft2(rng.standard_normal((n, n))) * amp
    a = np.real(np.fft.ifft2(spec))
    a = (a - a.mean()) / (a.std() * 4) + 0.5
    return np.clip(a, 0, 1)


N = 512
save("noise.png", [fbm_tile(N, 1.6, 1, 64, 1), fbm_tile(N, 1.4, 2, 96, 2),
                   fbm_tile(N, 1.0, 4, 160, 3)])
print("masks written to", OUT)
