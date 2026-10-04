#!/bin/bash
# Show call sites of the range-check function (start = check addr - 0x80 per layout) + 6 lines after
cd /mnt/f/MTKeyWork/Executables
for p in "MAXX Crown (V16.10)/start.elf|823e140" "MAXX Jade (V14.00)/start.elf|822a670" "MAXX Jade 2 (V15.10)/start.elf|823c9e0" "MAXX Sapphire 2 (V13.00)/start|8172440"; do
  f=${p%%|*}; a=${p##*|}
  echo "######## $f fn=$a"
  objdump -d --no-show-raw-insn "$f" | grep -A6 "call   $a " | grep -E 'call|test|j[a-z]+ ' | head -16
done
