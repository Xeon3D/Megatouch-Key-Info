#!/bin/bash
# P19: locate the merit executables / opsetup / gamedata in the Force-ION-era images.
# Read-only (debugfs -c). Output: analysis/p19/raw/find.txt
O=/mnt/f/MTKeyWork/analysis/p19/raw; mkdir -p "$O"
exec > "$O/find.txt" 2>&1

imgs=(
"/mnt/h/Megatouch/Hard Disk Images/Force 2003 v10.09/Force 2003.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2003.5 v11.00/Force 2003.5.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2004 v12.00/Force 2004 v12.00.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2005 v14.00/Force 2005 v14.00.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2005.5 v15.10/Force 2005.5.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2006/Merit HDD Force 2006.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2007.5/Force 2007.5.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2010.5/Force2010.5.img"
"/mnt/h/Megatouch/Hard Disk Images/Force 2011 Keyless/Keyless/Force 2011 Keyless.img"
"/mnt/h/Megatouch/Hard Disk Images/ION 2011 Keyless by Tommy/ion2011_patched.img"
"/mnt/h/Megatouch/Hard Disk Images/ION 2014 P5B Keyless/ION 2014 P5B.img"
"/mnt/h/Megatouch/Hard Disk Images/Touch2Play (2013)/T2P_2013_V38.10.img"
"/mnt/h/Megatouch/Hard Disk Images/Firefly (2010)/Firefly 2010 16gb.img"
)

DIRS="/ /usr/local/bin /usr/local/sbin /usr/local/share/merit /usr/local/share/merit/config
/usr/local/merit /usr/local/lib /home/maxx /home/maxx/bin /opt /opt/merit /var/merit
/usr/merit /merit /home /usr/local /usr/local/share"

for img in "${imgs[@]}"; do
  echo "################ $img"
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=[0-9a-f]+' | while read -r line; do
    s=$(echo "$line" | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); t=${line##*type=}
    [ "$s" = 0 ] || [ "$t" != 83 ] && continue
    dev="$img?offset=$((s*512))"
    for d in $DIRS; do
      out=$(debugfs -c -R "ls -l $d" "$dev" 2>/dev/null \
            | grep -iE 'start|opsetup|merit|gamedata|\.so|\.elf|key' | head -20)
      [ -n "$out" ] && { echo "--- sector $s : $d"; echo "$out"; }
    done
  done
done
echo DONE
