// Bats and fireflies, drawn into two transparent canvases that the shader
// composites: `front` sits over everything, `back` only shows through the moon
// (so bats can pass behind the roof). Positions are pure functions of loop
// time, so every frame is reproducible and the loop is seamless.
import { gsap } from "gsap";

const TAU = Math.PI * 2;
const MOON = { x: 674.5, y: 853.4 };
const { interpolate, clamp } = gsap.utils;

// Bats circling the house. `turns` and `flaps` are whole cycles per loop.
const ORBITERS = [
  { cx: 560, cy: 840, rx: 305, ry: 70, turns: 2, dir: 1, phase: 0.4, size: 44, flaps: 54 },
  { cx: 600, cy: 805, rx: 250, ry: 52, turns: 2, dir: -1, phase: 2.6, size: 38, flaps: 60 },
  { cx: 600, cy: 880, rx: 390, ry: 95, turns: 1, dir: 1, phase: 4.2, size: 50, flaps: 48 },
  { cx: 650, cy: 775, rx: 170, ry: 42, turns: 3, dir: -1, phase: 1.3, size: 32, flaps: 66 },
];

// Swarm that bursts from behind the roof peak when the lightning strikes.
// Each follows a quadratic curve from p0 (behind the roof) through c to p1 (off
// frame), easing along it with `ease` while its span grows with exponent `grow`.
// Routes cross the moon and the lettering, where the silhouettes read; the two
// big ones swoop towards the viewer.
const SWARM = [
  // hero: grows huge while silhouetted against the blood moon, exits right
  { delay: 0.3, dur: 1.9, p0: [640, 800], c: [660, 860], p1: [1350, 980], s0: 30, s1: 330,
    ease: "power2.in", grow: 0.7, flaps: 4.2 },
  // hero: sweeps left across HOUSE and the H of HALLOWEEN
  { delay: 0.55, dur: 2.2, p0: [590, 800], c: [430, 620], p1: [-300, 520], s0: 20, s1: 220,
    grow: 0.9, flaps: 4.8 },
  { delay: 0.0, dur: 2.2, p0: [602, 790], c: [720, 560], p1: [1180, 300], s0: 20, s1: 70, flaps: 6.5 },
  { delay: 0.12, dur: 2.5, p0: [590, 800], c: [470, 560], p1: [-170, 380], s0: 20, s1: 78, flaps: 6.0 },
  { delay: 0.25, dur: 1.9, p0: [615, 795], c: [800, 700], p1: [1160, 640], s0: 18, s1: 56, flaps: 7.0 },
  { delay: 0.66, dur: 2.3, p0: [604, 798], c: [600, 520], p1: [380, -160], s0: 17, s1: 64, flaps: 6.6 },
  { delay: 0.82, dur: 2.3, p0: [620, 802], c: [840, 600], p1: [1170, 200], s0: 16, s1: 52, flaps: 7.2 },
  { delay: 0.95, dur: 2.4, p0: [598, 796], c: [660, 480], p1: [760, -170], s0: 15, s1: 58, flaps: 6.8 },
  { delay: 1.1, dur: 2.2, p0: [612, 800], c: [540, 470], p1: [120, -150], s0: 15, s1: 60, flaps: 7.4 },
  { delay: 1.3, dur: 2.0, p0: [606, 804], c: [760, 520], p1: [1150, 420], s0: 14, s1: 48, flaps: 7.8 },
];
export const SWARM_SPAN = Math.max(...SWARM.map((b) => b.delay + b.dur));

// Fireflies drifting in the shrubs.
const FIREFLIES = Array.from({ length: 18 }, (_, i) => {
  const r = (n) => {
    const x = Math.sin((i + 1) * 12.9898 + n * 78.233) * 43758.5453;
    return x - Math.floor(x);
  };
  const zones = [
    [130, 1075, 330, 1205],
    [690, 990, 900, 1205],
    [420, 1140, 540, 1215],
    [660, 1150, 760, 1215],
  ];
  const z = zones[i % zones.length];
  return {
    x: z[0] + r(1) * (z[2] - z[0]),
    y: z[1] + r(2) * (z[3] - z[1]),
    ax: 10 + r(3) * 14, ay: 6 + r(4) * 10,
    kx: 1 + Math.floor(r(5) * 2), ky: 1 + Math.floor(r(6) * 3),
    blink: 2 + Math.floor(r(7) * 4), ph: r(8) * TAU, ph2: r(9) * TAU,
  };
});

// Right wing outline at rest, unit span: shoulder, wrist, wing tip, then the
// finger tips of the trailing edge back to the body.
const WING = {
  shoulder: [0.04, -0.06],
  wrist: [0.25, -0.17],
  tip: [0.52, -0.03],
  fingers: [[0.40, 0.11], [0.26, 0.16], [0.12, 0.12]],
  hip: [0.04, 0.1],
};

function batPath(ctx, flap) {
  // flap in [-1, 1]: -1 wings fully up, 1 fully down. Points rotate about the
  // shoulder and foreshorten a little as the wing sweeps through the stroke.
  const a = flap * 0.8;
  const pose = ([x, y]) => [x * (0.86 + 0.14 * Math.cos(2 * a)), y + x * Math.sin(a) * 1.15];
  for (const side of [1, -1]) {
    const P = ([x, y]) => [side * x, y];
    const sh = P(pose(WING.shoulder));
    const wr = P(pose(WING.wrist));
    const tip = P(pose(WING.tip));
    ctx.moveTo(...sh);
    ctx.quadraticCurveTo(sh[0] + (wr[0] - sh[0]) * 0.4, wr[1] - 0.03, ...wr);
    ctx.quadraticCurveTo((wr[0] + tip[0]) / 2, (wr[1] + tip[1]) / 2 - 0.02, ...tip);
    // membrane scallops curve inward (towards the wrist) between finger tips
    let prev = tip;
    for (const f of [...WING.fingers, WING.hip]) {
      const pt = P(pose(f));
      const cx = (prev[0] + pt[0]) / 2;
      const cy = (prev[1] + pt[1]) / 2 - 0.07;
      ctx.quadraticCurveTo(cx, cy, ...pt);
      prev = pt;
    }
    ctx.closePath();
  }
  // body, head and ears
  ctx.moveTo(0.055, 0.02);
  ctx.ellipse(0, 0.02, 0.055, 0.12, 0, 0, Math.PI * 2);
  ctx.moveTo(0.048, -0.115);
  ctx.ellipse(0, -0.115, 0.048, 0.045, 0, 0, Math.PI * 2);
  ctx.moveTo(-0.045, -0.13);
  ctx.lineTo(-0.05, -0.215);
  ctx.lineTo(-0.012, -0.15);
  ctx.closePath();
  ctx.moveTo(0.045, -0.13);
  ctx.lineTo(0.05, -0.215);
  ctx.lineTo(0.012, -0.15);
  ctx.closePath();
}

export function drawBat(ctx, x, y, span, flap, roll, rim) {
  const dx = MOON.x - x, dy = MOON.y - y;
  const d = Math.hypot(dx, dy) || 1;
  const rimOffset = Math.max(2.2, span * 0.035);
  // The moonlit rim is the silhouette stacked a few times towards the moon at
  // falling strength, which gives a soft edge that widens on the bats closest
  // to camera (a blur filter looks the same but renders far slower).
  const steps = rim ? Math.min(14, Math.max(3, Math.round(rimOffset * 1.2))) : 0;
  const passes = Array.from({ length: steps }, (_, i) => [1.4 * (1 - i / steps), 0.2]);
  passes.push([0, 1]);
  for (const [k, alpha] of passes) {
    ctx.save();
    ctx.translate(x + (dx / d) * rimOffset * k, y + (dy / d) * rimOffset * k);
    ctx.rotate(roll);
    ctx.scale(span, span);
    ctx.beginPath();
    batPath(ctx, flap);
    ctx.globalAlpha = k === 0 ? 1 : alpha;
    ctx.fillStyle = k === 0 ? "#070302" : rim;
    ctx.fill("nonzero");
    ctx.restore();
  }
}

export class BatLayer {
  constructor(width, height) {
    this.front = document.createElement("canvas");
    this.back = document.createElement("canvas");
    for (const c of [this.front, this.back]) {
      c.width = width;
      c.height = height;
    }
    this.scale = width / 1024;
  }

  draw(t, loop, fx) {
    const f = this.front.getContext("2d");
    const b = this.back.getContext("2d");
    for (const ctx of [f, b]) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, this.front.width, this.front.height);
      ctx.setTransform(this.scale, 0, 0, this.scale, 0, 0);
    }
    const u = t / loop;
    const rimMix = interpolate("rgba(240,120,50,0.9)", "rgba(225,40,25,0.9)", fx.blood);

    this.drawFireflies(f, u);

    for (const o of ORBITERS) {
      const th = o.phase + o.dir * TAU * o.turns * u;
      const z = Math.sin(th);
      const jx = 14 * Math.sin(TAU * 9 * u + o.phase) + 7 * Math.sin(TAU * 17 * u + o.phase * 2);
      const jy = 10 * Math.sin(TAU * 11 * u + o.phase * 3) + 6 * Math.sin(TAU * 23 * u + o.phase);
      const x = o.cx + o.rx * Math.cos(th) + jx;
      const y = o.cy + o.ry * z + jy;
      const vx = -o.dir * Math.sin(th);
      const flap = Math.sin(TAU * o.flaps * u + o.phase);
      const span = o.size * (0.78 + 0.3 * z);
      const roll = clamp(-0.5, 0.5, vx * 0.35 + 0.15 * Math.sin(TAU * 5 * u + o.phase));
      if (z >= 0) drawBat(f, x, y, span, flap, roll, rimMix);
      else drawBat(b, x, y, span * 0.9, flap, roll, null);
    }

    if (fx.burst > 0 && fx.burst < SWARM_SPAN) {
      for (const s of SWARM) {
        const k = (fx.burst - s.delay) / s.dur;
        if (k <= 0 || k >= 1) continue;
        const e = gsap.parseEase(s.ease ?? "power1.in")(k);
        const pt = (i) => (1 - e) ** 2 * s.p0[i] + 2 * (1 - e) * e * s.c[i] + e * e * s.p1[i];
        const x = pt(0), y = pt(1);
        const span = s.s0 + (s.s1 - s.s0) * e ** (s.grow ?? 1.6);
        const flap = Math.sin(TAU * s.flaps * (fx.burst - s.delay));
        const tx = 2 * (1 - e) * (s.c[0] - s.p0[0]) + 2 * e * (s.p1[0] - s.c[0]);
        const roll = clamp(-0.6, 0.6, tx * 0.0006);
        if (k < 0.12) drawBat(b, x, y, span, flap, roll, null);
        else drawBat(f, x, y, span, flap, roll, rimMix);
      }
    }
  }

  drawFireflies(ctx, u) {
    for (const ff of FIREFLIES) {
      const x = ff.x + ff.ax * Math.sin(TAU * ff.kx * u + ff.ph) + 5 * Math.sin(TAU * 7 * u + ff.ph2);
      const y = ff.y + ff.ay * Math.sin(TAU * ff.ky * u + ff.ph2);
      const glow = Math.max(0, Math.sin(TAU * ff.blink * u + ff.ph)) ** 5;
      if (glow < 0.02) continue;
      const g = ctx.createRadialGradient(x, y, 0, x, y, 9);
      g.addColorStop(0, `rgba(255,214,140,${0.95 * glow})`);
      g.addColorStop(0.18, `rgba(255,150,60,${0.55 * glow})`);
      g.addColorStop(1, "rgba(255,110,40,0)");
      ctx.fillStyle = g;
      ctx.fillRect(x - 9, y - 9, 18, 18);
    }
  }
}
