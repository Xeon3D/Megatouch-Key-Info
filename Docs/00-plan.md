# 00 — Bootstrap & plan: Megatouch security keys (2026-10-03)

## Goal

Understand Merit Megatouch Dallas-iButton security keys end to end:
1. key ↔ software-version correlation (the `SAxxxx` part number, why one version accepts several);
2. territory (last two digits of the part number) and what it drives;
3. key contents: every field, including feature/option locks (e.g. TournaMAXX on Crown);
4. the serial-number (laser ROM) checks in the game-menu executables.

## What the bootstrap established (evidence, not theory)

| Fact | Evidence |
|---|---|
| DOS line (XL R1 → MAXX Emerald 2): `MEGACDLL.EXE`, Watcom LE + CauseWay extender, uncompressed, 2–3 objects, base 0x10000, imports only `CAUSEWAY_KERNAL` ordinals 5/6/7 | `scripts/le_info.py`, `scripts/le_flatten.py` (0 unhandled fixups on all 25 images) |
| Linux line (Ruby 2 → Crown): i386 ELF `start.elf` + `opsetup.so`, g++ 2.9x, **dynamic C++ symbols present** (`ReadKeyData`, `USBIO::USBReadKeyData`, `USBIO::GetDecryptVal`, `DeOrEncrypt`, `KeyMgr::*`) | `readelf --dyn-syms` (`scripts/p0-keymgr.sh`) |
| `start` (no .elf) on Ruby 2/Sapphire/Jade/Jade 2/Crown is a packed launcher (entropy ≈ 7.35–7.7); `start.elf` is the unpacked game. Jade V14.21 & Sapphire 2 V13.00 only have a cracked plain `start` (keyless) | `NOTE.txt`, entropy scan `scripts/p0-ident.sh` |
| Maxx Ruby 2 V11.00 / Jade 2 V15.10 `start` md5 == Force 2003.5 / Force 2005.5 (Nicholas' list) → **one binary serves several products; the key selects the product** | `md5sum`, keyless `version_history.txt` |
| DS1991 key image = 3 secure subkeys × [ID 8][PW 8][DATA 48] + 64 B scratchpad. ID0 = part number `SAxxxxTT`, ID1 = date `MM/DD/YY`, ID2 = revision `R00` | keyflasher source + all dumps |
| Keyflasher's DS1991 crypto ported to `scripts/mtkey.py`; byte-exact vs. all 21 keyflasher decrypts, encrypt round-trips | `scripts/p1-verify-crypto.py` → `ok 21 bad 0` |
| Crypto schemes are **shared by pairs**: XL Gold = MAXX 2K, XL Platinum = MAXX Diamond, XL Titanium = MAXX Emerald | keyflasher params |
| Crown keys (`SA35xx`) decrypt with **no** known scheme; from the known plaintext/ciphertext pair: same DS91 structure, inc 0x16, seeds 0x42/0xA8/0x67, laserMath `03027D36` for serial `6D000000CB053702` (serial→laserMath formula still unknown) | `scripts/p1-crown-solve.py` |
| DOS key gate (Diamond V6.03 `0x2a4a0`): DATA0[0:8] must equal a de-obfuscated constant `PRSTUfw\x89`; ID0 (8 B) and ID2[0:4] are compared to copies in NVRAM — mismatch ⇒ "Dallas Key mismatch, re-initing NVRAM", not rejection | disassembly `analysis/p2/dia603_2a4a0.asm` |
| DOS hard-coded part-number special cases: `SA301901` (coin table override), `SA304208` (patched byte), territory `NJ…` (New Jersey lockout) | `0x2aa24`, `0x2abc8`, `0x2adc8` |
| DATA2 (subkey 2) carries a **2-bit-per-game** enable table; Diamond force-clears games 0x28/0x2d/0x2f in code | `0x2ab0c` |
| Territory **name** is on the key (DATA2+0x18, e.g. `USA-STD`, `CAN-VER2`, `PORTUGAL`); no territory-name table in the DOS exe | strings + dumps |
| Linux: key read through the USB I/O board (vendor control transfers); Nicholas' keyless replays raw USB `data_<wValue>_<wIndex>.bin` | keyless `mt_io.c` |

## Protection / key surface table (initial)

| # | Surface | Where | Type | Cadence | Status |
|---|---|---|---|---|---|
| A | DS1991 decrypt (per-version laserMath/inc/blkVCode) | DOS `0x84bdc..`, Linux `ReadKeyData`/`GetDecryptVal` | value-bearing | every boot | known for ≤Jade, Crown params partial |
| B | Magic DATA0[0:8] check | DOS `0x2a4a0` | bool-gate | every boot | found (Diamond) |
| C | Part-no / rev vs NVRAM | DOS `0x2a4a0` | re-init trigger | every boot | found (Diamond) |
| D | Part-number acceptance (which `SAxxxx` per version) | ? | bool-gate | every boot | **open** — hypothesis: implied by crypto+magic, no SA list |
| E | Territory: name, NJ, coin/currency, language | DATA0/DATA2, `KeyMgr::GetCountryCode/IsNJKey/IsUSAKey/GetCurrencyType/GetDefaultLangMask` | value-bearing | every boot | partial |
| F | Option locks (TournaMAXX etc.) | `KeyMgr::ExplodeOptions/GetOptionState/IsOptionSelectable` | value-bearing | runtime | open |
| G | Game enable table | DATA2 2-bit/game; Linux `SetGamePriceAndStatusFromKey` | value-bearing | every boot | partial |
| H | Laser-serial range check in menu exe | ? | bool-gate | ? | **open** |
| I | Online (MegaNet) serial checks — server side (`INVALID SERIAL NUMBER`, `SECURITY KEY VIOLATION`) | DOS string table `0x123fbc` | server | runtime | out of scope (server) |

## Phases (easiest → hardest)

1. **Key format field map** — all fields of DATA0/1/2/scratch across every version; DOS + Linux readers (`KeyMgr` names give semantics). Deliverable `Docs/01-key-format.md`.
2. **Version ↔ part-number acceptance** — per-version crypto params + magic constant + any SA checks, DOS (all 25) and Linux; resolve surface D and the "several SA numbers per version" observation. `Docs/02-version-acceptance.md`.
3. **Crown crypto** — recover serial→laserMath and scratch params from Crown `start.elf`; add to `mtkey.py`; decrypt `MCROWN_full_FF004000036F1F82`. `Docs/03-crown-crypto.md`.
4. **Territory & options** — country code, NJ/USA, currency, language masks, lockout, TournaMAXX/option bits (`KeyMgr`). `Docs/04-territory-options.md`.
5. **Serial (laser ROM) checks** — locate the range checks in menu executables. `Docs/05-serial-checks.md`.
6. **Validation in MegaPPBox** — craft keys with `mtkey.py`, boot them in the emulator rig (user-assisted where GUI is needed). `Docs/06-validation.md`.

## Blind-spot owners (guardrail 7)

| Blind spot | Owner |
|---|---|
| live vs dead key code (e.g. `XLKEYFILE` env debug path, SA special cases) | P2 (xref cadence) |
| runs-once vs every boot vs runtime (NVRAM re-init vs rejection; option checks at menu time) | P1/P4 |
| conditional paths (NJ, USA-only, family 0x02 vs 0x82 buttons, DS1991 vs DS1425) | P4 |
| data loaded at runtime (Linux: crypto may live in the I/O-board firmware rather than `start.elf` — `GetDecryptVal__5USBIO` suggests the board supplies a value) | P3 |
| packed regions (`start` launchers; Ruby 2/Sapphire `start.elf` entropy 6.1–6.2) | P3 |
| integrity self-checks (key data checksums — keyflasher has checksum logic for later formats) | P1 |
| time / counter bombs (key date field; NVRAM counters) | P4 |

## What the user may need to supply

- Plaintext/ciphertext of a second Crown key (or its `key` file produced by the same tool as `Crown USA-STD/key`), if P3 static recovery stalls.
- Running emulator sessions/screenshots for P6 (the MegaPPBox GUI can't be driven from here).

## Clause

New surfaces found during execution are expected and get appended to the surface table with
the phase that found them.
