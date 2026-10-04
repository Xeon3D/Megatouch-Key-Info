#!/bin/bash
# Look for the game table on the Crown image (read-only)
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03/HDD Images/MAXX Crown/MAXX Crown (V16.10) - New.img"
for s in 963963 5494293; do
  D="$R?offset=$((s*512))"
  echo "== part $s /"; debugfs -c -R "ls /" "$D" 2>/dev/null | tr -s ' ' | head -3
  for p in /usr/local/lib/merit /local/lib/merit /merit /config/database /usr/local/merit; do
    out=$(debugfs -c -R "ls $p" "$D" 2>/dev/null | tr -s ' ' | head -c 1500)
    [ -n "$out" ] && echo "-- $p: $out"
  done
done
