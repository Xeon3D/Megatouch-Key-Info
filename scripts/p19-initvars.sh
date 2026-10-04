#!/bin/bash
# P19: is there still a laser-serial window (Docs/05 surface H) in the Gen 4 builds?
# Dump InitVars and the functions it calls, and list the large immediates they compare against.
B=/mnt/f/MTKeyWork/analysis/p19/bin/I2014/start
read -r a s <<< "$(readelf -W --dyn-syms "$B" | awk '$4=="FUNC" && $2+0!=0 && $8 ~ /^_Z8InitVars/ {print $2" "$3; exit}')"
echo "InitVars @ 0x$a size $s"
objdump -d --start-address=0x$a --stop-address=$((0x$a+s)) -M intel "$B" > /tmp/iv.asm
echo "--- immediates >= 0x10000 compared in InitVars ---"
grep -oE 'cmp +[a-z]+,0x[0-9a-f]{5,}' /tmp/iv.asm | sort -u | head -20
echo "--- calls out of InitVars (demangled) ---"
grep -oE 'call +[0-9a-f]+ <[^>]+>' /tmp/iv.asm | sed 's/.*<//;s/>//' | sort -u | c++filt | head -40
