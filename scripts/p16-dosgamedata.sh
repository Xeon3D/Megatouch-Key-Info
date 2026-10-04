#!/bin/bash
# Extract C:\MERIT2\DATA\GAMEDATA.DAT (game table) read-only from every DOS rig image into analysis/p16/
export MTOOLS_SKIP_CHECK=1   # XL Double Platinum image has a FAT mtools rejects otherwise
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"; O=/mnt/f/MTKeyWork/analysis/p16; mkdir -p $O; : > $O/manifest.txt
find "$R" -iname '*.img' | sort | while read img; do
  n=$(basename "$img" .img | tr ' ()' '_' | tr -s '_'); off=$((63*512))
  mcopy -n -i "$img@@$off" ::/MERIT2/DATA/GAMEDATA.DAT "$O/$n.GAMEDATA.DAT" 2>/dev/null && \
    echo "$(sha256sum < "$O/$n.GAMEDATA.DAT" | cut -c1-16) $(stat -c%s "$O/$n.GAMEDATA.DAT") $n" >> $O/manifest.txt
done
cat $O/manifest.txt
