#!/bin/bash
E="/mnt/f/MTKeyWork/Executables/MAXX Sapphire (V12.01)"
objdump -d --no-show-raw-insn --start-address=0x7a510 --stop-address=0x7a5c0 "$E/opsetup.so" | tail -n +7
echo ===== GetGamePriceFromKey
objdump -d --no-show-raw-insn --start-address=0x813d7e0 --stop-address=0x813d8d0 "$E/start.elf" | tail -n +7
echo ===== key pointer globals
objdump -R "$E/start.elf" | grep -iE 'Dallas|k_data|k_id' | head
nm -D "$E/start.elf" | grep -iE 'DallasKey|k_data|k_id|k_laser'
