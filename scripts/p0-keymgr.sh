#!/bin/bash
cd "/mnt/f/MTKeyWork/Executables"
for d in "Maxx Ruby 2 (V11.00)" "MAXX Sapphire (V12.01)" "MAXX Jade (V14.00)" "MAXX Jade 2 (V15.10)" "MAXX Crown (V16.10)"; do
  echo "=== $d"
  for f in start.elf start opsetup.so; do [ -f "$d/$f" ] || continue; [ $f = start ] && [ -f "$d/start.elf" ] && continue
    readelf -Ws --dyn-syms "$d/$f" 2>/dev/null | awk '{print $8}' | grep -E '6KeyMgr|ReadKey|KeyData|DallasKey|k_laser|USBReadKey|FromKey|Territory|Region|KeyOption|Laser|Decrypt|Encrypt' | sort -u | sed "s|^|  $f: |"
  done
done
