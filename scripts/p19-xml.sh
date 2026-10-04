#!/bin/bash
# P19: extract the Gen4 XML config (game table, options, languages) read-only from the images.
O=/mnt/f/MTKeyWork/analysis/p19/xml; mkdir -p "$O"
H="/mnt/h/Megatouch/Hard Disk Images"

try() { # try <tag> <img> <sector> <dir>
  local tag=$1 img=$2 s=$3 d=$4
  local dev="$img?offset=$((s*512))"
  local ls
  ls=$(debugfs -c -R "ls -l $d" "$dev" 2>/dev/null)
  [ -z "$ls" ] && return
  echo "### $tag  sector $s  $d"
  echo "$ls" | awk '{print $NF}' | grep -iE '\.xml$|\.dat$|\.cfg$' | while read -r f; do
    mkdir -p "$O/$tag"
    debugfs -c -R "dump $d/$f $O/$tag/$f" "$dev" 2>/dev/null
    [ -s "$O/$tag/$f" ] && echo "    $f $(stat -c%s "$O/$tag/$f")B"
  done
}

for spec in \
  "I2014|$H/ION 2014 P5B Keyless/ION 2014 P5B.img|39584223|11229498|28017423|49319613|66107538|1494108|112455" \
  "I2011|$H/ION 2011 Keyless by Tommy/ion2011_patched.img|1820672|1497088|11558912|19802112" \
  "F2011|$H/Force 2011 Keyless/Keyless/Force 2011 Keyless.img|626598|32130|10378053" \
  "F2010_5|$H/Force 2010.5/Force2010.5.img|626598|32130|10378053" \
  "F2007_5|$H/Force 2007.5/Force 2007.5.img|626598|32130|10378053" \
  "T2P2013|$H/Touch2Play (2013)/T2P_2013_V38.10.img|1457528|406904|11187576|49247608|99704" \
  "FIREFLY|$H/Firefly (2010)/Firefly 2010 16gb.img|114688|9852928|26966016" ; do
  IFS='|' read -r tag img rest <<< "$spec"
  for s in $(echo "$spec" | cut -d'|' -f3- | tr '|' ' '); do
    for d in /usr/local/gamedata/config /usr/local/share/merit/config /gamedata/config /config; do
      try "$tag" "$img" "$s" "$d"
    done
  done
done
echo DONE
ls -lR "$O" | head -80
