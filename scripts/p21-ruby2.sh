#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/Maxx Ruby 2 (V11.00)/start.elf"
objdump -d --no-show-raw-insn --start-address=0x081370f0 --stop-address=0x08137270 "$E" | tail -n +7
