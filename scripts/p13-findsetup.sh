#!/bin/bash
# List setup-related files on the Emerald 2 image (read-only)
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"
I="$R/HDD Images/MAXX Emerald 2/MAXX Emerald 2 (V9.01) - New.img"
for o in 63 4193028; do
  echo "== partition @$o"
  mdir -i "$I@@$((o*512))" -/ -b ::/ 2>/dev/null | grep -iE 'setup|/merit2/[^/]*$|/merit2/exec/' | head -60
done
