#!/bin/bash
# P19: demangled key-related symbol lists for the Gen4 binaries.
B=/mnt/f/MTKeyWork/analysis/p19/bin
O=/mnt/f/MTKeyWork/analysis/p19/raw; mkdir -p "$O"
for t in F2011 I2011 I2014 T2P2013 FIREFLY F2006 F2003; do
  for f in start opsetup.so; do
    [ -f "$B/$t/$f" ] || continue
    readelf -W --dyn-syms "$B/$t/$f" 2>/dev/null \
      | awk '$4=="FUNC" || $4=="OBJECT" {print $8}' \
      | sed 's/@.*//' | sort -u > "$O/$t.$f.syms.txt"
    c++filt < "$O/$t.$f.syms.txt" | sort -u > "$O/$t.$f.dem.txt"
    printf '%-10s %-11s %6d symbols\n' "$t" "$f" "$(wc -l < "$O/$t.$f.syms.txt")"
  done
done
echo
echo "=== ION 2014 start: KeyMgr / key-data API (demangled) ==="
grep -iE 'keymgr|keydata|dallas|dskey|getkey|readkey' "$O/I2014.start.dem.txt" | head -80
