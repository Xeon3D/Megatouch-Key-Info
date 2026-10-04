#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/start.elf"
readelf -Ws --dyn-syms "$E" | awk '{print $2,$3,$4,$8}' | grep -iE 'firm|ezusb|hex|download|8051|loader|usbio|merit_' | sort -u | head -60
