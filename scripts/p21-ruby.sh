#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/Maxx Ruby 2 (V11.00)"
ls "$E"
nm -D -C "$E/start.elf" 2>/dev/null | grep -iE 'Price|GameStatus|KeyMgr|FromKey' | head -30
nm -C "$E/start.elf" 2>/dev/null | grep -iE 'Price.*Key|FromKey|KeyMgr' | head -30
