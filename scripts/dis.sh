#!/bin/bash
# dis.sh <flat.bin> <start> <end> : objdump a range of a flat LE image (base 0x10000)
objdump -D -b binary -m i386 --adjust-vma=0x10000 --start-address=$2 --stop-address=$3 "$1" | tail -n +8
