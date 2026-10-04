#!/bin/bash
f="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/start.elf"
bash /mnt/f/MTKeyWork/scripts/symdis.sh "$f" '^(NTournSupported__FUc|IsOptionOn__Fib|GetGamePriceFromKey__FUc)$' | grep -vE '\snop$|lea    0x0' | head -150
