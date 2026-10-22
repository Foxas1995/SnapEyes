#!/usr/bin/env bash
# LAB: the frames of ./record.mjs into an MP4 (H.264, 60 fps, BT.709 video range, faststart).
#   FFMPEG=<path to ffmpeg> bash scripts/lab/sphere/encode.sh <frames dir> <out.mp4>
set -euo pipefail
FFMPEG="${FFMPEG:-ffmpeg}"
"$FFMPEG" -y -loglevel error -framerate 60 -i "$1/f%05d.jpg" \
  -vf "scale=in_range=pc:out_range=tv:out_color_matrix=bt709,format=yuv420p" \
  -c:v libx264 -preset slow -crf 19 -x264-params "colorprim=bt709:transfer=bt709:colormatrix=bt709:range=tv" \
  -movflags +faststart "$2"
