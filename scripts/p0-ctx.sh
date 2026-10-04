#!/bin/bash
cd "/mnt/f/MTKeyWork/Executables"
for f in 'MAXX Diamond (V6.03)/MEGACDLL.EXE' 'MAXX (V3.06)/MEGACDLL.EXE'; do
  echo "== $f"; o=$(strings -a -t d "$f" | grep -m1 SA3019 | awk '{print $1}'); xxd -s $((o-128)) -l 320 "$f"
done
