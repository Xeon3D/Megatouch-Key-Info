# 02 — Which keys a version accepts (part number ↔ version)

Evidence: `scripts/p2-signatures.py` (+ manual check of the Emerald transform), `p2-blkvcode.py`,
`p2-pwscan.py`, `p2-linsig.py`; disassembly in `analysis/p2/`; Crown gate decompile
`analysis/p5/crown_serialcheck.c` (`FUN_0823ff40`).

## Answer in one paragraph

**The 6-digit model number (`SAxxxx`) is never validated.** A version accepts a key when (1) one of
the password sets compiled into it opens the three subkeys, (2) its cipher decrypts them, and (3) the
decrypted data carries the version's 8-byte **signature**; Jade/Jade 2/Crown additionally require a
family-0x82 button with a serial in Merit's purchased range (`Docs/05`). The part number is only
compared against the copy stored in NVRAM — a different part number makes the game print
"Dallas Key mismatch, re-initing NVRAM" and wipe settings, not reject the key. That is why one version
"accepts more than one set of 6 digits": Merit issued several part numbers (SKUs) programmed with the same
password/cipher/signature (e.g. M1 SA3022 + SA3031, XL Gold SA3033 + SA3039, Sapphire SA3059 + SA3065,
Crown SA3511 + SA3513), and some binaries carry two password sets (upgrade paths).

Guardrail-6 check: the boring explanation is "no SA list exists". Searched: no SA digit compare in any
DOS gate; Crown's only part-number test is `ID0[0]=='S' && ID0[1]=='A'` (and even that is a soft
error counter). **Falsification test run 2026-10-03 (user, MegaPPBox): passed.** `analysis/p6/` holds
Diamond, Emerald and Jade keys whose ID0 was changed to the non-existent `SA999901`, and an Emerald key
relabelled with Titanium's real part number `SA305201`. Everything else, passwords included, was left
unchanged. All four booted normally on MAXX Diamond V6.03, Emerald V8.04 and Jade V14.00 (stock "New"
images), so the SA digits are not checked by DOS or Linux builds.

## DOS versions (MEGACDLL.EXE)

Gate function = the one printing "Invalid Key [for version %s]!!!". It compares an 8-byte signature
(stored obfuscated, de-obfuscated with add/sub/shl/shr in the function) to the first 8 data bytes of
subkey 0, then compares ID0 (8 B) and ID2[0..3] with NVRAM.

| Version | Gate | Password sets in binary | Cipher | Signature D0[0..7] |
|---|---|---|---|---|
| XL R1 | `0x1b5xx` | M1 fixed | none | `11223344 55667788` |
| XL Super 5000 R5B/R5E | `0x189xx` | M1 fixed | none | `QRSTUfw\x88` |
| XL 6000 R02/R04/R07 | `0x19a50`… | M1 fixed | none | `PRSTUfw\x89` |
| MAXX V3.06 | `0x1b044` | M1 fixed (`0xC0814`) | none | `PRSTUfw\x89` |
| MAXX 2K V4.00 | `0x193a0` | **M2K + M1 fixed** | XGOLD/M2K | `PRSTUfw\x89` |
| MAXX 2K V4.01, 2K Plus V5.00 | `0x19420`, `0x1ab04` | **XGOLD + M2K** | XGOLD/M2K | `PRSTUfw\x89` |
| XL Gold R00/R01 | `0x1a9c8`, `0x19b84` | **XGOLD + M2K** | XGOLD/M2K | `PRSTUfw\x89` |
| XL Platinum V1.02, Double Platinum V2.00 | `0x287c0`, `0x287b4` | **XPLAT + MDIAMOND** | XPLAT/MDIAMOND | `PRSTUfw\x89` (obfuscated) |
| MAXX Diamond V6.03/6.20, Double Diamond V7.01/7.20 | `0x2a4a0`, `0x2aea4` | **XPLAT + MDIAMOND** | XPLAT/MDIAMOND | `PRSTUfw\x89` (obfuscated) |
| XL Titanium V3.00, Titanium 2 V4.00 | `0x1d028`, `0x1d4b0` | **XTIT + MEMERALD** | XTIT/MEMERALD | `e8420886 67400282`, or **`dd621043 21100293` when a mode byte == 2** |
| MAXX Emerald V8.04/8.05/8.20, Emerald 2 V9.00/9.01 | `0x1cdb8`… | MEMERALD + XPLAT | XTIT/MEMERALD | `dd621043 21100293` |

**Why two password sets: every DOS build from XL Gold onward is dual-platform (P7, 2026-10-03).**
The second set is not "a second key family accepted"; it is the key family of the *other cabinet
type*. The platform comes from the DOS boot environment:

- `XLSYSTYPE=MAXX` (or a system-type byte == 2, derived from `XLDATE`) ⇒ MAXX cabinet;
  otherwise XL cabinet (Diamond `0x25fb0` → global `0x150148`; Titanium `0x1891c` → `0xF83EB`).
- Diamond/Platinum/Emerald/Titanium pick the password set in one reader from that value
  (Diamond `0x850c8`: `[0x123618]==1` ⇒ MDIAMOND set, else XPLAT set; it also changes the bits sent to
  I/O port 0x22D). Titanium additionally switches its signature (raw `e8420886…` on XL, Emerald
  `dd621043…` on MAXX).
- XL Gold (and the MAXX 2K builds) instead switch on `XLNEWIO=YES` (new MAXX-style I/O board): old
  board ⇒ `0x1b2d4` with the XGOLD constants; new board ⇒ the MAXX reader `0x6f4e8` with the M2K set.
  `XLDEVSYS=YES` marks a development system; `XLKEYFILE=<file>` loads the key from a file (dev feature;
  `NO` disables it). Other switches present: `XLHASMODEM`, `XLBASE`, `XLRUNDIR`, `XLNVRFILE`,
  `XLRAMDRV`, `XLDYNSND`, `XLMOUSE`.

So: **the key family must match the cabinet the software is running on.** XL Titanium software on a
MAXX cabinet (`XLSYSTYPE=MAXX`) wants an Emerald key; on an XL cabinet a Titanium key. Diamond software
on an XL cabinet wants a Platinum key. MAXX 2K V4.00 on an XL board reads with the M1 fixed password
(original MAXX keys). Emerald's XL-side set is the XPLAT passwords, but Emerald still demands the
Emerald signature and cipher. No shipped key matches that combination, so Emerald was effectively
MAXX-only and Titanium was its XL counterpart.

Reading the table:
- Titanium accepts Titanium keys and — in mode 2 — Emerald-signature keys; it also carries the
  Emerald passwords, so Titanium ⇐ Emerald keys is fully supported by code.
- XL Gold and MAXX 2K/2K Plus share cipher+signature and both carry XGOLD+M2K passwords ⇒ they should
  cross-accept XL Gold and 2K keys. MAXX 2K V4.00 instead carries M1 + M2K ⇒ accepts original MAXX keys.
- Platinum/Double Platinum/Diamond/Double Diamond all carry XPLAT+MDIAMOND ⇒ cross-accept.
- Emerald carries the XPLAT passwords but its signature/cipher differ from Platinum keys; the purpose of
  that second set (read-old-key-for-upgrade?) is **open**.
- XL Gold's read path (`0x1b084`): optional key-from-file override → raw subkey reads with the XGOLD
  constants (`0x1b2d4`) → gate (`0x1b380`) → if valid and a flag is clear, a second encrypted read with
  the serial-derived M2K-style passwords (`0x6f4e8`). The exact selection between the two sets is
  **open** (P6 emulator test will settle it).

Hard-coded part-number special cases (Diamond V6.03; they only *modify* data, never reject):
`SA301901` (XL 6000 multikey) → coin channels forced to 1; `SA304208` → D1[0x2B] forced to 7;
territory `NJ…` → New-Jersey mode (refuses to run a non-NJ key after an NJ key without operator action:
"Previous program was NJ version!!!", "Illegal attempt to update NJ system!!!").

## Linux versions (start.elf)

| Version | Signature (D0[0x28..0x2F] for Gen 3) | Notes |
|---|---|---|
| Ruby 2 V11.00 / V11.05 | built from `e9420886 67400282` in `CheckKey(uchar)` (→ Ruby `de621043 21100293` in D0[0..7]) | same `start` md5 as Force 2003.5 (V11.00) |
| Sapphire V12.01 / Sapphire 2 V13.00 | `12345678 90abcdef` | V12.01 also has an XOR-0x11 hard-disk model check (`HDIsOk`) |
| Jade V14.00/V14.21, Jade 2 V15.10 | `8723879f e2432498` | Jade 2 `start` md5 == Force 2005.5 |
| Crown V16.10 | `8723879f e2432498` **or** `8723879f e2432487` | `FUN_0823ff40` |

Crown's gate (`FUN_0823ff40`): reads key (USB or legacy), soft checks (`SA` prefix, date year
`9x`/`00`–`05`, rev starts `R`; ≥2 failures only set a flag), then the signature test with two
modifiers that change the expected first byte: D2[0x1C] bit 3 must agree with a platform check
(`MGlob+0x1b1d4`), and any high-bit character in the territory name. Mismatch → error screen then a
deliberate crash (copies code after a `90 90 90` marker and jumps into it).

Because one Linux binary serves several products (Maxx and Force/Ion share `start`), the product the
machine boots as is selected by the key contents, not by the binary.

### Maxx vs Force on the shared Linux binaries (P7)
Jade, Jade 2 and Crown run the identical gate, and keyflasher's Force validators show the same signature
families (Force 2003 = Ruby `de621043…`, Force 2004 = Sapphire `1234567890abcdef`, Force 2005 =
`..23879FE24324..`, Force 2006 = `8624879F E2432498`). What separates the products:

- `ForceChk1()` (installed as `MGlob+0x1b1d4`) is true only on **board type 4** (Intel 810 82801/82810 +
  CMI8738) with display type 6, the USB I/O board and a ready HDD. It picks the "MegaTouch FORCE" vs
  "MegaTouch MAXX" banner.
- The key's **platform bit** D2[0x1C] bit 3 must agree with `ForceChk1()`; otherwise the expected
  signature's first byte is +1 and the key fails. A Force key won't boot on Maxx hardware and vice versa.
  Both of your Crown keys have it clear (Maxx). *Refined P14:* that bit is game **0x44 (Bowling)** in the
  key's game bitmap, and `gamedata.dat` flags Bowling **Force-only**. So the rule is "a key enables the
  Force-only game exactly when it runs on Force hardware".
- The alternate last byte `…87` (= `…98` − 0x11) is accepted by all three gates. **Resolved P18
  (reclassified): it is NOT the Force variant.** Force dumps now exist (`Docs/18`): Force 2005
  carries the *same* `8723879FE2432498` as Maxx Jade, and Force 2006 carries
  `8624879FE2432498` — i.e. the Force/Maxx difference lands on **byte 0** (−1, with byte 1 +1),
  which is the platform-bit modifier. `…87` therefore belongs to the other modifier, the
  high-bit character in the territory name.
- Board detection (`FUN_0823e340`, `/proc/pci` strings, XOR-obfuscated with key `"12:16:29"`):
  1 = i430TX + ATI Rage IIC/264VT3, 2 = i430VX + S3 Trio64, 3 = VIA VT8501 + VT82C686,
  4 = i810 + CMI8738. Type 0 ⇒ `KeyShutDown("INVALID MOTHERBOARD DETECTED")`.

## Open items
- ~~Confirm `…2487` = Force with a Force/ION key dump.~~ **Closed P18** — see above; `…2487` is
  the territory-name modifier, not Force. Force/ION signatures for every year are tabulated in
  `Docs/18` (DS1991 era) and `Docs/19` (Gen 4).
- Why a Sapphire/Jade-labelled key (SA3079, serial `0900400002B65782`) carries the Force
  platform bit D2[0x1C] bit 3 set while another SA3079 key has it clear (`Docs/18`).
