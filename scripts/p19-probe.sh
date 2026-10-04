#!/bin/bash
# P19 discovery: partition layout + merit tree shape of every Force/ION/Firefly/T2P image.
# Read-only (sfdisk -d, debugfs -c). Output: analysis/p19/raw/probe.txt
R="/mnt/h/Megatouch/Hard Disk Images"
O=/mnt/f/MTKeyWork/analysis/p19/raw; mkdir -p "$O"
exec > "$O/probe.txt" 2>&1

find "$R" -iname '*.img' \! -ipath '*Lost Classics*' | sort | while read -r img; do
  echo "################ $img"
  echo "size: $(stat -c%s "$img")"
  sfdisk -d "$img" 2>/dev/null | grep -E '^/|start='
  sfdisk -d "$img" 2>/dev/null | grep -oE 'start= *[0-9]+, size= *[0-9]+, type=[0-9a-f]+' | while read -r line; do
    s=$(echo "$line" | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+')
    t=${line##*type=}
    [ "$s" = 0 ] && continue
    dev="$img?offset=$((s*512))"
    if [ "$t" = 83 ]; then
      echo "--- ext part at sector $s"
      debugfs -c -R "ls -l /" "$dev" 2>/dev/null | head -30
      for d in /usr/local/share/merit /usr/local/merit /home/maxx /var/config /config /opt/merit; do
        out=$(debugfs -c -R "ls -l $d" "$dev" 2>/dev/null | head -40)
        [ -n "$out" ] && { echo "  >>> $d"; echo "$out"; }
      done
    elif [ "$t" = 6 ] || [ "$t" = b ] || [ "$t" = c ] || [ "$t" = 7 ]; then
      echo "--- fat/ntfs part at sector $s type $t"
      MTOOLS_SKIP_CHECK=1 mdir -i "$img@@$((s*512))" :: 2>/dev/null | head -25
    fi
  done
done
echo "DONE"
