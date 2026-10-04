#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)"
strings -a "$E/opsetup.so" | grep -iE 'touchtune|tournamaxx|TTM_|tt_' | sort -u | head -30
echo ----
strings -a "$E/start.elf" | grep -iE 'touchtune|jukebox|TT_[A-Z]' | sort -u | head -30
