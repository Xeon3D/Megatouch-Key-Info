#!/bin/bash
# decomp.sh <program-name> <outfile> addr...
G=~/ghidra/ghidra_11.3.2_PUBLIC/support/analyzeHeadless
P=~/ghidra-proj/mtkey; n=$1; shift
$G $P mtkey -process "$n" -noanalysis -readOnly -scriptPath /mnt/f/MTKeyWork/scripts/ghidra -postScript decomp_at.py "$@" 2>&1 | grep -E 'ERROR|Exception' | head
