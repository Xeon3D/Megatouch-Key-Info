#!/bin/bash
# P19: does the Gen 4 line still enforce a laser-serial range (Docs/05 surface H)?
B=/mnt/f/MTKeyWork/analysis/p19/bin
R=/mnt/f/MTKeyWork/analysis/p19/raw
for t in I2014 I2011 F2011 T2P2013 FIREFLY; do
  f=$B/$t/start; [ -f "$f" ] || continue
  echo "=== $t"
  grep -iE 'keyshutdown|validate_key_range|KeyRange|InitVars|findint3|Unlock_System' \
    "$R/$t.start.dem.txt" 2>/dev/null | head -8
  echo -n "  immediates 0x400000 / 0x40 lot pattern in .text: "
  objdump -d "$f" 2>/dev/null | grep -coE '0x40(00|0000)[0-9a-f]{0,4}\b' || true
done
echo
echo "=== strings that look like key errors (ION 2014) ==="
grep -aoE '[ -~]{8,60}' "$B/I2014/start" | grep -iE 'security key|key range|invalid key|key mismatch|motherboard' | sort -u | head -20
