#!/bin/bash
E=/mnt/f/MTKeyWork/Executables; O=/mnt/f/MTKeyWork/analysis/p10
for p in "ruby2|Maxx Ruby 2 (V11.00)" "sapphire|MAXX Sapphire (V12.01)" "sapphire2|MAXX Sapphire 2 (V13.00)" "jade|MAXX Jade (V14.00)" "jade2|MAXX Jade 2 (V15.10)" "jade1421|MAXX Jade (V14.21)" "crown|MAXX Crown (V16.10)"; do
  b=${p%%|*}; d=${p##*|}
  objdump -d --no-show-raw-insn "$E/$d/opsetup.so" > /tmp/op_$b.dis
  python3 /mnt/f/MTKeyWork/scripts/p10-slotcalls.py /tmp/op_$b.dis opsetup > $O/slotcalls_$b.tsv
  echo "$b $(wc -l < $O/slotcalls_$b.tsv) calls"
done
