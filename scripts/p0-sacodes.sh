#!/bin/bash
# For each executable, list SA codes found in strings
cd "/mnt/f/MTKeyWork/Executables"
for d in */; do
  for f in MEGACDLL.EXE start.elf opsetup.so; do
    [ -f "$d$f" ] || continue
    echo "== $d$f: $(strings -a "$d$f" | grep -oE 'SA[0-9]{4}' | sort | uniq -c | tr '\n' ' ')"
  done
  [ -f "${d}start.elf" ] || [ -f "${d}MEGACDLL.EXE" ] || echo "== ${d}start: $(strings -a "${d}start" | grep -oE 'SA[0-9]{4}' | sort | uniq -c | tr '\n' ' ')"
done
