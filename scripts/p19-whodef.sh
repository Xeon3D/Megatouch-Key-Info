#!/bin/bash
# P19: which extracted binary DEFINES the generated enum tag functions, and what libs exist.
B=/mnt/f/MTKeyWork/analysis/p19/bin
echo "=== definers (Value != 0) of enum_GameIds_tag / enum_GameOptionIndex_tag ==="
for f in $B/*/start $B/*/opsetup.so; do
  [ -f "$f" ] || continue
  readelf -W --dyn-syms "$f" 2>/dev/null | awk '$4=="FUNC" && $2+0!=0 && ($8 ~ /enum_GameIds_tag/ || $8 ~ /enum_GameOptionIndex_tag/) {print FILENAME": "$2" "$3" "$8}' FILENAME="$f"
done
echo
echo "=== libraries needed by ION 2014 start ==="
readelf -d "$B/I2014/start" 2>/dev/null | grep NEEDED
echo
echo "=== /usr/local/lib on the ION 2014 image ==="
debugfs -c -R "ls -l /usr/local/lib" "/mnt/h/Megatouch/Hard Disk Images/ION 2014 P5B Keyless/ION 2014 P5B.img?offset=$((39584223*512))" 2>/dev/null | awk '{print $6" "$NF}' | grep -iE '\.so|lib' | head -60
