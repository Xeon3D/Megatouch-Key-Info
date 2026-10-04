#!/bin/bash
cd "/mnt/f/MTKeyWork/Executables"
for f in "MAXX Crown (V16.10)/start.elf" "MAXX Crown (V16.10)/opsetup.so"; do
  echo "=== $f"; readelf -d "$f" | grep NEEDED
  readelf -Ws --dyn-syms "$f" | grep -E 'DallasKey|k_laser|Security|Key|Laser|Territ|Region' | head -40
done
