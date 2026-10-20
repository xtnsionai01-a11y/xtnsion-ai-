// Text animation. Every letter of the artwork's lettering has its own state
// (x/y offset in poster px, opacity, brightness), choreographed with GSAP
// staggers and handed to the shader each frame. assets/letters.json says which
// letters belong to which line.
import { gsap } from "gsap";

const TAU = Math.PI * 2;

export function createLetters(meta) {
  const all = [];
  const line = {};
  for (const l of meta.lines) {
    line[l.name] = Array.from({ length: l.count }, (_, k) => {
      const letter = { x: 0, y: 0, a: 1, b: 1, line: l.name, k };
      all.push(letter);
      return letter;
    });
  }
  return { all, line };
}

// Fixed shuffle, so every render and every loop flickers the same way.
function shuffled(list, seed = 7) {
  const out = [...list];
  let s = seed;
  for (let i = out.length - 1; i > 0; i--) {
    s = (s * 16807) % 2147483647;
    const j = s % (i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

// Adds the lettering choreography to the master timeline. Like everything else
// on it, each value is back at rest by the end of the loop.
export function addTextTimeline(tl, { line }, fx) {
  const title = [...line.trick, ...line.halloween, ...line.house];
  const glitch = (offsets) => ({ x: (i) => offsets[i % offsets.length], duration: 0.05, ease: "none" });

  tl.addLabel("letters", 0.2)
    // with the bell, TRICK OR TREAT lights up letter by letter and a gleam crosses the title
    .to(line.trick, {
      keyframes: [
        { b: 2.1, y: -3, duration: 0.18, ease: "power2.out" },
        { b: 1, y: 0, duration: 0.6, ease: "sine.inOut" },
      ],
      stagger: 0.055,
    }, "letters+=0.05")
    .to(fx, { sheen: 1100, duration: 1.5, ease: "power1.inOut" }, "letters")
    .set(fx, { sheen: -200 }, "letters+=1.6")
    // as the door opens, a shimmer runs along the tagline
    .to(line.invite, {
      keyframes: [
        { b: 1.9, duration: 0.15, ease: "power2.out" },
        { b: 1, duration: 0.5, ease: "sine.inOut" },
      ],
      stagger: 0.035,
    }, 2.7)
    // the storm builds: the title trembles, then dies out like failing lights
    .to(fx, { tremble: 1, duration: 1.0, ease: "power2.in" }, 4.95)
    .set(fx, { tremble: 0 }, 6.0)
    .to(shuffled(title), {
      keyframes: [
        { a: 0.25, duration: 0.05, ease: "none" },
        { a: 0.85, duration: 0.06, ease: "none" },
        { a: 0.07, duration: 0.08, ease: "none" },
      ],
      stagger: 0.017,
    }, 5.33)
    // lightning: it all slams back on, HALLOWEEN drops in and HOUSE glitches
    .addLabel("slam", 6.0)
    .set(title, { a: 1, b: 2.3 }, "slam")
    .set(line.halloween, { y: -46 }, "slam")
    .set(line.trick, { y: -18 }, "slam")
    .to(line.halloween, {
      y: 0, duration: 0.75, ease: "bounce.out", stagger: { each: 0.035, from: "center" },
    }, "slam")
    .to(line.trick, {
      y: 0, duration: 0.5, ease: "back.out(2)", stagger: { each: 0.02, from: "edges" },
    }, "slam")
    .to(line.house, {
      keyframes: [
        glitch([-7, 5, -4, 6, -5]),
        glitch([5, -6, 7, -3, 4]),
        glitch([-3, 4, -5, 5, -6]),
        { x: 0, duration: 0.12, ease: "power2.out" },
      ],
      stagger: 0.02,
    }, "slam")
    .to(title, { b: 1, duration: 1.1, ease: "power2.out" }, "slam+=0.08")
    // save the date: the divider redraws itself and the date glows from its centre out
    .addLabel("date", 9.45)
    .to(fx, { lineDraw: 0, duration: 0.25, ease: "power2.in" }, "date")
    .to(fx, { lineDraw: 1, duration: 0.9, ease: "expo.out" }, "date+=0.25")
    .to(fx, { line: 0.9, duration: 0.3, ease: "power2.out" }, "date+=0.25")
    .to(fx, { line: 0, duration: 1.5 }, "date+=0.55")
    .to(line.date, {
      keyframes: [
        { b: 1.8, duration: 0.25, ease: "power2.out" },
        { b: 1, duration: 0.9, ease: "sine.inOut" },
      ],
      stagger: { each: 0.04, from: "center" },
    }, "date+=0.3");
}

// Writes each letter's final state into the shader's uniform array, adding the
// motion that never stops: HALLOWEEN floats on a slow wave, HOUSE flickers
// like candlelight, and everything shakes while the storm builds.
export function writeLetterUniforms(target, letters, t, loop, fx) {
  const u = t / loop;
  letters.all.forEach((l, i) => {
    let { x, y, b } = l;
    if (l.line === "halloween") y += 2.2 * Math.sin(TAU * 3 * u - l.k * 0.7);
    if (l.line === "house") {
      b *= 1 + 0.07 * (0.6 * Math.sin(TAU * 29 * u + l.k * 1.7) + 0.4 * Math.sin(TAU * 47 * u + l.k * 2.9));
    }
    if (fx.tremble > 0) {
      x += fx.tremble * 2.4 * Math.sin(i * 12.9898 + t * 91.0);
      y += fx.tremble * 1.6 * Math.sin(i * 78.233 + t * 113.0);
    }
    target[i].set(x, y, l.a, b);
  });
}

