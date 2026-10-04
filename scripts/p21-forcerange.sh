#!/bin/bash
# p21-forcerange.sh: does each Force/ION start still carry the laser-serial range check (Docs/05 surface H)?
B=/mnt/f/MTKeyWork/analysis/p19/bin; E=/mnt/f/MTKeyWork/Executables
for f in $B/*/start "$E/Maxx Ruby 2 (V11.00)/start.elf" "$E/MAXX Jade 2 (V15.10)/start.elf" "$E/MAXX Crown (V16.10)/start.elf"; do
  s=$(nm -D "$f" 2>/dev/null | grep -ciE 'validate_key_range|KeyShutDown|findint3|InitVars')
  r=$(nm -D -C "$f" 2>/dev/null | grep -iE 'validate_key_range|KeyShutDown' | awk '{print $NF}' | tr '\n' ' ')
  echo "$(basename "$(dirname "$f")") syms=$s $r md5=$(md5sum < "$f" | cut -c1-8)"
done
