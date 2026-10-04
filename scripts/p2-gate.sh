#!/bin/bash
# p2-gate.sh: for each listed image, disassemble head of the function containing the "Part No" xref
cd /mnt/f/MTKeyWork/analysis/flat
while read f ref; do
  s=$(python3 ../../scripts/funcstart.py $f.bin $ref)
  echo "=================== $f  func $s"
  objdump -D -b binary -m i386 --adjust-vma=0x10000 --start-address=$s --stop-address=$((s+0x110)) $f.bin | tail -n +8 | cut -c1-90
done
