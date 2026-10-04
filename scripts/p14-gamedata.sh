#!/bin/bash
# Extract /usr/local/share/merit/config/gamedata.dat (read-only) from each Linux rig image.
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03/HDD Images"; O=/mnt/f/MTKeyWork/analysis/p14; mkdir -p $O
find "$R" -iname '*.img' | sort | while read img; do
  n=$(basename "$img" .img | tr ' ()' '_' | tr -s '_')
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=83' | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+' | while read s; do
    for p in /usr/local/share/merit/config/gamedata.dat /local/share/merit/config/gamedata.dat; do
      if debugfs -c -R "dump $p $O/$n.gamedata.dat" "$img?offset=$((s*512))" 2>/dev/null && [ -s $O/$n.gamedata.dat ]; then
        echo "$n $(stat -c%s $O/$n.gamedata.dat)B $(sha256sum < $O/$n.gamedata.dat | cut -c1-12)"; break 2
      fi
    done
  done
  rm -f $O/$n.gamedata.dat.empty
done
ls -la $O/*.gamedata.dat 2>/dev/null | awk '$5==0{print $9}' | xargs -r rm -f
