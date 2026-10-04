#!/bin/bash
# Extract NVRAM files (read-only) from every rig image into analysis/p9/nvram, with sha256 list.
export MTOOLS_SKIP_CHECK=1   # XL Double Platinum image has a FAT mtools rejects otherwise
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"; O=/mnt/f/MTKeyWork/analysis/p9/nvram; mkdir -p $O; : > $O/manifest.txt
find "$R" -iname '*.img' | sort | while read img; do
  n=$(basename "$img" .img | tr ' ()' '_' | tr -s '_')
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=[0-9a-f]+' | while read -r line; do
    s=$(echo "$line" | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); t=${line##*type=}
    if [ "$t" = 6 ]; then
      if mtype -i "$img@@$((s*512))" ::/NVRAM.DAT > $O/$n.NVRAM.DAT 2>/dev/null && [ -s $O/$n.NVRAM.DAT ]; then
        mtype -i "$img@@$((s*512))" ::/R.BAT 2>/dev/null | tr -d '\r' | grep -iE '^set xl' | tr '\n' ';' > $O/$n.env.txt
        echo "$(sha256sum < $O/$n.NVRAM.DAT | cut -c1-16) $n DOS C:\NVRAM.DAT $(stat -c%s $O/$n.NVRAM.DAT)B env:$(cat $O/$n.env.txt)" >> $O/manifest.txt
        break
      else rm -f $O/$n.NVRAM.DAT; fi
    elif [ "$t" = 83 ]; then
      dev="$img?offset=$((s*512))"
      for p in /config/nvram.dat /var/config/nvram.dat; do
        if debugfs -c -R "dump $p $O/$n.nvram.dat" "$dev" 2>/dev/null && [ -s $O/$n.nvram.dat ]; then
          debugfs -c -R "dump /config/hardware.cfg $O/$n.hardware.cfg" "$dev" 2>/dev/null
          echo "$(sha256sum < $O/$n.nvram.dat | cut -c1-16) $n LINUX $p $(stat -c%s $O/$n.nvram.dat)B" >> $O/manifest.txt
          break 2
        fi
      done
    fi
  done
done
cat $O/manifest.txt
