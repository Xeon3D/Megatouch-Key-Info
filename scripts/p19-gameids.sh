#!/bin/bash
# P19: inspect the GameIds tag function and find who defines the other generated enums.
B=/mnt/f/MTKeyWork/analysis/p19/bin/I2014
a=$(readelf -W --dyn-syms "$B/libenums.so" | awk '$4=="FUNC" && $2+0!=0 && $8 ~ /enum_GameIds_tag/ {print $2" "$3}')
set -- $a
echo "enum_GameIds_tag at 0x$1 size $2"
objdump -d --start-address=0x$1 --stop-address=$((0x$1+0x90)) -M intel "$B/libenums.so" | sed -n '6,40p'
echo
echo "=== definers of the other enums ==="
for f in "$B"/*.so; do
  readelf -W --dyn-syms "$f" 2>/dev/null \
    | awk -v n="$(basename "$f")" '$4=="FUNC" && $2+0!=0 && $8 ~ /enum_.*_tag/ {print n" "$8}'
done | c++filt | sort -u | head -40
