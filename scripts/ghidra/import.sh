#!/bin/bash
# import.sh <flat.bin> <entry-hex> : import raw flat LE image at 0x10000, seed entry, auto-analyze
G=~/ghidra/ghidra_11.3.2_PUBLIC/support/analyzeHeadless
P=~/ghidra-proj/mtkey; mkdir -p $P
$G $P mtkey -import "$1" -overwrite -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x10000 \
  -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -preScript seed.py $2 "$1.seeds.txt" -max-cpu 4 2>&1 | tail -25
