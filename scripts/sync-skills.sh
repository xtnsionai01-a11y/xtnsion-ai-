#!/usr/bin/env bash
# Copies the skills from the skill-pack submodules under .agents/ into
# .claude/skills/, where Claude Code discovers them. Submodules are not
# checked out in a fresh clone, so the copies are committed.
#
# Re-sync from the pinned commits:  scripts/sync-skills.sh
# Pull upstream first:              git submodule update --init --remote .agents/gsap-skills .agents/claudedesignskills
#                                   scripts/sync-skills.sh
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
dest="$root/.claude/skills"
cd "$root"

for pack in .agents/gsap-skills .agents/claudedesignskills; do
  [ -e "$pack/.git" ] || git submodule update --init --depth 1 "$pack"
done

copy() { rm -rf "$dest/$(basename "$1")"; cp -R "$1" "$dest/"; }

mkdir -p "$dest"

for d in .agents/gsap-skills/skills/*/; do copy "${d%/}"; done
cp .agents/gsap-skills/LICENSE "$dest/LICENSE.gsap-skills"

for d in .agents/claudedesignskills/plugins/individual/*/skills/*/; do
  # The official GSAP pack above already provides gsap-scrolltrigger.
  [ "$(basename "$d")" = gsap-scrolltrigger ] && continue
  copy "${d%/}"
done
cp .agents/claudedesignskills/LICENSE "$dest/LICENSE.claudedesignskills"
