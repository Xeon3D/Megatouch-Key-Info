#!/bin/bash
# elf.sh import <path> <name>            : import an ELF into ~/ghidra-proj/mtelf
# elf.sh decomp <name> <out> <sym|addr>... : decompile functions by symbol name or address
G=~/ghidra/ghidra_11.3.2_PUBLIC/support/analyzeHeadless; P=~/ghidra-proj/mtelf; mkdir -p $P
if [ "$1" = import ]; then cp "$2" /tmp/$3; $G $P mtelf -import /tmp/$3 -overwrite -max-cpu 4 2>&1 | grep -E 'REPORT|ERROR' | tail -3
elif [ "$1" = refs ]; then n=$2; shift 2; $G $P mtelf -process "$n" -noanalysis -readOnly -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -postScript refs_decomp.py "$@" 2>&1 | grep -E "ERROR|Exception" | head
elif [ "$1" = script ]; then n=$2; s=$3; shift 3; $G $P mtelf -process "$n" -noanalysis -readOnly -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -postScript $s "$@" 2>&1 | grep -E "ERROR|Exception|scanned" | head
elif [ "$1" = decomp ]; then n=$2; shift 2; $G $P mtelf -process "$n" -noanalysis -readOnly -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -postScript decomp_sym.py "$@" 2>&1 | grep -E 'ERROR|Exception|!!' | head; fi
# elf.sh flat <flatname-without-.bin> : import a flat DOS image (seeded) into mtelf
if [ "$1" = flat ]; then F=/mnt/f/MTKeyWork/analysis/flat/$2.bin; e=$(grep -o 'entry=0x[0-9a-f]*' /mnt/f/MTKeyWork/analysis/flat/$2.log | cut -d= -f2)
  $G $P mtelf -import $F -overwrite -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x10000 \
     -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -preScript seed.py $e $F.seeds.txt -max-cpu 4 2>&1 | grep -E 'REPORT|ERROR' | tail -2; fi
