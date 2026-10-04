#!/bin/bash
# p21-dis2.sh: disassemble start + every .so of the Gen 4 builds that ship opsetup.so (reads of option slots live in start/libs)
B=/mnt/f/MTKeyWork/analysis/p19/bin; O=/mnt/f/MTKeyWork/analysis/p21
for t in I2011 I2014 T2P2013 FIREFLY; do
  for f in start libapp_common.so libsettings.so libbooks.so; do
    [ -f $B/$t/$f ] && objdump -d -C --no-show-raw-insn $B/$t/$f > $O/$t.$f.dis
  done
done
for t in F2010_5; do objdump -d -C --no-show-raw-insn $B/$t/libapp_common.so > $O/$t.libapp_common.so.dis; done
for t in F2011; do for f in libapp_common.so libgendef_common.so; do objdump -d -C --no-show-raw-insn $B/$t/$f > $O/$t.$f.dis; done; done
ls -la $O
