#!/bin/bash
f="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/start.elf"
objdump -d --no-show-raw-insn -C "$f" | grep -B4 'mov    %e[a-d]x,0x1b1d4(%e[a-d]x)\|movl   \$0x[0-9a-f]*,0x1b1d4(' | head -40
