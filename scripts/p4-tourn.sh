#!/bin/bash
f="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/opsetup.so"
objdump -d --no-show-raw-insn -C "$f" > /tmp/crown_opsetup.dis
for fn in 'EnableDisableButtons__8TTM_Main' 'EnableDisableButtons__11BSM_BD_Main' 'MegaNetOptionsAvalible__Fi' 'DisableCategories__8MainMenu' 'EnableDisableButtons__8CSM_Main' '__14TournaMAXXMenuP12MegacGlobalsP10MenuSystem'; do
  echo "######## $fn"
  awk -v F="<$fn@@Base>:" '$2==F{p=1;next} /^[0-9a-f]+ <.*>:$/{p=0} p' /tmp/crown_opsetup.dis | grep -E 'push   \$0x|call|cmp ' | head -40
done
