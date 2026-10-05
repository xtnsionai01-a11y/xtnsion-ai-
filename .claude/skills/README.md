# Skills

Project skills available to Claude Code in this repo. Claude loads one when a
task matches its `description`; you can also invoke one by name.

## MengTo/Skills (designer agent skills)

162 designer-focused skills, vendored flat from
[MengTo/Skills](https://github.com/MengTo/Skills) at commit `d11f438`
(2026-10-05), MIT licensed — see [LICENSE-mengto-skills](LICENSE-mengto-skills).

Upstream groups skills as `agent-skills/<category>/<skill>/`. Claude Code only
discovers `.claude/skills/<skill>/SKILL.md`, so the category level is flattened
away here. No skill names collided. Categories are preserved below.

### 3D rendering — `3d` (16)
`3d-cloth-material` · `3d-falling-leaves` · `3d-four-seasons` · `3d-high-poly-models` · `3d-high-resolution-textures` · `3d-metal-material` · `3d-orbit-inspect-demo` · `3d-paper-material` · `3d-retina-resolution` · `3d-sky-background` · `3d-sky-rays` · `3d-ultra-realistic-water` · `3d-underwater-god-rays` · `3d-virtual-tour` · `3d-wood-lighting-scorecard` · `3d-wood-material`

### Agent workflows & capture — `codex` (20)
`article-prompts-to-skills` · `audit-reference-originality` · `audit-verify-explain-grade-5` · `browser-video-recording` · `build-daily-inspiration-sites` · `codex-gpt-image-2-5-flare` · `daily-ui-inspiration-capture` · `elevenlabs-tts` · `generate-reference-inspired-brand-worlds` · `html-to-interaction-prompts` · `implement-fog-of-war` · `iterate-until-verified` · `optimize-web-animations` · `performance-profiling` · `publish-project-to-github` · `stitched-full-page-capture` · `video-to-superprompt` · `web-technique-to-skill` · `write-like-meng-on-x` · `x-bookmark-quote-posts`

### Game combat VFX — `game-combat` (6)
`fire-smoke-skill-vfx` · `game-dev-combat-animation` · `game-dev-combat-skill-polish` · `ice-frost-skill-vfx` · `lightning-energy-skill-vfx` · `water-crystal-skill-vfx`

### Game development — `game-development` (20)
`author-game-levels` · `build-game-audio-feedback` · `build-game-camera-controls` · `build-game-changelog` · `build-game-inventory` · `build-game-map-editor` · `build-game-monster-system` · `build-hybrid-game-assets` · `build-isometric-arpg` · `build-mobile-threejs-games` · `build-rigged-game-assets` · `build-threejs-enemy-systems` · `build-vesperfall-review-assets` · `create-game-vfx` · `design-action-combat` · `design-game-encounters` · `optimize-threejs-games` · `ship-web-games` · `test-playable-web-games` · `tune-enemy-ai`

### Media assets — `media` (2)
`aura-asset-images` · `unsplash-asset-images`

### UI quality — `ui` (3)
`audit-ai-design-slop` · `design-first-ui-prompting` · `no-ai-design-slop`

### Web design — `web-design` (91)
`add-mouse-driven-orbit` · `add-shader-cursor-trail` · `agency-grid-layout-minimal` · `ambient-section-particles` · `animation-on-scroll` · `animation-systems` · `atmosphere-background` · `background-grid-webgl` · `beam-glow-states` · `beautiful-shadows` · `blue-cloudy-clean-modern` · `blue-laser-clean-glass-layout` · `book-serif-index` · `bright-green-tech-system-webgl` · `build-awwwards-quality-sites` · `build-interactive-particle-trail` · `build-threejs-scroll-worlds` · `build-wireframe-scan-reveal` · `cinematic-gsap-lenis-motion-system` · `cinematic-scroll-storytelling` · `clean-minimal-beige-light-mode` · `cobejs` · `company-logos` · `container-lines` · `corner-diagonals` · `corner-lasers` · `css-alpha-masking` · `css-border-gradient` · `dark-blue-contrasting-clean` · `dark-glass-clean-layout` · `dither-background` · `dither-laser-dark-mode` · `documentary-brutalist-agency` · `editorial-portfolio-chapters` · `editorial-service-booking` · `editorial-tech` · `falling-leaves` · `fire-paper-loader` · `framed-grid-layout` · `framed-tech-dark-border-gradient` · `funky-purple-container-tech` · `glass-dark-mode-clock` · `glass-dark-ui` · `globe-gl` · `globe-particles` · `gooey-blob-system` · `gsap` · `gsap-scrolltrigger-storytelling` · `high-contrast-skeuomorphic-clean` · `horizontal-scroll-scenes` · `image-first-grid-layout` · `landing-page` · `light-mode-paper-technical` · `liquid-metal-border` · `marquee-loop` · `masked-reveal` · `matterjs` · `mesh-gradient-dark-blue-clean` · `nested-container-clean-agency` · `nested-container-frames` · `number-details` · `operational-enterprise-ai` · `orange-clean-paper-saas` · `paper-cinder-transition` · `pointer-trail-emitter` · `pricing-page` · `product-proof-saas` · `progressive-blur` · `reveal-hover-effect` · `scroll-progress-timeline` · `scroll-scrubbed-visual-sequence` · `scroll-scrubbed-word-reveal` · `scroll-world-storytelling` · `shaders-cursor-ripples` · `skeuomorphic-ui` · `solar-duotone-bold` · `split-layout-technical` · `staggered-word-reveal` · `tailwindcss` · `tech-green-dark-mode-modern` · `technical-wireframe-info-layout` · `thinking-orbs` · `threejs` · `threejs-landscape` · `threejs-towers` · `threejs-weather` · `unicorn-studio` · `vantajs` · `webgl-3d-object` · `webgl-landing-steering` · `webgl-laser`

### Workflow — `workflow` (4)
`workflow-progress-screenshots` · `workflow-score-to-target` · `workflow-ship-change` · `workflow-threads-manager`

## What was left out

Upstream ships a `demo/` folder inside 103 of these skills — rendered example
pages with their image, video and texture assets, **109MB of the repo's 119MB**.
Those were excluded: this repo is cloned fresh at the start of every cloud
session, and binaries are permanent in git history. Everything an agent needs to
follow a skill (`SKILL.md`, `REFERENCES.md`, `ARTICLE.md`, `references/`,
`scripts/`, `templates/`) is here, at 11MB.

18 skills still mention a `demo/` path in their text; those links point
at files that were not vendored. To restore the demos for one skill, copy that
folder from upstream:

```bash
git clone --depth 1 https://github.com/MengTo/Skills.git /tmp/mengto
cp -r /tmp/mengto/agent-skills/<category>/<skill>/demo .claude/skills/<skill>/
```

Skills with dead `demo/` references:

- `3d-ultra-realistic-water`
- `3d-underwater-god-rays`
- `add-mouse-driven-orbit`
- `ambient-section-particles`
- `article-prompts-to-skills`
- `build-interactive-particle-trail`
- `build-threejs-scroll-worlds`
- `build-wireframe-scan-reveal`
- `fire-smoke-skill-vfx`
- `html-to-interaction-prompts`
- `ice-frost-skill-vfx`
- `lightning-energy-skill-vfx`
- `scroll-progress-timeline`
- `scroll-scrubbed-visual-sequence`
- `scroll-scrubbed-word-reveal`
- `scroll-world-storytelling`
- `water-crystal-skill-vfx`
- `web-technique-to-skill`

## Changes made while vendoring

Skill bodies are verbatim. Two things were normalized:

1. **Quoted five `description` values.** `3d-metal-material`,
   `fire-smoke-skill-vfx`, `ice-frost-skill-vfx`, `lightning-energy-skill-vfx`
   and `water-crystal-skill-vfx` each contain a colon followed by a space
   (`Three.js: steel`), which is illegal in a YAML plain scalar — their
   frontmatter did not parse. All 162 now parse, with `name` matching the
   folder name.
2. **Flattened the category directories**, as described above.

Note: five descriptions exceed 1024 characters (the longest,
`water-crystal-skill-vfx`, is 1691). They are left as upstream wrote them, but
a long description may be truncated when skills are listed.
