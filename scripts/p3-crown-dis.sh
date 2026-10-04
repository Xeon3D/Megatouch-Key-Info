#!/bin/bash
S=/mnt/f/MTKeyWork/scripts/symdis.sh; E="/mnt/f/MTKeyWork/Executables/MAXX Crown (V16.10)"
bash $S "$E/start.elf" '^(GetDecryptVal__5USBIO|DeOrEncrypt__FPvUiUc|ReadKeyData|USBReadKeyData__5USBIO|USBReadKeyID__5USBIOPUc|RGetKeyData__Fv|ProcessKeyData__FUc|ReadKey__FUc)$' > /mnt/f/MTKeyWork/analysis/p1/crown_keyread.asm
wc -l /mnt/f/MTKeyWork/analysis/p1/crown_keyread.asm
