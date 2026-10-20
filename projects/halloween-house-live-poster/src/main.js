import * as THREE from "three";
import { gsap } from "gsap";
import { vertexShader, fragmentShader } from "./shader.js";
import { BatLayer, SWARM_SPAN } from "./bats.js";
import { createLetters, addTextTimeline, writeLetterUniforms } from "./text.js";

export const LOOP = 12;
const STAGE = { w: 1080, h: 1920 };
const POSTER = { x: 0, y: 150, w: 1080, h: 1620 };
const params = new URLSearchParams(location.search);
const RENDER_MODE = params.has("render");

// ---------------------------------------------------------------------------
// Choreography. Every value returns to its starting point by the end of the
// loop, so the poster can repeat forever without a visible seam.
// ---------------------------------------------------------------------------
const fx = {
  gust: 0.35, gold: 0, blood: 0, moonGlow: 1, flash: 0, punch: 0,
  door: 1, figureX: 540, line: 0, burst: 0, sheen: -200, tremble: 0, lineDraw: 1,
};
let letters = null; // per-letter state, added once assets/letters.json loads

const tl = gsap.timeline({ paused: true, defaults: { ease: "sine.inOut" } });
tl.addLabel("bell", 0.15)
  .to(fx, { line: 1, duration: 0.35, ease: "power2.out" }, "bell")
  .to(fx, { line: 0, duration: 2.2 }, "bell+=0.35")
  // the moon warms to amber, then cools back
  .to(fx, { gold: 0.55, duration: 3.0 }, 0.4)
  .to(fx, { gold: 0, duration: 2.2 }, 3.6)
  // a first gust through the trees
  .to(fx, { gust: 1, duration: 1.4 }, 0.8)
  .to(fx, { gust: 0.35, duration: 1.8 }, 2.2)
  // the front door creaks open and the porch light swells
  .addLabel("door", 2.4)
  .to(fx, { door: 1.7, duration: 1.4, ease: "power2.inOut" }, "door")
  // someone walks past the gable window, pauses, moves on
  .addLabel("figure", 3.3)
  .to(fx, { figureX: 588, duration: 1.0 }, "figure")
  .to(fx, { figureX: 624, duration: 1.0, ease: "power1.in" }, "figure+=1.6")
  // lightning: double flash, small camera jolt, blood moon, storm gust, bats
  .addLabel("strike", 6.0)
  .to(fx, {
    keyframes: [
      { flash: 1, duration: 0.05, ease: "none" },
      { flash: 0.18, duration: 0.09, ease: "power1.out" },
      { flash: 0.95, duration: 0.05, ease: "none" },
      { flash: 0, duration: 0.9, ease: "expo.out" },
    ],
  }, "strike")
  .to(fx, {
    keyframes: [
      { flash: 0.3, duration: 0.06, ease: "none" },
      { flash: 0, duration: 0.35, ease: "power2.out" },
    ],
  }, "strike+=1.3")
  .to(fx, { punch: 1, duration: 0.08, ease: "power2.out" }, "strike")
  .to(fx, { punch: 0, duration: 1.6, ease: "power3.out" }, "strike+=0.08")
  .to(fx, { blood: 0.9, duration: 1.6, ease: "power2.out" }, "strike+=0.05")
  .to(fx, { moonGlow: 1.25, duration: 1.0, ease: "power2.out" }, "strike+=0.05")
  .to(fx, { moonGlow: 1, duration: 4.4 }, "strike+=1.2")
  .to(fx, { gust: 1.25, duration: 0.6, ease: "power2.out" }, "strike+=0.2")
  .to(fx, { gust: 0.35, duration: 4.0 }, "strike+=0.9")
  .to(fx, { burst: SWARM_SPAN, duration: SWARM_SPAN, ease: "none" }, "strike+=0.2")
  // everything settles back for the loop
  .to(fx, { blood: 0, duration: 2.8 }, 9.0)
  .to(fx, { door: 1, duration: 2.0 }, 9.6)
  .set(fx, { figureX: 540 }, 11.9)
  .set({}, {}, LOOP);

// ---------------------------------------------------------------------------
// Renderer
// ---------------------------------------------------------------------------
const canvas = document.getElementById("stage");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(STAGE.w, STAGE.h, false);
renderer.outputColorSpace = THREE.LinearSRGBColorSpace;

const loader = new THREE.TextureLoader();
const load = (url, { repeat = false, nearest = false } = {}) =>
  loader.loadAsync(url).then((t) => {
    t.colorSpace = THREE.NoColorSpace;
    t.generateMipmaps = false;
    t.minFilter = t.magFilter = nearest ? THREE.NearestFilter : THREE.LinearFilter;
    if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
    return t;
  });

const bats = new BatLayer(POSTER.w, POSTER.h);
const canvasTexture = (c) => {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.NoColorSpace;
  t.premultiplyAlpha = true;
  t.generateMipmaps = false;
  t.minFilter = THREE.LinearFilter;
  return t;
};
const batsFront = canvasTexture(bats.front);
const batsBack = canvasTexture(bats.back);

const uniforms = {
  tPoster: { value: null }, tMask1: { value: null }, tMask2: { value: null },
  tMask3: { value: null }, tNoise: { value: null }, tText: { value: null }, tLetters: { value: null },
  uLetters: { value: Array.from({ length: 64 }, () => new THREE.Vector4(0, 0, 1, 1)) },
  uSheen: { value: -200 }, uLineDraw: { value: 1 },
  tBatsFront: { value: batsFront }, tBatsBack: { value: batsBack },
  uStage: { value: new THREE.Vector2(STAGE.w, STAGE.h) },
  uPoster: { value: new THREE.Vector4(POSTER.x, POSTER.y, POSTER.w, POSTER.h) },
  uTime: { value: 0 }, uLoop: { value: LOOP }, uFrame: { value: 0 },
  uZoom: { value: 1 }, uGust: { value: 0 }, uGold: { value: 0 }, uBlood: { value: 0 },
  uMoonGlow: { value: 1 }, uFlash: { value: 0 }, uDoor: { value: 1 },
  uFigureX: { value: 540 }, uLine: { value: 0 },
};

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
scene.add(new THREE.Mesh(
  new THREE.PlaneGeometry(2, 2),
  new THREE.ShaderMaterial({ uniforms, vertexShader, fragmentShader, depthTest: false }),
));

function renderAt(t, frame = Math.round(t * 60)) {
  t = gsap.utils.wrap(0, LOOP, t);
  tl.time(t);
  const breathe = 0.5 - 0.5 * Math.cos((Math.PI * 2 * t) / LOOP);
  const u = uniforms;
  u.uTime.value = t;
  u.uFrame.value = frame % 997;
  u.uZoom.value = 1 + 0.022 * breathe + 0.012 * fx.punch;
  u.uGust.value = fx.gust;
  u.uGold.value = fx.gold;
  u.uBlood.value = fx.blood;
  u.uMoonGlow.value = fx.moonGlow;
  u.uFlash.value = fx.flash;
  u.uDoor.value = fx.door;
  u.uFigureX.value = fx.figureX;
  u.uLine.value = fx.line;
  u.uLineDraw.value = fx.lineDraw;
  u.uSheen.value = fx.sheen;
  if (letters) writeLetterUniforms(u.uLetters.value, letters, t, LOOP, fx);
  bats.draw(t, LOOP, fx);
  batsFront.needsUpdate = true;
  batsBack.needsUpdate = true;
  renderer.render(scene, camera);
}

const ready = Promise.all([
  load("./assets/poster.webp"), load("./assets/masks1.png"), load("./assets/masks2.png"),
  load("./assets/masks3.png"), load("./assets/noise.png", { repeat: true }),
  load("./assets/masks4.png"), load("./assets/letters.png", { nearest: true }),
  fetch("./assets/letters.json").then((r) => r.json()),
]).then(([poster, m1, m2, m3, noise, m4, letterMap, letterMeta]) => {
  uniforms.tPoster.value = poster;
  uniforms.tMask1.value = m1;
  uniforms.tMask2.value = m2;
  uniforms.tMask3.value = m3;
  uniforms.tNoise.value = noise;
  uniforms.tText.value = m4;
  uniforms.tLetters.value = letterMap;
  letters = createLetters(letterMeta);
  addTextTimeline(tl, letters, fx);
  renderAt(0);
});

window.livePoster = { ready, renderAt, LOOP, STAGE };

// ---------------------------------------------------------------------------
// Live playback (skipped when a renderer drives frames via ?render)
// ---------------------------------------------------------------------------
if (!RENDER_MODE) {
  document.body.classList.add("live");
  const audio = document.getElementById("soundtrack");
  const button = document.getElementById("sound");
  const start = performance.now();
  button.addEventListener("click", () => {
    if (audio.paused) {
      audio.currentTime = (((performance.now() - start) / 1000) % LOOP);
      audio.play();
      button.textContent = "Sound on";
      button.setAttribute("aria-pressed", "true");
    } else {
      audio.pause();
      button.textContent = "Tap for sound";
      button.setAttribute("aria-pressed", "false");
    }
  });
  ready.then(() => {
    gsap.ticker.add(() => {
      const t = audio.paused ? (performance.now() - start) / 1000 : audio.currentTime;
      renderAt(t);
    });
  });
}
