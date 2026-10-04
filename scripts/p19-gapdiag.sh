#!/bin/bash
# P19: how are the GameIds values with no `je` leaf dispatched?
B=/mnt/f/MTKeyWork/analysis/p19/bin/I2014/libenums.so
a=0x690; e=$((0x690+12284))
objdump -d --start-address=$a --stop-address=$e -M intel "$B" > /tmp/gid.asm
echo "--- occurrences of 'cmp eax,0xb' (value 11) ---"
grep -n -A6 'cmp    eax,0xb$' /tmp/gid.asm | head -30
echo
echo "--- occurrences of 'cmp eax,0x16' (value 22) ---"
grep -n -A6 'cmp    eax,0x16$' /tmp/gid.asm | head -30
echo
echo "--- conditional jump mnemonic census ---"
grep -oE '\bj[a-z]+ ' /tmp/gid.asm | sort | uniq -c | sort -rn
