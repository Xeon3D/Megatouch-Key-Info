#!/bin/bash
# Batch import: all flat DOS images (seeded) + Linux ELFs (native loader) into ~/ghidra-proj/mtkey
G=~/ghidra/ghidra_11.3.2_PUBLIC/support/analyzeHeadless; P=~/ghidra-proj/mtkey; S=/mnt/f/MTKeyWork/scripts/ghidra
L=/mnt/f/MTKeyWork/analysis/ghidra_import.log; : > $L
cd /mnt/f/MTKeyWork/analysis/flat
for f in *.bin; do
  e=$(grep -o 'entry=0x[0-9a-f]*' "${f%.bin}.log" | cut -d= -f2)
  echo "== $f $e" >> $L
  $G $P mtkey -import "$PWD/$f" -overwrite -processor x86:LE:32:default -loader BinaryLoader -loader-baseAddr 0x10000 \
     -scriptPath $S -preScript seed.py $e "$PWD/$f.seeds.txt" -max-cpu 6 2>&1 | grep -E 'REPORT|seeded|ERROR' >> $L
done
mkdir -p $P/elf
cd /mnt/f/MTKeyWork/Executables
for d in */; do
  for f in start.elf opsetup.so; do
    [ -f "$d$f" ] || continue
    n=$(echo "${d%/}" | tr ' ()' '_' | tr -s '_')__$f
    echo "== $n" >> $L
    cp "$d$f" /tmp/$n
    $G $P mtkey -import /tmp/$n -overwrite -max-cpu 6 2>&1 | grep -E 'REPORT|ERROR' >> $L
  done
  if [ -f "${d}NOTE.txt" ]; then n=$(echo "${d%/}" | tr ' ()' '_' | tr -s '_')__start; echo "== $n" >> $L; cp "${d}start" /tmp/$n; $G $P mtkey -import /tmp/$n -overwrite -max-cpu 6 2>&1 | grep -E 'REPORT|ERROR' >> $L; fi
done
echo ALLDONE >> $L
