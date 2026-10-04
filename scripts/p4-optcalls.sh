#!/bin/bash
# For Crown opsetup.so + start.elf: every call to GetOptionState/IsOptionSelectable with the option index
# (immediate pushed just before) and the enclosing function symbol.
for f in "/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/opsetup.so" "/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)/start.elf"; do
  echo "######## $f"
  objdump -d --no-show-raw-insn -C "$f" | awk '
    /^[0-9a-f]+ <.*>:$/ {fn=$2}
    /push   \$0x/ {split($0,a,"$"); last=a[2]}
    /call .*(GetOptionState|IsOptionSelectable|IsOptionInUse|IsOptionOn|SetOptionValue|OptionAvail)/ {print fn, "opt=" last, $NF}' | sort | uniq -c | sort -k3 | head -400
done
