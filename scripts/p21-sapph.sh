#!/bin/bash
# p21-sapph.sh: where Sapphire (V12.01) reads the option table and game enables from the key
E="/mnt/f/MTKeyWork/Executables/MAXX Sapphire (V12.01)"
for f in start.elf opsetup.so; do
  nm -D -C "$E/$f" 2>/dev/null | grep -iE 'ExplodeOptions|IsOptionSelectable|GetOptionState|SetGamePriceAndStatus|GetGamePriceFromKey' 
done
a=$(nm -D "$E/start.elf" | grep -i 'ExplodeOptions' | head -1 | cut -d' ' -f1)
[ -n "$a" ] && objdump -d --no-show-raw-insn --start-address=0x$a --stop-address=$(printf '0x%x' $((0x$a+0x120))) "$E/start.elf" | tail -n +7
a=$(nm -D "$E/start.elf" | grep -i 'SetGamePriceAndStatusFromKey' | head -1 | cut -d' ' -f1)
[ -n "$a" ] && objdump -d --no-show-raw-insn --start-address=0x$a --stop-address=$(printf '0x%x' $((0x$a+0x100))) "$E/start.elf" | tail -n +7
