#!/bin/bash
# p21-findgd.sh: locate the game table in images whose gamedata.dat was not found by p19-extract.sh (read-only)
H="/mnt/h/Megatouch/Hard Disk Images"
for img in "$H/Force 2003 v10.09/Force 2003.img" "$H/Force 2006/Merit HDD Force 2006.img" "$H"/MAXX\ Ruby\ 2/*.img "$H"/MAXX\ Ruby/*.img "$H"/Force\ 2002/*.img; do
  [ -f "$img" ] || continue
  echo "=== $img"
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=[0-9a-f]+' | while read l; do
    s=$(echo "$l" | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); t=${l##*=}
    if [ "$t" = 83 ]; then
      for d in /usr/local/share/merit /usr/local/share/merit/config /usr/local/share /usr/local/merit /merit; do
        r=$(debugfs -c -R "ls -p $d" "$img?offset=$((s*512))" 2>/dev/null | grep -iE 'game' | cut -d/ -f6 | tr '\n' ' ')
        [ -n "$r" ] && echo "  ext2@$s $d: $r"
      done
    else
      MTOOLS_SKIP_CHECK=1 mdir -i "$img@@$((s*512))" -b ::/MERIT2/DATA 2>/dev/null | grep -i gamedata | sed "s/^/  fat@$s /"
    fi
  done
done
