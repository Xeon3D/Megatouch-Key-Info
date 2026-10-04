#!/bin/bash
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"
D="$R/MAXX 2K/MAXX 2K (V4.01) - Played.img"; O=$((63*512))
for f in TS.BAT TEST.BAT R.BAT; do echo "=== $f"; mtype -i "$D@@$O" ::/$f 2>&1 | head -30; done
mdir -i "$D@@$O" -/ ::/ 2>/dev/null | grep -iE 'nv|\.nvr|sram' | head
L="$R/HDD Images/MAXX Jade/MAXX Jade (V14.00) - New.img"
debugfs -c -R "ls -l /config" "$L?offset=$((5494293*512))" 2>/dev/null
