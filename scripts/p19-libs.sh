#!/bin/bash
# P19: extract the generated-definition libraries (they hold the enum<->string tables).
O=/mnt/f/MTKeyWork/analysis/p19/bin; H="/mnt/h/Megatouch/Hard Disk Images"
LIBS="libenums.so libgendef_xml.so libgendef_common.so libgendef_db.so libsettings.so libbooks.so libapp_common.so"
grab() { # grab <tag> <img> <sector>
  local tag=$1 img=$2 s=$3
  mkdir -p "$O/$tag"
  for l in $LIBS; do
    for d in /usr/local/lib /usr/lib /lib; do
      if debugfs -c -R "dump $d/$l $O/$tag/$l" "$img?offset=$((s*512))" 2>/dev/null \
         && [ -s "$O/$tag/$l" ]; then
        echo "$tag $d/$l $(stat -c%s "$O/$tag/$l")B"; break
      fi
      rm -f "$O/$tag/$l"
    done
  done
}
grab I2014   "$H/ION 2014 P5B Keyless/ION 2014 P5B.img" 39584223
grab I2011   "$H/ION 2011 Keyless by Tommy/ion2011_patched.img" 1820672
grab T2P2013 "$H/Touch2Play (2013)/T2P_2013_V38.10.img" 1457528
grab FIREFLY "$H/Firefly (2010)/Firefly 2010 16gb.img" 114688
grab F2011   "$H/Force 2011 Keyless/Keyless/Force 2011 Keyless.img" 626598
grab F2010_5 "$H/Force 2010.5/Force2010.5.img" 626598
grab F2007_5 "$H/Force 2007.5/Force 2007.5.img" 626598
