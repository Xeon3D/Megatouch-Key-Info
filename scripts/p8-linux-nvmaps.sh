#!/bin/bash
# Run nvram_refs.py on each imported Linux build, then aggregate per version.
S=/mnt/f/MTKeyWork/scripts/ghidra/elf.sh; O=/mnt/f/MTKeyWork/analysis/p8
for v in ruby2_1100 ruby2_1105 sapph_1201 jade_1400 jade2_1510; do
  for f in start.elf opsetup.so; do
    bash $S script ${v}_$f nvram_refs.py $O/${v}_${f%%.*}.nvrefs.tsv
  done
  echo "$v done"
done
echo ALLDONE
