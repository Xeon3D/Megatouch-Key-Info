#!/bin/bash
R="/mnt/f/TouchPPBox Folder/Rigs/05-megappbox-1.03"
L="$R/HDD Images/MAXX Jade/MAXX Jade (V14.00) - New.img"
for s in 63 48195 963963 5478228 5494293; do
  echo "--- jade part @${s}"; debugfs -c -R "ls -l /" "$L?offset=$((s*512))" 2>/dev/null | awk '{print $NF}' | tr '\n' ' ' | cut -c1-300; echo
done
D="$R/MAXX 2K/MAXX 2K (V4.01) - Played.img"
echo "--- 2K C:"; mdir -i "$D@@$((63*512))" ::/ 2>&1 | head -30
mtype -i "$D@@$((63*512))" ::/AUTOEXEC.BAT 2>&1 | head -40
