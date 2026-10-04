#!/bin/bash
H="/mnt/h/Megatouch/Hard Disk Images"
for spec in "Force 2003 v10.09/Force 2003.img|96390" "Force 2006/Merit HDD Force 2006.img|176715" "MAXX Ruby 2/MAXX Ruby 2.img|" "MAXX Ruby/Maxx Ruby.img|"; do
  img="$H/${spec%%|*}"; s=${spec##*|}
  echo "=== $img"; sfdisk -d "$img" 2>/dev/null | grep start
  for s in $s $(sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); do
    echo "-- $s"; debugfs -c -R "ls -l /usr/local/share/merit/config" "$img?offset=$((s*512))" 2>&1 | head -8
  done
done
