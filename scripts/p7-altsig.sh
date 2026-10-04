#!/bin/bash
D=/mnt/f/MTKeyWork/scripts/disoff.sh; E=/mnt/f/MTKeyWork/Executables
for p in "MAXX Jade (V14.00)/start.elf|0x1e619b" "MAXX Jade 2 (V15.10)/start.elf|0x1f6eeb" "MAXX Crown (V16.10)/start.elf|0x1f7f5b"; do
  echo "### ${p%%|*}"; bash $D "$E/${p%%|*}" ${p##*|} 0x500 | grep -E 'addb|subb|incb|0xef|0x11,|-0x11|memicmp|cmpb   \$0x(53|41|52|30|39)' | head -12
done
