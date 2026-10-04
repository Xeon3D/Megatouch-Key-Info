#!/bin/bash
# disoff.sh <elf> <fileoffset-dec-or-0x> <len> : disassemble an ELF region given a file offset
f="$1"; off=$(($2)); len=$(($3))
va=$(python3 - "$f" $off <<'P'
import sys, struct
b = open(sys.argv[1], 'rb').read(); off = int(sys.argv[2])
phoff, = struct.unpack_from('<I', b, 0x1c); n, = struct.unpack_from('<H', b, 0x2c)
for i in range(n):
    t, o, v, _, fs, *_ = struct.unpack_from('<8I', b, phoff + 32*i)
    if t == 1 and o <= off < o + fs: print(v + off - o); break
P
)
objdump -d --no-show-raw-insn --start-address=$va --stop-address=$((va+len)) "$f" | tail -n +7 | grep -vE '\snop$|lea    0x0'
