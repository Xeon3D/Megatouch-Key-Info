#!/bin/bash
cd "/mnt/f/MTKeyWork/Executables"
find . -type f \( -name '*.EXE' -o -name 'start*' -o -name '*.so' \) | sort | while read f; do
  ent=$(python3 -c "
import math,sys,collections
b=open(sys.argv[1],'rb').read(); c=collections.Counter(b); n=len(b)
print('%.3f'%(-sum(v/n*math.log2(v/n) for v in c.values())))" "$f")
  echo "$ent | $f | $(file -b "$f" | cut -c1-110)"
done
echo; which binwalk ghidra analyzeHeadless upx wine 2>&1 | grep -v 'no '
ls /opt 2>/dev/null
