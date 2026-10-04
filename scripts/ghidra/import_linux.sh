#!/bin/bash
# Import remaining Linux start.elf/opsetup.so into the mtelf project (sequential).
S=/mnt/f/MTKeyWork/scripts/ghidra/elf.sh; E=/mnt/f/MTKeyWork/Executables; L=/mnt/f/MTKeyWork/analysis/ghidra_linux.log; : > $L
for p in "Maxx Ruby 2 (V11.00)|ruby2_1100" "MAXX Ruby 2 (V11.05)|ruby2_1105" "MAXX Sapphire (V12.01)|sapph_1201" "MAXX Jade (V14.00)|jade_1400" "MAXX Jade 2 (V15.10)|jade2_1510"; do
  d=${p%%|*}; n=${p##*|}
  for f in start.elf opsetup.so; do echo "== $n $f" >> $L; bash $S import "$E/$d/$f" ${n}_$f >> $L 2>&1; done
done
for p in "MAXX Sapphire 2 (V13.00)|sapph2_1300" "MAXX Jade (V14.21)|jade_1421"; do d=${p%%|*}; n=${p##*|}
  echo "== $n start+opsetup" >> $L; bash $S import "$E/$d/start" ${n}_start >> $L 2>&1; bash $S import "$E/$d/opsetup.so" ${n}_opsetup.so >> $L 2>&1; done
echo ALLDONE >> $L
