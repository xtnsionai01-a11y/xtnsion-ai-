# Vendored skills

## instagram-agent (`ig-*`)

Thirteen Instagram skills, vendored from
[Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill)
at commit `d03c56b` (2026-09-13). MIT — see `LICENSE-instagram-agent`.

Copied in flat (not as a submodule) so the skills resolve on a plain `git clone`
with no `--recurse-submodules` step. `ig-viral/swipe.py` reads
`../ig-reel/hooks.json`, so the `ig-*` folders must stay siblings.

| command | what it does |
| --- | --- |
| `/ig-reel` | Idea into a Reel: hooks off 26 formulas, scored, script, on-screen text, timed beat sheet. |
| `/ig-viral` | Finds what is working in a niche, ranks by multiple over each account's own median. |
| `/ig-caption` | Caption, linted against the 125-char feed truncation. |
| `/ig-carousel` | Swipe posts: cover, slide copy, 1080x1350 files. |
| `/ig-story` | Daily story sequence, sticker jobs, DM funnel. |
| `/ig-profile` | Scores a profile against a 12-part rubric out of 100, rewrites fix-first. |
| `/ig-plan` | The week: what to post, which format, when, who to engage. |
| `/ig-human` | Humanizer: strips em dashes, slop vocabulary, invisible watermarks; scores the result. |
| `/ig-comment` | Comments on other people's posts, nine types. |
| `/ig-reply` | The thread under your own post, sorted then written. |
| `/ig-dm` | Keyword delivery, first message, collab pitch, two follow-ups. |
| `/ig-repurpose` | One long asset into a week of reels and carousels. |
| `/ig-audit` | Post-mortem, ranked by outlier multiple and sends per reach. |

### Voice file

Every skill reads `~/.claude/instagram/voice.md`. The blank template lives at
`.claude/instagram/voice.md` in this repo — copy it into place and fill it in:

```bash
mkdir -p ~/.claude/instagram && cp .claude/instagram/voice.md ~/.claude/instagram/
```

### Updating

```bash
git clone --depth 1 https://github.com/Jakeschincariol/instagram-agent-skill.git /tmp/ig
rm -rf .claude/skills/ig-*
cp -r /tmp/ig/skills/ig-* .claude/skills/
```
