#!/bin/bash
# p21-gamedata.sh: extract (read-only) the game tables missing so far: Ruby-era and Force 2003/2006 keep
# /usr/local/share/merit on partition 7 (so the path inside it is /config/gamedata.dat); Force 2002 is DOS.
H="/mnt/h/Megatouch/Hard Disk Images"; O=/mnt/f/MTKeyWork/analysis/p21/gamedata; mkdir -p $O; : > $O/manifest.txt
lin() { # tag img
  for s in $(sfdisk -d "$2" 2>/dev/null | grep 'type=83' | grep -oE 'start= *[0-9]+' | grep -oE '[0-9]+'); do
    for p in /config/gamedata.dat /share/merit/config/gamedata.dat /usr/local/share/merit/config/gamedata.dat; do
      if debugfs -c -R "dump $p $O/$1.gamedata.dat" "$2?offset=$((s*512))" 2>/dev/null && [ -s $O/$1.gamedata.dat ]; then
        echo "$(sha256sum < $O/$1.gamedata.dat | cut -c1-16) $(stat -c%s $O/$1.gamedata.dat) $1 part@$s $p" >> $O/manifest.txt; return
      fi
    done
  done
  rm -f $O/$1.gamedata.dat; echo "-- none $1" >> $O/manifest.txt
}
lin RUBY "$H/MAXX Ruby/Maxx Ruby.img"
lin RUBY2 "$H/MAXX Ruby 2/MAXX Ruby 2.img"
lin F2003 "$H/Force 2003 v10.09/Force 2003.img"
lin F2003_5 "$H/Force 2003.5 v11.00/Force 2003.5.img"
lin F2006 "$H/Force 2006/Merit HDD Force 2006.img"
for i in "$H"/MAXX\ Crown*/*.img "$H"/MAXX\ Jade/*.img "$H"/MAXX\ Jade\ 2/*.img "$H"/MAXX\ Sapphire\ 2\ Keyless/*.img; do
  t=$(basename "$(dirname "$i")" | tr -d ' '); lin "$t" "$i"
done
MTOOLS_SKIP_CHECK=1 mcopy -n -i "$H/Force 2002/Force 2002.img@@32256" ::/MERIT2/DATA/GAMEDATA.DAT $O/F2002.GAMEDATA.DAT && \
  echo "$(sha256sum < $O/F2002.GAMEDATA.DAT | cut -c1-16) $(stat -c%s $O/F2002.GAMEDATA.DAT) F2002 fat" >> $O/manifest.txt
cat $O/manifest.txt
