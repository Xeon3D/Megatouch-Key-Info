#!/bin/bash
# symdis.sh <elf> <symbol-regex> : disassemble dynamic-symbol functions matching regex
f="$1"; readelf -Ws --dyn-syms "$f" | awk -v r="$2" '$4=="FUNC" && $7!="UND" && $8 ~ r {print $2, $3, $8}' | sort -u | while read a s n; do
  echo "######## $n @0x$a size $s"
  objdump -d --no-show-raw-insn -C --start-address=0x$a --stop-address=$((0x$a + s)) "$f" | tail -n +7
done
