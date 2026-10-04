#!/bin/bash
# p21-optapi.sh: every exported function that takes an xml_gameoptions::GameOptionIndex, per Gen 4 binary
cd /mnt/f/MTKeyWork/analysis/p19/bin/I2014
for f in *; do
  echo "== $f"
  nm -D -C --defined-only "$f" 2>/dev/null | grep GameOptionIndex | cut -d' ' -f3- | head -40
done
