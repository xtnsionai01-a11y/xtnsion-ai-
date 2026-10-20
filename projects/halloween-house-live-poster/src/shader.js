// Full-frame shader that turns the flat poster into a living painting.
// Coordinates are source-poster pixels (1024 x 1536, top-left origin) unless noted.
// Every periodic term completes a whole number of cycles per loop, so the
// animation repeats seamlessly.

export const vertexShader = /* glsl */ `
  void main() {
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

export const fragmentShader = /* glsl */ `
  precision highp float;

  uniform sampler2D tPoster;
  uniform sampler2D tMask1;   // r sway, g emissive, b moon
  uniform sampler2D tMask2;   // r HOUSE, g light bloom, b cream text
  uniform sampler2D tMask3;   // r HOUSE glow, g cream glow, b scene area
  uniform sampler2D tNoise;   // tileable fBm
  uniform sampler2D tBatsFront;
  uniform sampler2D tBatsBack;
  uniform sampler2D tText;    // r HALLOWEEN region, g HOUSE region, b small lines
  uniform sampler2D tLetters; // per text line, which letter owns each column
  uniform vec4 uLetters[64];  // per letter: x/y offset (px), opacity, brightness

  uniform vec2 uStage;        // output size in px
  uniform vec4 uPoster;       // poster rect inside the stage (x, y, w, h), top-left origin
  uniform float uTime;        // seconds into the loop
  uniform float uLoop;        // loop length in seconds
  uniform float uFrame;

  uniform float uZoom;
  uniform float uGust;
  uniform float uGold;
  uniform float uBlood;
  uniform float uMoonGlow;
  uniform float uFlash;
  uniform float uDoor;
  uniform float uFigureX;
  uniform float uLine;
  uniform float uLineDraw;
  uniform float uSheen;

  const vec2 SRC = vec2(1024.0, 1536.0);
  const vec2 MOON_C = vec2(674.5, 853.4);
  const float MOON_R = 147.1;
  const float TAU = 6.28318530718;
  const vec3 BG = vec3(0.008);

  float cyc(float cycles) { return TAU * cycles * uTime / uLoop; }
  float scroll(float tiles) { return tiles * uTime / uLoop; }

  vec2 texUv(vec2 p) { return vec2(p.x / SRC.x, 1.0 - p.y / SRC.y); }
  bool inside(vec2 p) { return p.x >= 0.0 && p.y >= 0.0 && p.x <= SRC.x && p.y <= SRC.y; }

  vec3 poster(vec2 p) {
    return inside(p) ? texture2D(tPoster, texUv(p)).rgb : vec3(0.008);
  }
  vec4 mask(sampler2D t, vec2 p) {
    return inside(p) ? texture2D(t, texUv(p)) : vec4(0.0);
  }
  float noise(vec2 uv, int ch) {
    vec4 n = texture2D(tNoise, uv);
    return ch == 0 ? n.r : (ch == 1 ? n.g : n.b);
  }
  float hash(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
  }
  float box(vec2 p, vec2 lo, vec2 hi) {
    vec2 d = max(lo - p, p - hi);
    return 1.0 - smoothstep(-0.5, 1.5, max(d.x, d.y));
  }

  // Letter state for column x of a text line, or opacity 0 where it has none.
  vec4 letter(float x, float row) {
    vec2 uv = vec2((floor(clamp(x, 0.0, 1023.0)) + 0.5) / 1024.0, 1.0 - (row + 0.5) / 8.0);
    vec4 info = texture2D(tLetters, uv);
    return info.g < 0.5 ? vec4(0.0) : uLetters[int(info.r * 255.0 + 0.5)];
  }

  // Redraws one line of the artwork's lettering with each letter moved,
  // faded and brightened on its own. The text sits on black, so letters
  // combine with max() and nothing else on the poster is disturbed.
  vec3 drawLine(vec3 col, vec2 p, float row, int ch) {
    vec4 L = letter(p.x, row);
    vec2 q = p - L.xy;
    vec4 r = mask(tText, q);
    float region = ch == 0 ? r.r : (ch == 1 ? r.g : r.b);
    vec3 c = BG + (poster(q) - BG) * L.z * L.w;
    return max(col, mix(BG, c, region));
  }

  vec3 moonTint() {
    vec3 c = vec3(0.86, 0.36, 0.13);
    c = mix(c, vec3(0.80, 0.07, 0.05), uBlood);
    return mix(c, vec3(1.0, 0.72, 0.36), uGold);
  }

  void main() {
    vec2 stage = vec2(gl_FragCoord.x, uStage.y - gl_FragCoord.y);
    vec2 focus = uPoster.xy + uPoster.zw * vec2(0.5, 0.56);
    vec2 zoomed = focus + (stage - focus) / uZoom;
    vec2 p = (zoomed - uPoster.xy) / uPoster.zw * SRC;
    vec2 q = p / SRC;

    // Most of the frame is black sky and letterbox, so each effect only runs
    // inside the band of the poster it can touch.
    bool poster_ = inside(p);
    bool scene = poster_ && p.y > 690.0 && p.y < 1260.0;
    bool title = poster_ && p.y > 150.0 && p.y < 760.0;
    bool footer = poster_ && p.y > 1150.0 && p.y < 1420.0;
    vec3 tint = moonTint();
    float flick = noise(vec2(p.x * 0.0021 + p.y * 0.0013, scroll(3.0)), 0);
    flick = 0.84 + 0.42 * (flick - 0.5) * 2.0;

    // --- foliage sway: slow wind wave + gusty flutter, branch tips move most
    vec2 ps = p;
    float sway = scene ? mask(tMask1, p).r : 0.0;
    if (sway > 0.0) {
      float wave = 0.65 * sin(cyc(4.0) - p.x * 0.011 + p.y * 0.004)
                 + 0.35 * sin(cyc(7.0) - p.x * 0.019 - p.y * 0.006);
      float fx = noise(q * vec2(1.7, 1.2) + vec2(scroll(2.0), 0.0), 2) - 0.5;
      float fy = noise(q * 2.3 + vec2(0.37, scroll(3.0)), 2) - 0.5;
      ps -= vec2(wave * (1.6 + 2.8 * uGust) + fx * 4.0 * uGust,
                 wave * 0.5 + fy * 2.2 * uGust) * sway;
    }
    vec3 col = poster(ps);

    // --- lettering: lift every line off the artwork, then redraw it letter by letter
    vec4 houseL = vec4(0.0);
    float creamGlow = 0.0, creamBloom = 0.0, creamInk = 0.0, houseHalo = 0.0;
    if (title || footer) {
      vec4 tr = mask(tText, p);
      col = mix(col, BG, max(max(tr.r, tr.g), tr.b));
      if (p.y > 150.0 && p.y < 300.0) col = drawLine(col, p, 0.0, 2);
      if (p.y > 200.0 && p.y < 700.0) col = drawLine(col, p, 1.0, 0);
      if (p.y > 440.0 && p.y < 760.0) col = drawLine(col, p, 2.0, 1);
      if (p.y > 1230.0 && p.y < 1320.0) col = drawLine(col, p, 3.0, 2);
      if (p.y > 1340.0 && p.y < 1420.0) col = drawLine(col, p, 4.0, 2);
      // glows and highlights travel with their letters; each line keeps its own
      if (title) {
        vec4 trickL = letter(p.x, 0.0);
        vec4 titleL = letter(p.x, 1.0);
        houseL = letter(p.x, 2.0);
        float split = smoothstep(258.0, 276.0, p.y); // between TRICK OR TREAT and HALLOWEEN
        float glowT = p.y < 330.0 ? mask(tMask3, p - trickL.xy).g * (1.0 - split) : 0.0;
        float glowH = mask(tMask3, p - titleL.xy).g * split;
        creamGlow = max(glowT, glowH);
        creamBloom = max(glowT * max(trickL.w - 1.0, 0.0) * trickL.z,
                         glowH * max(titleL.w - 1.0, 0.0) * titleL.z);
        creamInk = p.y < 700.0
            ? max(mask(tMask2, p - trickL.xy).b * step(p.y, 330.0), mask(tMask2, p - titleL.xy).b) : 0.0;
        houseHalo = mask(tMask3, p - houseL.xy).r;
      }
      if (footer) {
        vec4 smallL = letter(p.x, p.y < 1330.0 ? 3.0 : 4.0);
        float glowS = mask(tMask3, p - smallL.xy).g;
        creamGlow = max(creamGlow, glowS);
        creamBloom = max(creamBloom, glowS * max(smallL.w - 1.0, 0.0) * smallL.z);
        // the divider under the tagline can retract and draw itself again
        float lineBox = box(p, vec2(472.0, 1323.0), vec2(551.0, 1339.0));
        float lineKeep = 1.0 - smoothstep(-1.0, 1.0, abs(p.x - 511.5) - 34.5 * uLineDraw);
        col = mix(col, mix(BG, col, lineKeep), lineBox);
      }
    }

    vec4 m1 = scene ? mask(tMask1, ps) : vec4(0.0);
    vec4 m2 = (scene || title) ? mask(tMask2, p) : vec4(0.0);
    float lum = dot(col, vec3(0.299, 0.587, 0.114));

    // --- moon: shifting shades, drifting cloud wisps, breathing glow
    float moon = m1.b;
    float dMoon = length(p - MOON_C);
    if (moon > 0.001) {
      float t = smoothstep(0.16, 0.78, lum);
      vec3 blood = mix(vec3(0.17, 0.012, 0.018), vec3(0.80, 0.11, 0.07), t);
      vec3 gold = mix(vec3(0.52, 0.22, 0.05), vec3(1.0, 0.80, 0.46), t);
      vec3 mc = mix(col, blood, uBlood);
      mc = mix(mc, gold, uGold);
      vec2 cuv = (p - MOON_C) / vec2(520.0, 300.0);
      float c1 = noise(cuv + vec2(scroll(1.0), 0.21), 1);
      float c2 = noise(cuv * 1.7 + vec2(scroll(2.0), 0.63), 0);
      float cloud = smoothstep(0.5, 0.8, c1 * 0.65 + c2 * 0.45);
      mc *= 1.0 - cloud * 0.5;
      mc *= uMoonGlow;
      col = mix(col, mc, moon);
    }
    float halo = pow(1.0 - smoothstep(MOON_R * 0.96, MOON_R * 2.4, dMoon), 2.2) * (1.0 - moon);
    col += tint * halo * (0.06 + 0.3 * (uMoonGlow - 1.0));

    if (scene) {
      // --- candle-lit windows, lanterns and the open door
      float em = m1.g;
      float door = box(p, vec2(536.0, 1048.0), vec2(670.0, 1206.0));
      float lightGain = mix(flick, flick * uDoor, door);
      col += col * em * (lightGain - 1.0) * 1.2;
      vec3 bloomCol = vec3(1.0, 0.42, 0.13);
      float bloomGain = mix(flick, flick * uDoor * 1.4, smoothstep(0.0, 1.0, door + 0.35 * m2.g));
      col += bloomCol * m2.g * 0.16 * bloomGain;

      // someone walks past the gable window
      vec2 fp = p - vec2(uFigureX, 0.0);
      float head = length((fp - vec2(0.0, 853.0)) * vec2(1.0, 0.85)) - 5.6;
      float body = max(abs(fp.x) - 9.0 - max(fp.y - 870.0, 0.0) * 0.05, 864.0 - fp.y);
      float figure = 1.0 - smoothstep(-0.8, 1.2, min(head, body));
      float gable = box(p, vec2(572.0, 833.0), vec2(605.0, 909.0));
      col = mix(col, col * 0.07, figure * gable * smoothstep(0.05, 0.4, em));

      // --- low ground mist drifting through the garden, lit by the door
      float band = smoothstep(1030.0, 1150.0, p.y) * (1.0 - smoothstep(1192.0, 1246.0, p.y));
      band *= smoothstep(40.0, 230.0, p.x) * (1.0 - smoothstep(800.0, 980.0, p.x));
      if (band > 0.0) {
        float f1 = noise(vec2(p.x / 950.0 + scroll(1.0), p.y / 320.0), 0);
        float f2 = noise(vec2(p.x / 620.0 - scroll(2.0), p.y / 230.0 + 0.37), 1);
        float mist = smoothstep(0.38, 0.9, f1 * 0.62 + f2 * 0.5) * band;
        col += mist * (vec3(0.13, 0.075, 0.06) + m2.g * vec3(0.45, 0.2, 0.07) * uDoor) * 0.85;
      }

      // --- bats behind the house only show against the moon
      float behind = mask(tMask1, p).b;
      if (behind > 0.0) {
        vec4 back = mask(tBatsBack, p);
        col = col * (1.0 - back.a * behind) + back.rgb * behind;
      }
    }
    vec4 front = mask(tBatsFront, p);
    col = col * (1.0 - front.a) + front.rgb;

    // --- lettering: HOUSE smoulders with the moon, lit letters bloom, a gleam sweeps the title
    if (title) {
      float houseGlow = 0.06 + 0.35 * (uMoonGlow - 1.0) + 0.16 * uBlood;
      col += m2.r * col * houseGlow;
      col += houseHalo * tint * (0.035 + 0.05 * uBlood) * (0.7 + 0.3 * flick) * houseL.z;
      col += houseHalo * vec3(1.0, 0.38, 0.12) * max(houseL.w - 1.0, 0.0) * houseL.z * 0.6;
      float sheen = exp(-pow((p.x - (p.y - 450.0) * 0.35 - uSheen) / 26.0, 2.0));
      col += sheen * creamInk * vec3(1.0, 0.93, 0.8) * 0.55;
    }
    col += creamBloom * vec3(1.0, 0.86, 0.66) * 0.5;
    if (footer) {
      vec2 lineC = vec2(511.5, 1330.5);
      float dLine = length(max(abs(p - lineC) - vec2(33.0 * uLineDraw, 2.5), 0.0));
      col += vec3(1.0, 0.42, 0.16) * exp(-dLine / 7.0) * uLine * 0.45;
    }

    // --- lightning: sheet flash that reveals the house, with a cool tint
    if (uFlash > 0.0) {
      vec3 flashTint = vec3(0.80, 0.86, 1.0);
      if (scene) col += col * uFlash * 3.2 * mask(tMask3, p).b * flashTint;
      vec2 sky = (p - vec2(600.0, 820.0)) / vec2(560.0, 380.0);
      col += uFlash * flashTint * (0.025 + 0.11 * exp(-dot(sky, sky) * 1.6));
      col += uFlash * 0.22 * creamGlow * flashTint;
    }

    // --- grade: soft vignette, film grain
    vec2 v = (stage / uStage - 0.5) * vec2(1.0, 1.3);
    col *= mix(0.74, 1.0, smoothstep(0.95, 0.25, length(v)));
    float g = hash(gl_FragCoord.xy + vec2(uFrame * 37.13, uFrame * 11.71)) - 0.5;
    col += g * 0.038 * (1.0 - 0.6 * clamp(lum, 0.0, 1.0));

    gl_FragColor = vec4(clamp(col, 0.0, 1.0), 1.0);
  }
`;
