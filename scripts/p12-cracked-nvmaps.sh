#!/bin/bash
S=/mnt/f/MTKeyWork/scripts/ghidra/elf.sh; O=/mnt/f/MTKeyWork/analysis/p8
for v in jade_1421 sapph2_1300; do
  bash $S script ${v}_start nvram_refs.py $O/${v}_start.nvrefs.tsv
  bash $S script ${v}_opsetup.so nvram_refs.py $O/${v}_opsetup.nvrefs.tsv
  echo "$v done"
done
echo ALLDONE
