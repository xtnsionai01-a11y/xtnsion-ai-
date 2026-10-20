#!/usr/bin/env bash
# Muxes the rendered frames with the soundtrack into the delivery formats.
#   tools/export.sh <video.mp4> <soundtrack.wav> <output dir>
set -euo pipefail

video="$1"
audio="$2"
out="$3"
name=halloween-house-live-poster
mkdir -p "$out"

# Film grain is expensive to encode; capping at 9 Mb/s keeps each file under
# WhatsApp's 16 MB limit with no visible loss.
enc=(-c:v libx264 -preset slow -crf 18 -maxrate 9M -bufsize 18M -tune film
     -profile:v high -pix_fmt yuv420p -r 30
     -c:a aac -b:a 192k -ar 48000 -movflags +faststart -shortest)

# 9:16 for Reels, Stories and WhatsApp status
ffmpeg -v error -y -i "$video" -i "$audio" "${enc[@]}" "$out/${name}_9x16.mp4"

# 4:5 for the Instagram feed: the poster area, letterboxed in black
ffmpeg -v error -y -i "$video" -i "$audio" \
  -vf "crop=1080:1620:0:150,scale=900:1350:flags=lanczos,pad=1080:1350:90:0:color=0x020202" \
  "${enc[@]}" "$out/${name}_4x5.mp4"

# soundtrack for the live web version
ffmpeg -v error -y -i "$audio" -c:a aac -b:a 192k "$(dirname "$0")/../assets/soundtrack.m4a"

ls -la "$out"
