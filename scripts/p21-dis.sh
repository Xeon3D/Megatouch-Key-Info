#!/bin/bash
# p21-dis.sh: disassemble the Gen 4 opsetup.so / start of each build into analysis/p21/<tag>.<file>.dis (C++ names demangled)
B=/mnt/f/MTKeyWork/analysis/p19/bin; O=/mnt/f/MTKeyWork/analysis/p21
for t in I2011 I2014 T2P2013 FIREFLY F2003; do
  [ -f $B/$t/opsetup.so ] && objdump -d -C --no-show-raw-insn $B/$t/opsetup.so > $O/$t.opsetup.dis
done
for t in F2007_5 F2010_5 F2011; do
  objdump -d -C --no-show-raw-insn $B/$t/start > $O/$t.start.dis
done
wc -l $O/*.dis
