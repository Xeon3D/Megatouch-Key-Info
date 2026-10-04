#!/bin/bash
f="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/start.elf"
objdump -d --no-show-raw-insn "$f" | awk '/^[0-9a-f]+ <.*>:$/{fn=$2} /imul +\$0x194/{c[fn]++} /0x39e0\(/{d[fn]++} END{for(k in c) if(d[k]) print c[k], d[k], k}' | sort -rn | head -20
