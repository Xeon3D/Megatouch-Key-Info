#!/bin/bash
# List partitions of each rig image (read-only).
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"
find "$R" -iname '*.img' | sort | while read f; do
  echo "== ${f#$R/}"
  sfdisk -d "$f" 2>/dev/null | grep -E 'start=' | sed 's/^/   /'
done
