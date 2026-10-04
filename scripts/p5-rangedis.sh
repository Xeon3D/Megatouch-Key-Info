#!/bin/bash
# Disassemble the laser-serial range check in each Linux binary (file offset -> VA via PT_LOAD).
cd /mnt/f/MTKeyWork/Executables
dis() { f="$1"; off=$2
  va=$(python3 - "$f" $off <<'P'
import sys, struct
b = open(sys.argv[1], 'rb').read(); off = int(sys.argv[2])
phoff, = struct.unpack_from('<I', b, 0x1c); n, = struct.unpack_from('<H', b, 0x2c)
for i in range(n):
    t, o, v, _, fs, *_ = struct.unpack_from('<8I', b, phoff + 32*i)
    if t == 1 and o <= off < o + fs: print(hex(v + off - o)); break
P
)
  echo "######## $f off=$off va=$va"
  objdump -d --no-show-raw-insn --start-address=$((va-0x60)) --stop-address=$((va+0x80)) "$f" | tail -n +7 | grep -vE 'nop|lea    0x0'; }
dis "MAXX Crown (V16.10)/start.elf" 2056640
dis "MAXX Jade (V14.00)/start.elf" 1976048
dis "MAXX Jade 2 (V15.10)/start.elf" 2050656
dis "MAXX Sapphire 2 (V13.00)/start" 1221858
