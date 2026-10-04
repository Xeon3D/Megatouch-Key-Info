#!/bin/bash
# Extract Linux books/settings databases (read-only) from played images.
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03/HDD Images"; O=/mnt/f/MTKeyWork/analysis/p15; mkdir -p $O
for img in "$R/MAXX Jade/MAXX Jade (V14.21) - Keyless Played.img" "$R/MAXX Crown/MAXX Crown (V16.10) - TournaMAXX test.img" "$R/MAXX Sapphire 2 Keyless/MAXX Sapphire 2 (V13.00) - Played Keyless.img" "$R/MAXX Ruby/Maxx Ruby 2 (V11.00) - Played.img"; do
  n=$(basename "$img" .img | tr ' ()' '_' | tr -s '_')
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=83' | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+' | while read s; do
    D="$img?offset=$((s*512))"
    if debugfs -c -R "ls /config" "$D" 2>/dev/null | grep -q nvram; then
      echo "== $n part $s"
      debugfs -c -R "ls -l /config/database" "$D" 2>/dev/null | head -20
      mkdir -p $O/$n
      debugfs -c -R "rdump /config/database $O/$n" "$D" 2>/dev/null
      debugfs -c -R "dump /config/amusement.db $O/$n/amusement.db" "$D" 2>/dev/null
      ls -la $O/$n $O/$n/database 2>/dev/null | head -30
    fi
  done
done
