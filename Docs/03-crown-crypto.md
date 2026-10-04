# 03 — MAXX Crown key crypto (recovered)

keyflasher has no Crown support; Crown keys (`SA35xx`) decrypt with none of its schemes.

## Recovery
1. Known-plaintext solve (`scripts/p1-crown-solve.py`) on `Crown CAN-VER2/MCROWN_full_6D000000CB053702`
   vs `key_out`: subkey 0 fits the DS91 structure with inc 0x16 (4 bit-7-ambiguous solutions).
2. Crown `start.elf`: `ReadKeyData`/`USBReadKeyData` set `BlkVCode = 12 78 37 F3`; `merit_encrypt`
   (`0x0828bee0`) derives laserMath from the laser ROM `k[0..7]` (family first):
   - `lm0 = ((k3 - k4) - k5) ^ k1 ^ 0x7F`
   - `lm1 = (((k1 + k2) - k3) - k4) ^ 0xF3`
   - `lm2 = (k4 + 0xBC) ^ (k2 + k2 + k1)`
   - `lm3 = k4 + k5 + k1 + k4 + 0x7F`
   For `6D000000CB053702` this gives `83 82 FD B6` and seeds `C2 28 E7` — the bit-7 twin of the solved
   pair, so both routes agree.
3. Added as scheme `MCROWN` in `scripts/mtkey.py`; `scripts/p3-crown-verify.py` decrypts
   `MCROWN_full_FF004000036F1F82` to exactly the 232 plaintext bytes in `Crown USA-STD/key`
   (that file = 8-byte ROM `82 1F 6F 03 00 40 00 FF` + plaintext): **0 differing bytes**.

## Other Crown key-path facts
- Passwords: legacy path uses Jade-style `(i + k[i] + 0x27/0x30/0x42)` init; USB path uses
  `+3/+0x11/+0x99`, runs `merit_encrypt` with the blkVCode, then XORs 0x18/0x19/0x1A before handing them
  to the board (`USBReadKeyData`).
- USB I/O board protocol (Cypress EZ-USB, vendor request 0xA0 = RAM read/write, 0xA1 = command):
  passwords → RAM 0x1CA0; trigger 0xA1/wValue 2; poll 0x1C48; subkeys ← 0x1B48/0x1B88/0x1BC8 (64 B each),
  tail ← 0x1C08 (0x2C B). `GetDecryptVal`: 0xA1/wValue 4, result ← 0x1C34 (4 B), used to unmask the
  returned data. Firmware blob: `firmware` symbol, 0x11A5 bytes, uploaded by `anchor_download`.
- `FixKey__5USBIO` forces the decrypt value to `29 29 29 29` (debug/factory hook).
- The board EEPROM holds a machine serial (`ReadSNFromEEPROM`: magic `100293JKKJ` at 0x1FD6, SN at
  0x1FE0) — separate from the key.

Open: scratch byte count (60 assumed, unproven because known scratch is all zero); the 8051 firmware
mask algorithm (not needed for offline decryption of dumps).
