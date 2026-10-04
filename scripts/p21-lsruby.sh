#!/bin/bash
H="/mnt/h/Megatouch/Hard Disk Images"
for spec in "MAXX Ruby 2/MAXX Ruby 2.img" "Force 2006/Merit HDD Force 2006.img"; do
 img="$H/$spec"; echo "=== $spec"
 for s in $(sfdisk -d "$img" 2>/dev/null | grep 'type=83' | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); do
   echo "-- $s: $(debugfs -c -R 'ls' "$img?offset=$((s*512))" 2>/dev/null | tr -s ' \n' ' ' | head -c 400)"
 done
done
