#!/bin/bash
# Extract C:\MERIT2\EXEC\SETUP*.DLL (read-only) from every DOS rig image into analysis/p13/setup/
export MTOOLS_SKIP_CHECK=1   # XL Double Platinum image has a FAT mtools rejects otherwise
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"; O=/mnt/f/MTKeyWork/analysis/p13/setup; mkdir -p $O; : > $O/manifest.txt
find "$R" -iname '*.img' | sort | while read img; do
  n=$(basename "$img" .img | tr ' ()' '_' | tr -s '_')
  off=$((63*512))
  mdir -i "$img@@$off" -b ::/MERIT2/EXEC/ 2>/dev/null | grep -iE 'SETUP|OPSET' | while read f; do
    b=$(basename "$f"); mcopy -n -i "$img@@$off" "$f" "$O/$n.$b" 2>/dev/null && \
      echo "$(sha256sum < "$O/$n.$b" | cut -c1-16) $(stat -c%s "$O/$n.$b") $n $b" >> $O/manifest.txt
  done
done
cat $O/manifest.txt
