# Claude-uploadable marketing skills

Two packagings of the same 50 skills. Pick one.

## marketing-skills-bundle.zip  (one upload)

A single skill named `marketing`. Its `SKILL.md` is a router: a table of all 50
skills, with instructions to open the matching `skills/<name>/SKILL.md` before
answering. All 50 ride along as reference material.

Upload this if you want one thing to manage. Trade-off: Claude matches your
request against the router's one combined description, so triggering is slightly
blunter than with separate skills.

## individual/  (50 uploads)

One zip per skill, each with its own `name` and `description` frontmatter, so
each triggers on its own keywords. Upload only the ones you want.

Sharper triggering, more to manage. Good starting set:

    product-marketing   run first; writes shared product/ICP context
    marketing-plan      13-section AARRR plan
    copywriting         page and landing copy
    emails              lifecycle and drip sequences
    cro                 conversion optimization
    seo-audit           technical and on-page SEO
    ai-seo              citations in AI search
    pricing             tiers, packaging, price level

## How to upload

Claude.ai → Settings → Capabilities → Skills → Upload skill, then select a .zip.
Each archive has its files under one top-level folder containing SKILL.md, which
is what both the UI and the Agent Skills API expect.

## What was left out

Each source skill ships an `evals/evals.json` of test fixtures. Those are
development artifacts, not runtime instructions, so they are excluded here. The
full originals, evals included, are in `.claude/skills/` in this repo.

Source: github.com/coreyhaines31/marketingskills — check that repo for license
terms before redistributing or using commercially.
