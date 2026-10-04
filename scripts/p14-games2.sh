#!/bin/bash
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03/HDD Images/MAXX Crown/MAXX Crown (V16.10) - New.img"
D="$R?offset=$((5494293*512))"; O=/mnt/f/MTKeyWork/analysis/p14; mkdir -p $O
debugfs -c -R "ls -l /merit/menu" "$D" 2>/dev/null | head -30
for f in $(debugfs -c -R "ls /merit/menu" "$D" 2>/dev/null | tr -s ' ' '\n' | grep -E '\.(xml|txt|dat|cfg|lay)$' | head -10); do
  debugfs -c -R "dump /merit/menu/$f $O/$f" "$D" 2>/dev/null; echo "--- $f"; head -c 600 $O/$f; echo
done
