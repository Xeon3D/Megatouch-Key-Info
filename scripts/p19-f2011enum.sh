#!/bin/bash
# P19: where are the generated enums in the Force 2011 build, and what shape?
B=/mnt/f/MTKeyWork/analysis/p19/bin/F2011/start
echo "=== generated enum tag symbols defined in F2011/start ==="
readelf -W --dyn-syms "$B" | awk '$4=="FUNC" && $2+0!=0 && $8 ~ /enum_.*_tag/ {print $2" "$3" "$8}' \
  | while read -r a s n; do printf '%s %6s %s\n' "$a" "$s" "$(echo "$n" | c++filt)"; done | head -30
echo
echo "=== prologue of the GameIds tag function ==="
a=$(readelf -W --dyn-syms "$B" | awk '$4=="FUNC" && $2+0!=0 && $8 ~ /enum_GameIds_tag/ {print $2; exit}')
[ -n "$a" ] && objdump -d --start-address=0x$a --stop-address=$((0x$a+0x60)) -M intel "$B" | sed -n '6,30p'
echo
echo "=== option enum symbols anywhere in F2011 ==="
readelf -W --dyn-syms "$B" | awk '$8 ~ /GameOption/ {print $2" "$4" "$8}' | head -10
