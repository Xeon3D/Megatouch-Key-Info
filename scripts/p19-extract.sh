#!/bin/bash
# P19: extract (read-only) the Force/ION-era game binary, operator-setup lib, game table and
# config from each image into analysis/p19/bin/<tag>/ with a sha256 manifest.
O=/mnt/f/MTKeyWork/analysis/p19/bin; mkdir -p "$O"; M="$O/manifest.txt"; : > "$M"

ex() {  # ex <tag> <img> <sector> <path-in-fs> [outname]
  local tag=$1 img=$2 s=$3 p=$4 name=${5:-$(basename "$4")}
  mkdir -p "$O/$tag"
  if debugfs -c -R "dump $p $O/$tag/$name" "$img?offset=$((s*512))" 2>/dev/null \
     && [ -s "$O/$tag/$name" ]; then
    echo "$(sha256sum < "$O/$tag/$name" | cut -c1-16) $tag $p $(stat -c%s "$O/$tag/$name")B" >> "$M"
  else
    rm -f "$O/$tag/$name"
  fi
}

each() {  # each <tag> <img> <rootsector> <datasector>
  local tag=$1 img=$2 rs=$3 ds=$4
  ex "$tag" "$img" "$rs" /usr/local/bin/start
  ex "$tag" "$img" "$rs" /usr/local/lib/opsetup.so
  ex "$tag" "$img" "$rs" /usr/local/lib/libtmaxx.so
  for g in /usr/local/share/merit/config/gamedata.dat /usr/local/share/merit/gamedata.dat \
           /usr/local/share/merit/config/games.dat; do
    ex "$tag" "$img" "$rs" "$g"
  done
  [ -n "$ds" ] && for f in /config/nvram.dat /config/hardware.cfg /merit/config/nvram.dat; do
    ex "$tag" "$img" "$ds" "$f" "$(echo "${f#/}" | tr / _)"
  done
}

H="/mnt/h/Megatouch/Hard Disk Images"
each F2003    "$H/Force 2003 v10.09/Force 2003.img"                         96390   947835
each F2003_5  "$H/Force 2003.5 v11.00/Force 2003.5.img"                     96390   947835
each F2004    "$H/Force 2004 v12.00/Force 2004 v12.00.img"                  48195   5092668
each F2005    "$H/Force 2005 v14.00/Force 2005 v14.00.img"                  963963  5494293
each F2005_5  "$H/Force 2005.5 v15.10/Force 2005.5.img"                     963963  5494293
each F2006    "$H/Force 2006/Merit HDD Force 2006.img"                      176715  1831410
each F2007_5  "$H/Force 2007.5/Force 2007.5.img"                            626598  10378053
each F2010_5  "$H/Force 2010.5/Force2010.5.img"                             626598  10378053
each F2011    "$H/Force 2011 Keyless/Keyless/Force 2011 Keyless.img"        626598  10378053
each I2011    "$H/ION 2011 Keyless by Tommy/ion2011_patched.img"             1820672 1497088
each I2014    "$H/ION 2014 P5B Keyless/ION 2014 P5B.img"                     39584223 39262923
each T2P2013  "$H/Touch2Play (2013)/T2P_2013_V38.10.img"                     1457528 1187576
each FIREFLY  "$H/Firefly (2010)/Firefly 2010 16gb.img"                      114688  26966016
cat "$M"
