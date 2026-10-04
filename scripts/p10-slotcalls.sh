#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)"; O=/mnt/f/MTKeyWork/analysis/p10; mkdir -p $O
objdump -d --no-show-raw-insn "$E/opsetup.so" > /tmp/op.dis
objdump -d --no-show-raw-insn "$E/start.elf" > /tmp/st.dis
python3 /mnt/f/MTKeyWork/scripts/p10-slotcalls.py /tmp/op.dis opsetup > $O/slotcalls.tsv
python3 /mnt/f/MTKeyWork/scripts/p10-slotcalls.py /tmp/st.dis start >> $O/slotcalls.tsv
wc -l $O/slotcalls.tsv; cut -f2,3 $O/slotcalls.tsv | sort | uniq -c
