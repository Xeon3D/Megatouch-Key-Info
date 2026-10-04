#!/bin/bash
cd "/mnt/f/MTKeyWork/Executables"
for f in "MAXX Jade (V14.00)/start.elf" "MAXX Crown (V16.10)/start.elf" "MAXX Crown (V16.10)/opsetup.so"; do
  echo "=== $f"; strings -a -t x "$f" | grep -iE 'dallas|ibutton|key ?(part|rev|mismatch)|invalid key|SA3[0-9]|territor|tournam|laser|keyman|eskey|security' | head -40
done
