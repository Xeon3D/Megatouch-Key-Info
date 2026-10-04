#!/bin/bash
# P19: pull /var/merit/settings.xml (written in game-enum order) from the Gen4 images.
O=/mnt/f/MTKeyWork/analysis/p19/xml; H="/mnt/h/Megatouch/Hard Disk Images"
grab() { # grab <tag> <img> <sectors...>
  local tag=$1 img=$2; shift 2
  for s in "$@"; do
    for p in /var/merit/settings.xml /merit/settings.xml /settings.xml \
             /var/merit/settings.bak.xml /merit/settings.bak.xml; do
      mkdir -p "$O/$tag"
      if debugfs -c -R "dump $p $O/$tag/settings.xml" "$img?offset=$((s*512))" 2>/dev/null \
         && [ -s "$O/$tag/settings.xml" ]; then
        echo "$tag <- sector $s $p ($(stat -c%s "$O/$tag/settings.xml")B)"; return
      fi
      rm -f "$O/$tag/settings.xml"
    done
  done
  echo "$tag -- settings.xml not found"
}
grab I2014   "$H/ION 2014 P5B Keyless/ION 2014 P5B.img" 39262923 39584223 28017423 49319613 66107538 11229498 1494108
grab I2011   "$H/ION 2011 Keyless by Tommy/ion2011_patched.img" 1497088 11558912 19802112 1820672
grab T2P2013 "$H/Touch2Play (2013)/T2P_2013_V38.10.img" 1187576 11187576 27966840 39208312 49247608 66026872 406904
grab FIREFLY "$H/Firefly (2010)/Firefly 2010 16gb.img" 26966016 9852928 26642432 114688
grab F2007_5 "$H/Force 2007.5/Force 2007.5.img" 10378053 626598 10361988
