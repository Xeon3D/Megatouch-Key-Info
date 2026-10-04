#!/bin/bash
for d in "MAXX Crown (V16.10)/start.elf" "MAXX Jade (V14.00)/start.elf" "MAXX Sapphire (V12.01)/start.elf" "Maxx Ruby 2 (V11.00)/start.elf"; do
  f="/mnt/f/MTKeyWork/Executables/$d"; echo "== $d"
  strings -a "$f" | grep -iE 'nvram|\.nvr|ntnvram|/var/merit/[a-z]*\.dat' | sort -u | head -12
  readelf -Ws --dyn-syms "$f" | awk '$8=="NVRAMData"{print "  NVRAMData size", $3}'
done
