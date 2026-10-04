#!/bin/bash
# P19: disassemble every KeyManager accessor in a Gen4 binary so the field offsets can be read.
# usage: p19-accessors.sh <tag> [pattern]
T=${1:-I2014}; PAT=${2:-'KeyManager::|xml_gameoptions|xml_gameinfo'}
B=/mnt/f/MTKeyWork/analysis/p19/bin/$T/start
O=/mnt/f/MTKeyWork/analysis/p19/raw; mkdir -p "$O"
OUT=$O/$T.keymgr.asm

# address + size + mangled name for the matching symbols
readelf -W --dyn-syms "$B" | awk '$4=="FUNC" && $3+0>0 {print $2" "$3" "$8}' | sed 's/@[^ ]*$//' \
 > /tmp/$T.funcs
: > "$OUT"
while read -r addr size name; do
  dem=$(echo "$name" | c++filt)
  echo "$dem" | grep -qE "$PAT" || continue
  a=$((0x$addr)); e=$((a + size))
  { echo "########## $dem   [0x$addr size $size]"
    objdump -d --start-address=$a --stop-address=$e -M intel "$B" \
      | sed -n '/>:/,$p' | sed 's/^[ \t]*//' | grep -vE '^$|file format|Disassembly'
  } >> "$OUT"
done < /tmp/$T.funcs
grep -c '^##########' "$OUT"
wc -l "$OUT"
