# keyinfo.md — Megatouch Dallas security keys: everything learned

A self-contained technical handover for another instance. It covers the physical key, the crypto, how a
software version decides to accept a key, what the key controls (territory, games, prices, the option
locks), the laser-serial windows, the NVRAM that mirrors the key, and the tooling in this workspace.
It spans **every release from XL R1 (1997) to ION 2014**, i.e. the Maxx/XL line *and* the Force / ION
line, including the Gen 4 keys (DS1995/DS1996) that replaced the DS1991 MultiKey in 2007.
Each claim is tagged with how solid it is: **[verified]** = checked byte-exact or by experiment,
**[code]** = read from disassembly/decompile, **[inferred]** = consistent evidence but not directly
proven, **[open]** = unknown.

Canonical per-topic detail lives in `Docs/01`–`Docs/08` (Maxx/XL), `Docs/18` (Force/ION containers,
ciphers, passwords, signatures) and `Docs/19` (the Gen 4 field map, all 120 option names, game ids). Orientation for this workspace is `CLAUDE.md`
(read it first), and the working method is `METHOD.md`. This file condenses all of them.

---

## 0. Context and ground rules

- Merit Megatouch bartop/upright touch-screen arcade machines, 1997–2005. Two software lines:
  - **DOS line** XL R1 (1997) → MAXX Emerald 2 (2002): `C:\MERIT2\EXEC\MEGACDLL.EXE`, Watcom C,
    LE executable under the CauseWay DOS extender, plus per-game `*.DLL` and the operator menus in
    `SETUP.DLL`.
  - **Linux line** Ruby 2 (V11) → Crown (V16.10, 2005): i386 ELF `start.elf` (game; `start` is a packed
    launcher, ignore it) + `opsetup.so` (operator setup), g++ 2.9x with **dynamic C++ symbols** (names
    like `KeyMgr::ExplodeOptions` survive).
  - **Force / ION line** Force 2002 (DOS!) → Force 2011 and ION 2006 → ION 2014, plus Touch2Play 2013
    and Firefly 2010 on the same code base. Force 2003 onward are Linux `start` builds; from Force 2007
    the binaries are **not** packed and carry 12 000–17 000 dynamic C++ symbols plus generated
    enum tables in `libenums.so`. The class is `KeyManager` (the later name for `KeyMgr`).
  - **One binary serves several products** — Maxx Ruby 2 V11.00 and Force 2003.5 share a `start` md5,
    as do Jade 2 V15.10 and Force 2005.5. The *key* selects the product, not the binary.
- Every machine needs a Dallas iButton "security key" (DS1991 MultiKey or the family-0x82 DS1425
  equivalent). It holds the product's part number, territory, game list, prices and feature locks.
- Workspace rules: originals are immutable (work on copies under `analysis/`); every transformation is a
  script with input/output SHA-256; one canonical `Docs/NN-*.md` per phase.
- Context: authorized preservation / interoperability work.

### Where things are

| What | Path |
|---|---|
| Menu executables per version | `Executables/<version>/` (MEGACDLL.EXE, or start.elf + opsetup.so) |
| Key dumps | `Key Info & Dumps/New Keys` (superset of `Keys`); more in `F:/TouchPPBox Folder/keys` |
| Force / ION dumps | `Key Info & Dumps/Force - ION/` (Nicholas keys F2002–F2011 + I2006–I2014, Force 2011 block, ION 2014 USB capture) |
| Force/ION/T2P/Firefly disk images | `H:/Megatouch/Hard Disk Images/<product>/*.img` (use the extracted `.img`, never the archives) |
| Gen 4 binaries + XML configs | `analysis/p19/bin/<tag>/`, `analysis/p19/xml/<tag>/` (extracted read-only) |
| **The key editor** | `scripts/mtkeytool.py` (GUI) on `scripts/mtkeylib.py`; standalone copy in `Run/` |
| keyflasher (Java, Nicholas Navaroli) | `Key Info & Dumps/keyflasher 20240222/keyflasher/src/megatouch/` |
| Emulator rig (MegaPPBox, an 86Box fork) | `F:/TouchPPBox Folder/Rigs/05-megappbox-1.03/HDD Images/<product>/*.img` |
| Flattened DOS images | `analysis/flat/*.bin` (+ `.exports.txt`, `.imports.txt`, `.seeds.txt`) |
| Scripts | `scripts/` (catalogue in §13) |

---

### Product lines and releases [Docs/18, Docs/19, Docs/21]

| Key era | Maxx / XL | Force | ION and others | Button | Layout (`mtkeylib.LAYOUT`) |
|---|---|---|---|---|---|
| Gen 0/1 (DOS) | XL R1 … Double Diamond | - | - | DS1991 | dos |
| Gen 2 | XL Titanium, Emerald (DOS); Ruby 2 | Force 2002 (DOS), Force 2003 / 2003.5 | - | DS1991 / DS1425 | dos; ruby |
| Gen 3 | Sapphire, Jade, Crown | Force 2004, 2005 / 2005.5, 2006 | ION 2006 | DS1425 | sapphire (Sapphire, F2004); crown |
| Gen 4 | - | Force 2007-2011 | ION 2007-2014, Touch2Play 2013, Firefly 2010 | DS1995 (ION 2007) / DS1996 | gen4 |

- Byte-identical programs (packed `start` md5): Force 2003.5 = Maxx Ruby 2 V11.00, Force 2005 = Maxx Jade
  V14.00, Force 2005.5 = Maxx Jade 2 V15.10. So those Force builds enforce the Maxx serial windows.
- Force 2003 keys are cryptographically Ruby 2 keys (MRUBY cipher, MRUBY == F2003 passwords, Ruby
  signature); only the part number and game list differ - `mtkeylib` labels such a key "MAXX Ruby 2".
- Model numbers: Force 2002 SA3050, 2003 SA3059, 2004 SA3068, 2005 SA3083, 2006 SA3501/3504; ION 2006
  SA3505; F2007 SA3526, F2008 SA3542/3543, F2009 SA3570/3572, F2010 SA3579, F2011 SA3603/3604; I2007
  SA3522/3523, I2008 SA3547/3548, I2009 SA3559/3560, I2010 SA3590, I2011 SA3605/3607, I2012 SA3614/3617,
  I2013 SA3623/3624, I2014 SA3628/3630.
- `SA305945` is a Maxx Sapphire key (MSAPPHIRE cipher, **MSAPPHIRE passwords**, Sapphire signature) with
  the Force 2003 model number and the Force 2004 game list (D1 byte-identical to the F2004 key) [inferred:
  a Maxx-to-Force upgrade key; Merit's ION help text mentions "MAXX-to-FORCE upgraded games"]. Docs/02's
  "Sapphire SA3059 + SA3065" pairing rests on this key alone.
- Platform bit (game 0x44 Bowling): set on every DS1991-era Force/ION key, clear on Maxx Crown and on
  the genuine Maxx Sapphire SA306501.

## 1. The physical key

Two completely different containers across the range:

| Container | Family | Size | Payload | Protection | Used by |
|---|---|---|---|---|---|
| DS1991 MultiKey / DS1425 | `0x02`, `0x82` | 256 B | 3 × [ID 8][PW 8][DATA 48] + 64 B scratch | 3 passwords **and** a byte cipher | XL R1 → Crown, Force 2002–2006, ION 2006 |
| **DS1995** | `0x0A` | 2 KB | one 1024-byte block | **cipher only, no passwords** | ION 2007 |
| **DS1996** | `0x0C` / `0x8C` | 8 KB | one 1024-byte block at a per-version offset | **cipher only, no passwords** | Force 2007–2011, ION 2008–2014, Touch2Play, Firefly |

`KeyManager::Init` branches on `USBIO::GetKeyFamilyCode()`: `0x0C`, `0x8C` or `0x0A` ⇒ the Gen 4
layout, anything else ⇒ the legacy DS1991 layout. Every Gen 4 build still reads DS1991 keys. [code]

- **DS1991 MultiKey** (1-Wire family `0x02`) for XL R1 → Ruby. Ruby 2 → Crown keys are seen on family
  **`0x82`** buttons (DS1425, same command set). Jade, Jade 2 and Crown **require** 0x82 (§7). [verified]
- Memory: **3 secure subkeys**, each `[ID 8][PW 8][DATA 48]`, plus a **64-byte scratchpad**.
  - Reading a subkey's DATA needs its 8-byte password. A **wrong password returns pseudo-random bytes**,
    not an error. That is why one dump (`MJADE_full_64000000C235D602`, SA307933) has a garbage subkey 2.
  - The ID field is readable without the password.
- The 64-bit **ROM ID** ("laser serial") is factory laser-burned and **cannot be changed** on a real
  button: `family(1) | serial48 (6, little-endian) | CRC8(1)`.
  - Printed / keyflasher order is reversed: CRC first … family last, e.g. `6D000000CB053702` =
    CRC 0x6D, serial `00 00 00 CB 05 37`, family 0x02.
  - The games use ROM order `k[0]=family, k[1..6]=serial bytes, k[7]=CRC`.
  - CRC is Dallas/Maxim CRC-8 (poly x^8+x^5+x^4+1, reflected 0x8C) over the first 7 ROM bytes.
    Implemented in `scripts/p17-reserial.py::crc8`, which reproduces all real ROM IDs tested. [verified]

### keyflasher file formats
- `*_full_<serial>`: 256-byte encrypted image (`3 × [ID8 PW8 DATA48]` + scratch64) followed by the
  8-byte ROM ID in printed order (264 bytes total). Older files may be 256 bytes with the serial only
  in the filename.
- `*_decrypted_*`: 232-byte plaintext `ID0 D0 ID1 D1 ID2 D2 SCRATCH` (no passwords).
- `*_multikey_*` (192 B) in TouchPPBox/keys are **hand-made** plaintext for the old emulator, not dumps.
- In memory (DOS and Linux) a subkey stays `[ID8][PW8][DATA48]`, so a code offset `P+X` ↔ `DATA[X-0x10]`.
  Linux globals: `DallasKeyP1/P2/P3`, `DallasKeyScratch`, `k_laser` (ROM), `k_id1..3`, `k_data1..3`.

---

## 2. Cipher [verified, byte-exact vs keyflasher 21/21; Crown 0-byte diff vs known plaintext]

Per byte, per subkey, with the seed chained from ID into DATA:

```
enc = ((plain ^ laserMath[i % 4]) + seed) & 0xFF ;  seed = (seed + inc) & 0xFF
subkey s (0..2): seed starts at blkVCode[s] + 8*inc   (the 8 ID bytes are encrypted first with
                 seed = blkVCode[s], so DATA continues from +8*inc)
scratchpad:      seed starts at blkVCode[3], its own byte count
```

`laserMath` is 4 bytes derived from the ROM ID `k[0..7]` (family first), with arithmetic mod 256:

| Scheme | blkVCode | inc | scratch bytes | laserMath | Used by |
|---|---|---|---|---|---|
| M1 | — | 0 | — | all 0 (plaintext) | XL R1, Super 5000, XL 6000, MAXX V3.06 |
| XGOLD/M2K | 55 54 53 52 | 0x31 | 64 | A | XL Gold, MAXX 2K, 2K Plus |
| XPLAT/MDIAMOND | 55 54 53 52 | 0x31 | 64 | B | XL Platinum, Double Platinum, MAXX Diamond, Double Diamond |
| XTIT/MEMERALD | 73 3C AA E7 | 0x31 | 64 | C | XL Titanium, Titanium 2, MAXX Emerald, Emerald 2 |
| MRUBY | 61 E3 5A 13 | 0x17 | 48 | Ruby | Ruby 2 |
| MSAPPHIRE | A7 67 9A AA | 0x53 | 60 | Sapphire | Sapphire, Sapphire 2 |
| MJADE | FF 35 5A 4B | 0x16 | 60 | Jade | Jade, Jade 2 |
| **MCROWN** | **12 78 37 F3** | 0x16 | 60 (unproven) | Crown | Crown V16.10, **Force 2006, ION 2006** |

**The Force/ION DS1991-era keys reuse the Maxx ciphers byte for byte** [verified, 7/7 dumps byte-exact
and 7/7 encrypt round-trips]: Force 2002 = XTIT/MEMERALD, Force 2003 = MRUBY, Force 2004 = MSAPPHIRE,
Force 2005 = MJADE, Force 2006 and ION 2006 = MCROWN. Only the signature and the password init
constants differ. Force 2003's passwords are *identical* to Maxx Ruby 2's, so those keys are
interchangeable at the crypto layer — consistent with the shared `start` binary.

```
A  (M2K):   [k2 ^ ((k0+k1)|k4),  k2 | ((k0-k1)^k3),  k1 & (k3+k2+k4),  k4 | ((k3+k1)-k2)]
B  (Dia):   [k2 ^ ((k2+k1)|k4),  k2 | ((k3-k0)^k3),  k1 & (k3+k1+k4),  k4 | ((k0+k1)-k2)]
C  (Eme):   [k3 ^ ((k1+k4)|k2),  k1 | ((k2-k3)^k4),  k4 ^ (k3+k2+k1),  k2 | ((k4+k1)-k3)]
Ruby:       [((k1+k3)|k4)^k3,    ((k3-k4)^k3)|k1,    (k2+k1+k3)^k4,    ((k4+k2)-k1)|k2]
Sapphire:   [((k1^k3)-k5)+k3,    ((k0-k5)-k3)-k1,    ((k2-k1)+k3)^k5,  ((k5^k2)+k1)^k2]
Jade:       [((k1^k5)-k3)+k2,    ((k1-k5)-k4)-k2,    k5^k1,            k2^k4]
Crown:      [((k3-k4)-k5)^k1^0x7F, (((k1+k2)-k3)-k4)^0xF3, (k4+0xBC)^(2*k2+k1), 2*k4+k5+k1+0x7F]
```

- keyflasher has no Crown support. The Crown scheme was **recovered** here:
  - a known-plaintext solve on the CAN-VER2 dump gave inc 0x16 plus 4 bit-7-ambiguous seed solutions;
  - `start.elf` `ReadKeyData`/`USBReadKeyData` set blkVCode `12 78 37 F3`;
  - the laserMath formula comes from `merit_encrypt @0x0828bee0`;
  - the result decrypts `MCROWN_full_FF004000036F1F82` to the `Crown USA-STD/key` plaintext with 0
    differing bytes. [verified]
- Identify an unknown key by trying all schemes. A decryption is "plausible" when
  `ID0 = "SA" + 6 digits` and `ID1` matches `MM/DD/YY` (`mtkey.try_all`).

### Gen 4 cipher — Force 2007–2011, ION 2007–2014 [verified, 22/22 dumps byte-exact + round-trip]

No subkeys, no passwords: one keystream over the 1024-byte block, keyed by a 6-byte per-version magic
and the **inner six bytes of the ROM serial** (print order, so `serial[1..6]`).

```
ADD:  kk[i] = magic[5-i] + serial[6-i]
      for i in 0 .. 32*nChunks-1:  plain[i] = cipher[i] - ((i/32) ^ kk[i%6]) + (i/32)
XOR:  kk[i] = magic[5-i] ^ serial[6-i]
      bytes 18..21 first; for 2009/2010 kk[0..3] are then REPLACED by the ciphertext at 18..21;
      then plain[i] = cipher[i] ^ kk[i%6] for every byte outside 18..21
```

| Version | Part no. | Mode | Magic | Block offset |
|---|---|---|---|---|
| Force 2007 / ION 2007 | SA3526 / SA3522,SA3523 | ADD, 31 chunks | `55AA72371221` | 0 |
| Force 2008 / ION 2008 | SA3542,SA3543 / SA3547,SA3548 | ADD, 32 chunks | `55AA72371221` | 0 |
| Force 2009 / ION 2009 | SA3570,SA3572 / SA3559,SA3560 | XOR, key self-modifying | `36353759564E` | **1024** |
| Force 2010 / ION 2010 | SA3579 / SA3590 | XOR, key self-modifying | `3637374C4F42` | 0 |
| Force 2011 | SA3603, SA3604 | XOR | `393D3649564E` | 0 |
| ION 2011 | SA3605, SA3607 | XOR | `45414156594C` | **2048** |
| ION 2012 | SA3614, SA3617 | XOR | `726D5F6A634C` or `45414156594C` | **2048** |
| ION 2013 | SA3623, SA3624 | XOR | `6D6B5C68624C` | **6144** |
| ION 2014 | SA3628, SA3630 | XOR | `756F726E6260` | **2048** |

Force and ION share the magic wherever the year matches; they diverge from 2011, when Force stopped.

**The XOR cipher leaks its own key.** The plaintext starts with the ASCII part number `SAnnnn`, so six
known bytes hand over the whole 6-byte key; long runs of plaintext zeros print it outright. Inverting
`serial[6-i] = magic[5-i] ^ kk[i]` then recovers the button's serial *and* identifies the version
(`scripts/p18-xorsolve.py`). That is how `FORCE 2011.bin` (Force 2011, serial `0040_0003994F`) and the
V40.02 USB capture (ION 2014, `0040_0001A819`) were identified with no serial on file. [verified]

Gen 4 adds a **16-bit checksum** at 0x355: `Σ block[0..0x3EF]` minus bytes 18–21 and 0x355–0x356.
`KeyManager::Check` implements exactly that, independently confirming keyflasher's validators. Force
2007 / ION 2007 sum only to 0x35B instead. Every genuine dump validates. [verified + code]

### Passwords — the real version discriminator
- Each family has its own password generator (keyflasher `io/passwords/*PasswordGenerator.java`):
  3 × 8-byte init values from the ROM ID, then the same `merit_encrypt` loop with the family's
  laserMath ("magic"), `blkVCode[0..2]` and `inc`.
- Jade-style init (Jade, and Crown's legacy path) [verified for Crown and Jade dumps]:
  ```
  pass_s = copy(k);  pass_1[0] = 1; pass_2[0] = 2
  for i in 0..6: t = i + k[i] + C_s  (C = 0x27, 0x30, 0x42);  pass_s[i] = (t + t//0xFF) ^ pass_s[i]
  then for i in 0..7: p[i] ^= laserMath[i%4]; p[i] += seed; seed += inc   (seed = blkVCode[s]); & 0xFF
  ```
  Crown's USB path uses init constants `+3/+0x11/+0x99`, runs `merit_encrypt`, then XORs
  `0x18/0x19/0x1A` before sending to the I/O board. That only matters for the live board protocol. [code]
- M1-era keys use one fixed password `CC E3 AA F0 0F 3C AE CE` on all subkeys (also hard-coded in
  MAXX 3.06 at `0xC0814`).
- Pairs that share cipher + signature still have **different** passwords: XL Gold/2K,
  Platinum/Diamond, Titanium/Emerald. Some constants are literally x86 instruction bytes, e.g.
  Diamond's `83 F8 01 76 22 56 8B F0` = `cmp eax,1; jbe …`.
- keyflasher `*_full_` dumps store the passwords in each PW field. For the CAN-VER2 Crown dump they are
  exactly the generator's output for its own 0x02 serial.
- **All of them are now ported and checked**: `scripts/mtpass.py` reproduces the stored passwords of
  **48 of 49** dumps byte-exact, covering every scheme including the Force/ION ones. [verified]

| Password scheme | Init table | blkVCode / inc |
|---|---|---|
| M1 | fixed `CCE3AAF00F3CAECE` ×3, no encryption step | 0 / 0 |
| XGOLD, M2K, XPLAT, MDIAMOND, XTIT, MEMERALD | per-version fixed 3×8 constants | per scheme |
| **F2002** | Emerald constants XOR `02`/`31`/`10` | `733CAAE7` / 0x31 |
| MRUBY, **F2003** | Emerald constants XOR `02`/`31`/`10` (so F2003 ≡ MRUBY) | `61E35A13` / 0x17 |
| MSAPPHIRE | ROM-derived: `k7 % 7`, a shift chain, `k7 & 0x1F` | `A7679AAA` / 0x53 |
| **F2004** | ROM-derived: `k7 & 0xF`, two different shift chains | `A7679AAA` / 0x53 |
| MJADE, MCROWN | `t = i + k[i] + 0x27/0x30/0x42`, `(t + t/255) ^ p` | `FF355A4B` / `127837F3`, 0x16 |
| **F2005** | same shape, constants `0x03/0x11/0x99` | `FF355A4B` / 0x16 |
| **FI2006** (Force + ION 2006) | `t = i + k[i] + 0x03/0x11/0x99`, `p ^= t % 255` (mod, not `t + t/255`) | `127837F3` / 0x16 |

The one dump whose passwords match no generator is `SA002001_full_5B0000008E4C8A02` (the key the
Emerald V8.05 "exefix" image last ran with): Emerald cipher, a mangled Emerald signature
`DD62108621400293`, and a fourth init table — presumably an engineering/service key. [open, low value]

### Linux USB transport [code]
- On USB I/O-board cabinets (Cypress EZ-USB; vendor request 0xA0 = RAM read/write, 0xA1 = command), the
  host computes the passwords and writes them to board RAM 0x1CA0, then triggers 0xA1/wValue 2 and polls
  0x1C48.
- Subkeys come back from 0x1B48/0x1B88/0x1BC8 (64 B each), and the tail from 0x1C08 (0x2C B).
- Returned data is XOR-masked with a 4-byte value from `GetDecryptVal` (0xA1/wValue 4 → RAM 0x1C34).
  `FixKey__5USBIO` forces that value to `29 29 29 29`.
- The board firmware (`firmware` symbol, 0x11A5 B) is uploaded by `anchor_download`.
- The board EEPROM holds a separate machine serial (`ReadSNFromEEPROM`, magic `100293JKKJ` at 0x1FD6).
- Nicholas' keyless patches **replay** these USB transfers, which is why they never needed the cipher.

---

## 3. Plaintext layout (Gen 1-3; Gen 4 is in §3b)

IDs, all generations:
- `ID0` = part number `SA` + 4-digit model + 2-digit territory (`SA304201`);
- `ID1` = programming date `MM/DD/YY`;
- `ID2` = revision `R00`/`R01` (space- or NUL-padded).

Offsets below are into each subkey's 48-byte DATA (`D0/D1/D2`) or the scratchpad `SC`.

### Gen 0/1 — XL R1 → MAXX Double Diamond (signature at D0[0..7])
| Field | Where |
|---|---|
| signature | D0[0..7]: `11223344 55667788` (XL R1), `QRSTUfw\x88` (Super 5000), `PRSTUfw\x89` (XL 6000 → Double Diamond) |
| coin channels | D0[8..0x17], 4 × 4 bytes (`01 01 01 00`; Portugal `05 02 0A 00 / 01 01 05 00 …`) |
| region/language dword | D0[0x28..0x2B], byte-swapped on load: `0011007F` USA, `0020006F` S. Europe/Portugal, `0030008F` Canada, `0001007F` M1 |
| game table | D1[0..0x1F]: one nibble per game id 0x00–0x3F, 0 = not on the key; Diamond/Platinum/2K/3.06 value = price per play, Emerald/Titanium a class code [verified vs DOS NVRAM, Docs/21] |
| option table | D2[0..0x13], the same 80 × 2-bit table as Gen 3, MSB-first [verified: matches every DOS NVRAM's option bytes, Docs/21] |
| territory name | D2[0x18..0x21] |
| currency names | SC[8·i] (e.g. `DM1`, `DM2`, `DM5`) |

### Gen 2 — Titanium, Emerald, Ruby 2 (signature still D0[0..7])
Same as Gen 1 except the signature: `e8420886 67400282` (Titanium), `dd621043 21100293` (Emerald),
`de621043 21100293` (Ruby). D1 holds price nibbles on Titanium/Emerald and a game-ID list on Ruby.

Ruby 2 / Force 2003 game list (`SetGamePriceAndStatusFromKey`, Ruby 2 V11.00) [code, P21]: D1 is
scanned to offset 0x2F; a byte with **bit 7 set disables** game `byte & 0x7F` and consumes one byte,
any other byte is the first half of an `(id, price)` pair, and `FF` ends the list. Games not named in
the list are **on** at the default price `DallasKeyP3+0x32` = D2[0x22] (1 on both Ruby keys). So a
Ruby key is an opt-*out* list, unlike every other generation.

### Gen 3 — Sapphire, Jade, Crown (signature at D0[0x28..0x2F]) [code: Crown `KeyMgr`]
| Field | Where |
|---|---|
| TournaMAXX game cost / prize mode / prize rate | D0[1] bits 0–4 / bits 5–6; rate = `(D0[2]&0xF)*2 \| D0[1]>>7` |
| default language mask | D0[3..6] (LE u32) |
| coin channels ×6 | D0[7+4i], D0[8+4i], D0[9+4i] (coins / credits / pulses) |
| lockout value | D0[0x27] |
| **signature** | D0[0x28..0x2F]: `8723879f e2432498` Jade/Crown (or `…87`, §5), `12345678 90abcdef` Sapphire |
| price list | D1[0..0x1B]: a byte ≥ 0xF0 sets the running price to its low nibble; any other byte is a game ID at that price; `FF` ends the list |
| premium / default price | D1[0x1F] (games 0x71–0x74, 0xA3–0xA8) / D1[0x2A] (all other unlisted games) |
| territory name | D1[0x20..0x29] (Sapphire: D2[4]) |
| country code | D1[0x2E]: 0 USA, 1 Canada, 3/4 UK-style renames ("Crazy-Golf", "Race Cards", "21 Pontoon") |
| **80 option slots** | D2[0..0x13], 2 bits each, MSB-first: slot i = `(D2[i//4] >> (6 - 2*(i%4))) & 3` |
| **game enable bitmap** | D2[0x14..0x2F]: game g enabled ⇔ `D2[0x14 + g//8] & (0x80 >> (g&7))` (IDs 0x00–0xDF) |
| currency names ×6 | SC[8i..8i+7]; value = `atoi(name + 5)` |

The "platform bit" D2[0x1C] bit 3 used by the Crown gate is game **0x44** in that bitmap (§5).

### Sapphire / Force 2004 are laid out differently from Jade/Crown [code: Sapphire V12.01; corrected P21]

Gen 3 is not one layout. Sapphire and Sapphire 2 (and so Force 2004) move four of the five
key-driven regions:

| Field | Sapphire, Sapphire 2, Force 2004 | Jade, Jade 2, Crown |
|---|---|---|
| option table | **D2[0x16..0x2B], 22 B = 88 slots** (`KeyMgr::ExplodeOptions` reads `key+0x26+i`, `i < 0x16`) | D2[0..0x13], 80 slots |
| price list | **D1[0..0x11]** - `F<p>` + ids, or `(id, price)` pairs when D1[0] = 0 (`GetGamePriceFromKey`) | D1[0..0x1B] |
| game enable bitmap | **D1[0x12 + id/8]** (`SetGamePriceAndStatusFromKey` via `DallasKeyP2`) | D2[0x14 + id/8] |
| default price | **D2[2]** (`GetGamePriceFromKey` reads `DallasKeyP3+0x12`; 1 on all three Sapphire keys) | D1[0x2A] |
| territory name | **D2[4]** | D1[0x20..0x29] |

Consequence for §5: on a Sapphire or Force 2004 key the platform bit (game 0x44) is **D1[0x1A] bit
3**, not D2[0x1C] bit 3 - clear on the genuine Maxx Sapphire key `SA306501`, set on the Force 2004
key, exactly as the platform rule predicts. `SA305945`'s D1 is byte-identical to the Force 2004
key's, so that Sapphire-labelled key carries Force game data.

---

## 3b. Gen 4 plaintext layout (Force 2007+, ION 2007+) [code, from `KeyManager` in ION 2014]

`KeyManager::Read` does `memset(this, 0, 0x3F0)` then reads the decrypted block **straight into the
object at offset 0**, so every `[this+X]` with X < 0x3F0 in the Gen 4 branch of an accessor *is* key
offset X. (The legacy branch puts ID1 at `this+0x3F0`, D0 at `0x400`, D1 at `0x440`, D2 at `0x480`,
scratch at `0x4B0` — which independently reproduces the whole Gen 3 map in §3, including the game
bitmap at D2[0x14] whose bit for game 0x44 is D2[0x1C] bit 3.) The container holds 1024 bytes but the
game only consumes **0x3F0 (1008)**.

| Offset | Size | Field |
|---|---|---|
| 0x000 | 8 | part number, ASCII `SAnnnnTT` |
| 0x009 | 4 | **programming date — `time_t`, little endian** (ASCII `MM/DD/YY` in Gen 1–3) |
| 0x00D | 4 | revision, ASCII (`R00`) |
| 0x012 | 4 | serial-bound token; **excluded from the checksum** |
| 0x016 | 10 | territory / country description, ASCII |
| 0x02A | 200 | MegaNet server URL, ASCII |
| 0x0F2 / 0x0F3 / 0x0F4 | 1 each | country code / NJ exception number / lockout value |
| 0x0F5 | 8 | **signature** |
| 0x0FE / 0x100 / 0x102 | 2 each | ChampEdition game cost / prize mode (bits 5–6) / pool rate (×5) |
| 0x104 | 8 | language mask; 0x10C (4) default-language mask |
| 0x114 | 4 × 23 | currency name strings |
| 0x170 / 0x171 | 1 each | default pricing scheme / default currency |
| 0x172 / 0x192 / 0x198 | 6×f32 / 6×u8 / 6×f32 | coin channel value / credits per channel / credit value |
| 0x1B0 | 300 | **per-game price**: low nibble = price, high nibble = continue cost |
| 0x2DD | 120 | **option slots, one byte each** |
| 0x355 | 2 | **checksum** (u16 LE) |
| 0x357 / 0x359 | 2 each | unit time for games 0x2718 / 0x271B (seconds) |
| 0x35B | 100 | web portal URL, ASCII |
| 0x3BF | 48 | **game enable bitmap**, 300 bits, MSB first |
| 0x3EF | 1 | region |
| 0x3F0 | 16 | three copies of a 4-byte serial token; **never read by the game** |

Changes from Gen 3: the date became a `time_t`; the territory moved to 0x016 and the signature to
0x0F5; options went from 80 × 2 bits to **120 × 1 byte**; prices became a 300-entry nibble array; a
300-bit game bitmap and a 16-bit checksum were added; and the key now carries the MegaNet server URL
and the web-portal URL as plain strings.

---

## 4. Which keys a version accepts

### The SA digits are never checked [verified by emulator experiment, 2026-10-03]
A version accepts a key when:
1. one of the **password sets** compiled into it opens the three subkeys;
2. its **cipher** decrypts them;
3. the decrypted data carries the version's **8-byte signature**;
4. (Linux, Ruby 2 onward) the button's **ROM serial** is in that build's window (§7).

The part number (`ID0`) is only compared with the copy stored in NVRAM. A different one prints
"Dallas Key mismatch, re-initing NVRAM" and wipes the settings; **it never rejects the key**.

That is why one version "accepts several 6-digit models": Merit issued several part numbers (SKUs)
programmed with the same passwords, cipher and signature, for example:
- M1: SA3022 + SA3031;
- XL Gold: SA3033 + SA3039;
- Sapphire: SA3059 + SA3065;
- Crown: SA3511 + SA3513.

Experiment (`analysis/p6/`, built with `scripts/p6-craft.py`, which changes only ID0 and keeps the
passwords):
- Diamond, Emerald and Jade keys relabelled to the non-existent `SA999901`, plus an Emerald key
  relabelled to Titanium's real `SA305201`.
- All booted normally in MegaPPBox on MAXX Diamond V6.03, Emerald V8.04 and Jade V14.00 (stock "New"
  images), each showing only the NVRAM re-init.

Crown's only part-number test is a soft one: `ID0[0..1] == "SA"`, year `9x`/`00`–`05`, revision starting
with `R`. Two or more failures only set a flag.

Hard-coded part-number special cases (Diamond V6.03) modify data but never reject:
- `SA301901` (XL 6000 multikey) forces coin channels to 1;
- `SA304208` forces D1[0x2B] = 7;
- an `NJ…` territory enters New-Jersey mode ("Previous program was NJ version!!!",
  "Illegal attempt to update NJ system!!!").

### Signatures and password sets per DOS version [code]
The gate is the function that prints "Invalid Key [for version %s]!!!". It de-obfuscates the expected
8-byte signature (add/sub/shl/shr in code), compares it with D0[0..7], then compares ID0 and ID2[0..3]
with NVRAM.

| Version | Password sets | Cipher | Signature D0[0..7] |
|---|---|---|---|
| XL R1 | M1 fixed | none | `11223344 55667788` |
| XL Super 5000 R5B/R5E | M1 fixed | none | `QRSTUfw\x88` |
| XL 6000 R02/R04/R07, MAXX V3.06 | M1 fixed | none | `PRSTUfw\x89` |
| MAXX 2K V4.00 | M2K + M1 | XGOLD/M2K | `PRSTUfw\x89` |
| MAXX 2K V4.01, 2K Plus V5.00, XL Gold R00/R01 | XGOLD + M2K | XGOLD/M2K | `PRSTUfw\x89` |
| XL Platinum, Double Platinum, MAXX Diamond, Double Diamond | XPLAT + MDIAMOND | XPLAT/MDIAMOND | `PRSTUfw\x89` |
| XL Titanium, Titanium 2 | XTIT + MEMERALD | XTIT/MEMERALD | `e8420886 67400282`, or `dd621043 21100293` when the system type is MAXX |
| MAXX Emerald, Emerald 2 | MEMERALD + XPLAT | XTIT/MEMERALD | `dd621043 21100293` |

The Emerald transform uses an **unsigned** divide (a signed reading gives a wrong constant).

### Why most DOS builds carry two password sets: dual-platform builds [code]
From XL Gold onward every DOS build runs on both cabinet types. The second password set belongs to the
**other cabinet type**, chosen from the DOS boot environment (`C:\R.BAT`, `AUTOEXEC.BAT`):

- `XLSYSTYPE=MAXX` (or system-type byte 2 derived from `XLDATE`) selects the MAXX cabinet; otherwise
  it is an XL cabinet.
  - Diamond/Platinum/Emerald/Titanium pick the password set in one reader. In Diamond (`0x850c8`),
    MAXX selects MDIAMOND, else XPLAT; it also changes the bits sent to I/O port 0x22D.
  - Titanium also switches signature: raw `e8420886…` on XL, Emerald's `dd621043…` on MAXX.
- XL Gold and the 2K builds switch on `XLNEWIO=YES` (new MAXX-style I/O board): the old board uses the
  XGOLD reader, the new board the M2K reader.
- Other switches:
  - `XLKEYFILE=<file>` loads the key from a file (development feature; `NO` disables it);
  - `XLDEVSYS=YES` marks a development system;
  - `XLNVRFILE` names the NVRAM file;
  - also present: `XLHASMODEM`, `XLBASE`, `XLRUNDIR`, `XLRAMDRV`, `XLDYNSND`, `XLMOUSE`.
- Rule: **the key family must match the cabinet the software is running on.**
  - Titanium software on a MAXX cabinet wants an Emerald key; on an XL cabinet a Titanium key.
  - Diamond software on an XL cabinet wants a Platinum key.
  - Emerald's XL-side set is XPLAT, but Emerald still demands the Emerald signature and cipher. No
    shipped key matches that combination, so Emerald was effectively MAXX-only and Titanium was its XL
    counterpart.
  - All emulator rigs run `set xlsystype=maxx`.

### Force / ION signatures [verified, straight off the dumps]

DS1991 era, at D0[0..7] (Gen 1/2) or D0[0x28..0x2F] (Gen 3):

| Version | Signature | | Version | Signature |
|---|---|---|---|---|
| Force 2002 | `DD62104321100293` (= Emerald) | | Force 2003 | `DE62104321100293` (= Ruby) |
| Force 2004 | `1234567890ABCDEF` (= Sapphire) | | Force 2005 | `8723879FE2432498` (= Jade) |
| Force 2006 | `8624879FE2432498` | | ION 2006 | `342190FA11880410` |

Gen 4, at 0x0F5:

| Version | Signature | | Version | Signature |
|---|---|---|---|---|
| Force 2007 | `64563647452C2837` | | ION 2007 | `42367123EF235334` |
| Force 2008 | `E72136AB30C92156` | | ION 2008 | `5621C930AB3621E7` (F2008 reversed) |
| Force 2009 | `6874328C954F6743` | | ION 2009 | `213566732E476A32` |
| Force 2010 | `CFB4A9611BB72003` | | ION 2010 | `29342DA908FBC6DE` |
| Force 2011 | `90322BBAA4370CFE` | | ION 2014 | `93E41C6E20911B9B` |

ION 2014's `KeyManager::Check` accepts `93E41C6E20911B9B`, `CFB4A9611BB72003` and `00000000C7723CEF`
on the Gen 4 path, and `0123456789ABCDFF` plus one more on the legacy path. It also **reads its own
executable** (raw `open`/`read`/`close`, 0x400 bytes) before comparing — an integrity self-check
embedded in the key gate. [code, not analysed further]

### Linux signatures [code]
| Version | Signature | Notes |
|---|---|---|
| Ruby 2 V11.00/V11.05 | built from `e9420886 67400282` in `CheckKey(uchar)` → `de621043 21100293` at D0[0..7] | `start` is byte-identical to Force 2003.5 |
| Sapphire V12.01 / Sapphire 2 V13.00 | `12345678 90abcdef` (D0[0x28]) | V12.01 also has an XOR-0x11 hard-disk model check `HDIsOk` [not analysed] |
| Jade V14.00/V14.21, Jade 2 V15.10 | `8723879f e2432498` | Jade 2 `start` == Force 2005.5 |
| Crown V16.10 | `8723879f e2432498` or `8723879f e2432487` | gate `FUN_0823ff40` |

---

## 5. Maxx vs Force: the platform bit [code + inferred]

One Linux binary serves several products (Maxx and Force/ION share `start`), so the key selects the
product.

- **`ForceChk1()`** (installed at `MGlob+0x1b1d4`) is true only on **board type 4**: an Intel 810
  (82801/82810) board with CMI8738 audio, display type 6, the USB I/O board and a ready HDD. It chooses
  the "MegaTouch FORCE" vs "MegaTouch MAXX" banner.
- The Crown/Jade gate makes the expected signature's first byte +1 unless key **D2[0x1C] bit 3**
  equals `ForceChk1()`. Any high-bit character in the territory name also modifies it. On a mismatch the
  game shows an error screen, then crashes deliberately: it copies code after a `90 90 90` marker and
  jumps into it.
- D2[0x1C] bit 3 is game **0x44 = Bowling** in the game bitmap, and `gamedata.dat` flags Bowling
  **Force-only**. So the rule is: a key enables the Force-only game exactly when it runs on Force
  hardware. Both Crown keys here have it clear (Maxx).
- The alternate last byte `…87` (= `…98` − 0x11) is accepted by Jade, Jade 2 and Crown. keyflasher's
  Force 2005 wildcard suggests it is the Force/ION family [unconfirmed; needs a Force dump].
- **Motherboard whitelist** (`FUN_0823e340`, `/proc/pci` strings XOR-obfuscated with key `"12:16:29"`):
  - 1 = i430TX + ATI Rage IIC/264VT3;
  - 2 = i430VX + S3 Trio64;
  - 3 = VIA VT8501 + VT82C686;
  - 4 = i810 + CMI8738;
  - type 0 ⇒ `KeyShutDown("INVALID MOTHERBOARD DETECTED")`.

---

### Resolved: `…2487` is not the Force variant [verified, P18]

The earlier note that Crown's gate accepts `8723879FE2432498` **or** `8723879FE2432487`, with
`…2487` suspected to be the Force/ION value, is **wrong**. With real Force dumps in hand:

- Force 2005 carries the *same* `8723879FE2432498` as Maxx Jade — so `…2498` is not Maxx-specific.
- Force 2006 carries `8624879FE2432498` against Crown's `8723879FE2432498`: **byte 0 is −1 and byte 1
  is +1**. That is exactly the platform-check modifier ("if D2[0x1C] bit 3 disagrees with the platform
  check the expected first byte is +1"), observed from the key side for the first time.
- `…2487` (= `…2498` − 0x11) therefore belongs to the *other* modifier, the high-bit character in the
  territory name.

Platform bit D2[0x1C] bit 3 (on Sapphire/Force 2004: D1[0x1A] bit 3, Docs/21) across the dumps: set on Force 2004/2005/2006 and ION 2006, clear on every
Gen 1/2 Maxx/XL key and on Maxx Crown. Two keys with the same part number SA3079 differ in it, so it is
a per-key programming choice rather than a property of the SKU. [open: why a Jade-labelled key has it]

---

## 6. Territory (last two digits of the part number) [verified across dumps]

The numbering is the same in every generation. The key also carries the territory **name**, and from
Sapphire on a country code. A territory is really a bundle of defaults: coin channels, currency names,
language mask, lockout value.

| Suffix | Name on key | Seen on | Country code (Gen 3) |
|---|---|---|---|
| 01 | USA-STD (Ruby: `STD-USA`) | nearly every product | 0 |
| 04 | S EUROPE | MAXX 2K | — |
| 05 | PORTUGAL | MAXX 2K, Ruby 2 | — |
| 08 | (no dump; Diamond patches `SA304208` data) | — | — |
| 09 | USA-VER1 | MAXX 2K | — |
| 14 | USA-VER2 | M1 | — |
| 33 | CAN-VER2 / USA-CANV2 | Diamond, Jade, Crown | 1 |
| 45 | USA-STD (!) | Sapphire SA305945 (Maxx Sapphire key with the Force model number, §0) | — |

- An `NJ…` name means New-Jersey mode in every version (DOS `0x2adc8`, Linux `IsNJKey`). NJ rental mode
  is an NVRAM bit.
- Oddity: `SA002001` (Emerald cipher, 10/01/01) is named CAN-VER2 with suffix 01 and carries signature
  `dd621086 21400293`, which matches no build [open; probably non-production]. The Emerald V8.05
  "exefix" image last ran with it.

---

## 7. Laser-serial windows (Linux DS1991 builds only) [code; matches every real key]

**Gen 4 dropped them.** `InitVars` in the ION 2014 build compares no immediate ≥ 0x10000 and has no
`validate_key_range`-style callee; the only key-related calls are `Key()`, `KeyShutDown`,
`Unlock_System_Vars` and `findint3`. The window became redundant once the keystream was derived from
the button's own serial — a key written for one button simply decrypts to garbage on another and fails
both the signature and the checksum. Every genuine Gen 4 dump is still inside Merit's `0040_00xxxxxx`
block, but nothing in the software checks it. Platform discrimination also moved, from `ForceChk1` to
`system_info::SystemInfo::IsPlatformION/IsPlatformGameTime/IsPlatformMindSpark/HasESKey`. [code]


Check function (Crown `0x0823e140`), called from `InitVars` at boot and from `Unlock_System_Vars`. A
failure calls `KeyShutDown` ("KEY RANGE MISMATCH" on Ruby 2):

```
serial48 = ROM[6]:ROM[5]:ROM[4]:ROM[3]:ROM[2]:ROM[1]
accept ⇔ ROM[0] == 0x82 && serial48 >> 32 == 0x0040 && LO <= (serial48 & 0xFFFFFFFF) <= HI
```

| Version | Family | Accepted 48-bit serial |
|---|---|---|
| Ruby 2 V11.00/V11.05 | 0x82 | `0040_00000000`–`0040_000189C1` |
| | **0x02** | `0000_00B00DF9`–`0000_00B013AD` or `0000_00B026F9`–`0000_00B032B8` (two Merit DS1991 lots) |
| Sapphire V12.01, Sapphire 2 V13.00 | 0x82 | `0040_00010680`–`0040_00024000` |
| Jade V14.00/V14.21, Jade 2 V15.10 | 0x82 | `0040_00022917`–`0040_00053FFF` |
| Crown V16.10 | 0x82 | `0040_00031380`–`0040_00053FFF` |

- The windows move upward over time (Merit buying consecutive lots), and each build also accepts some
  older lots.
- **The Force builds enforce the Maxx windows**, proven by binary identity of the packed `start`
  launchers (md5) rather than by re-reading the constants [P21]:

  | Force build | byte-identical to | window enforced |
  |---|---|---|
  | Force 2003.5 v11.00 | Maxx Ruby 2 V11.00 | Ruby 2 |
  | Force 2005 v14.00 | Maxx Jade V14.00 | Jade |
  | Force 2005.5 v15.10 | Maxx Jade 2 V15.10 | Jade 2 |
  | Force 2003 v10.09, Force 2004, Force 2006, ION 2006 | binary differs or missing | nearest Maxx sibling [inferred] |

  The extracted Force `start` files are the packed launchers, which is why the window constants do not
  appear in them directly. `mtkeylib.check_serial(version, serial)` applies this table, plus the CRC
  and family rules, and for Gen 4 only the container rule: family must be DS1995 (0x0A) or DS1996
  (0x0C/0x8C) and the button must be large enough for the release's block offset - ION 2013 writes at
  7 KB, so it needs a DS1996.
- **No DOS version has a serial window.** DOS binds a key to its ROM only through the serial-derived
  cipher and passwords.
- Consequence: a family-0x02 DS1991 re-flashed with Jade/Crown data decrypts and passes the signature,
  but is shut down at boot. The CAN-VER2 Crown dump (`6D000000CB053702`) is exactly that.
  - Its passwords are keyflasher's output for its own serial, so it is probably Crown data re-flashed
    onto a blank. Origin unknown.
  - `scripts/p17-reserial.py` produced `analysis/p17/MCROWN_full_8900400004CA0282`: the same plaintext on
    an arbitrarily chosen serial `0x82 / 0040_0004CA02`, inside the Crown and Jade windows. It is for
    emulators only, since a real button's ROM cannot change.
- Known keys:
  - Jade `0900…57`/`4700…1B` pass Jade but are below Crown's window;
  - Crown USA `FF004000036F1F82` passes both;
  - Sapphire keys `0x19A95`/`0x11247` pass Sapphire only;
  - Ruby `EC00400000E98382` passes Ruby 2 only.
- **Anti-tamper:**
  - `findint3(fn)`: if byte 3 or 0x1C of the check function (or of `FUN_0823f970`) is `0xCC`, the game
    loops forever cycling video modes and logging "Not Jersey Key, Not Dallas Key, must be Florida Key".
    Do not set software breakpoints there.
  - Error strings are obfuscated by `u_m_m_s` (XOR with key string `m_m_k`).
- **Runtime presence check:** `ConfirmKeyID` / `USBIO::USBConfirmKeyID` re-reads the ROM ID; more than
  10 consecutive mismatches ⇒ `KeyShutDown("SECURITY KEY MISMATCH")`.
- Other serial uses (not checks):
  - the menu shows `ID: %02X…`;
  - TournaMAXX licensing derives the request code and checks the auth code from it
    (`TT_GetLicenseRequestCode`, `TT_ConfirmAuthCode`);
  - MegaNet login sends it, and the server has its own checks (out of scope).

---

## 8. The option slots (feature locks) — **all named** [code, exact]

Every DS1991-era key has the option table: **80 slots × 2 bits** at D2[0..0x13] — XL and DOS MAXX keys
included (*corrected P21*: earlier read as a per-game table) — except Sapphire/Force 2004, which keep
**88 slots at D2[0x16..0x2B]** (Docs/21). Gen 4 expands to **120 slots × 1 byte**
at 0x2DD, with `num_used_opts` = 120 sitting at index 0x78 in the enum. State semantics are unchanged:
**0 = locked off, 1 = forced on, 2 or 3 = operator-selectable** (then the effective value comes from
NVRAM).

Every slot name was lifted from the generated enum `xml_gameoptions::enum_GameOptionIndex_tag` in
`libenums.so` — a jump table, so the value → name mapping is exact, not inferred. The table is
**byte-identical across ION 2011, ION 2014, Touch2Play 2013 and Firefly 2010**, and it agrees with
every slot previously pinned by hand for Crown (0x0D six-star, 0x11 golf-has-women, 0x14 TournaMAXX,
0x31 lease), so slots 0x00–0x4F apply to the Gen 3 keys too. The full list is in `Docs/19`; the tool
loads it from `scripts/data/options.json`. A few of the notable ones:

| # | option | # | option |
|---|---|---|---|
| 0x0D | `six_stars_enabled_inx` | 0x14 | `tournamaxx_enabled_inx` |
| 0x11 | `golf_has_women_inx` | 0x1E | `allow_nudity_inx` |
| 0x29 | `free_play_enabled_inx` | 0x31 | `lease_mode_enabled_inx` |
| 0x02 | `enable_rental_mode_inx` | 0x3D | `enable_coinless_coinop_inx` |
| 0x5C | `allow_coin_in_table_modification` | 0x67 | `firefly_mode_enabled` |



### Gen 4 key-only switches on real keys [verified from the dumps, P21c]

ION 2014 / ION 2011 / Touch2Play classify 18 slots as key-only (`analysis/p21/I2014.slots.json`). States
on the genuine Gen 4 keys (F07 F08 F09 F10 F11 / I07 I08 I09 I14):

| Slot | Label | States |
|---|---|---|
| 0x14 | TournaMAXX (menu-set on ION, key-gated) | 1 3 1 1 1 / 3 3 3 3 |
| 0x0B | TournaMAXX allowed in free play | 1 1 1 1 1 / 1 1 1 0 |
| 0x0C | TournaMAXX price differs | all 1 |
| 0x0F | Rental mode 5-row price table | all 1 |
| 0x10, 0x2F, 0x31, 0x43, 0x47, 0x59, 0x5D, 0x6D, 0x72 | Touch2Play, senior, lease, MindSpark, Premiere terminal, KidZpace, UAE prize, MegaNet without TournaMAXX, download selector | all 0 |
| 0x1D | Disable free credits | all 0 |
| 0x39 | Prize Zone | 3 3 3 3 0 / 3 3 3 0 |
| 0x3F | Quick pricing | 1 1 1 1 1 / 1 1 1 0 |
| 0x51 | Alternate language selection | all 3 |
| 0x52 | Operator setup from Six Stars | 3 3 3 3 0 / 3 3 3 0 |
| 0x5C | Allow coin-in table changes | all 1 |

Reading: the product variants (Touch2Play, KidZpace, MindSpark, UAE, Premiere terminal, lease) are
key-only and off on every standard key - the same program becomes a different product by key. TournaMAXX
is never locked off on a Force/ION key (unlike Maxx Crown).

### What each slot does, and who sets it [P21: `scripts/data/option_catalog.json`]

Naming the slots is not the same as knowing what they do or who may change them. Both are now pinned
per release:

- **Descriptions.** **67 of the 120** slots carry Merit's *own* operator help text, harvested as
  `<b>Label</b>|text` strings out of 8 `opsetup.so` builds (`scripts/p21-help.py`). The remaining 53
  are described from the enum name plus the functions that read or write the slot, and are labelled as
  such in the catalogue (`source` = `merit` or `code`).
- **Five slots drifted in meaning** between the Crown era and Merit's later ION names (0x0C, 0x0F,
  0x2F, 0x43, 0x47). The catalogue carries both and the tool shows the Crown-era meaning on Jade/Crown
  keys.
- **Classes per release.** Who writes a slot was recovered from each release's own operator menus -
  Gen 3 from P12, Gen 4 from `scripts/p21-gen4slots.py` over `start` + `opsetup.so` + libs (ION builds
  via `MenuSystem::SETUP_OPTION` / `SetOptionValue` / `NVRAMMap::SetGameOption`):

  | Build | operator menu | key-only | other |
  |---|---|---|---|
  | Ruby 2 | 38 | 5 | 37 unused |
  | Sapphire | 51 | 5 | 1 runtime, 23 unused |
  | Sapphire 2 | 52 | 7 | 1 runtime, 20 unused |
  | Jade | 52 | 9 | 1 runtime, 1 remote, 17 unused |
  | Jade 2, Jade V14.21, Crown | 53 | 10 | 1 runtime, 1 remote, 15 unused |
  | ION 2011, ION 2014, Touch2Play 2013 | 69 | 18 | 33 unused |
  | Firefly 2010 | 74 | 13 | 33 unused (its unlock options are menu-set) |
  | DOS 3.06 → Emerald 2 | 16-20 traced | - | the rest reached through an untraced index table |

- **TournaMAXX (0x14) changed class.** Key-only on every Linux DS1991 build; on ION it is a menu
  toggle ("Select Tournament Mode"), still usable only when the key leaves the slot selectable.
- **Force 2007-2011** uses an older `KeyManager::Option(int)` API and its operator menus are not among
  the extracted binaries, so Force Gen 4 keys are shown with the ION 2011 classification, flagged
  "nearest".
- **DOS** `SETUP.DLL` addresses only 16-21 slots directly, so a DOS key's remaining slots are reported
  as "not traced" - never as key-only.

Gen 3 keys hold `D2[0..0x13]` = 80 two-bit states (Gen 1/2 use the same place for the same option
table; their games are the D1 nibbles).

| State | Meaning (bit 1 = operator may change; bit 0 = value/default) |
|---|---|
| 0 | locked **off** (hidden/unavailable) |
| 1 | locked **on** |
| 2 | operator-selectable, default off |
| 3 | operator-selectable, default on |

- The operator's stored choice is one byte per slot at NVRAM `options_base + slot` (Crown `0x8E`).
  **Effective value** = 0 if state 0, 1 if state 1, else the stored byte (`IsOptionOn`).
  `IsOptionSelectable` ⇔ state ∈ {2, 3}.
- **TournaMAXX = slot 0x14.** `NTournSupported` tests NVRAM `[0xA2]` = `0x8E + 0x14`.
  - Jade keys have state 1 (forced on); both Crown keys have 0 (locked off). That is the historical
    "TournaMAXX had to be enabled in the Crown key".
  - Slot 0x14 is a key-only switch in every Linux build: no menu writes it.
  - The Crown "TournaMAXX test" image has it stored on while its key locks it off.
- Slot 0x37 is **TouchTunes** (`TTM_*` menus), not TournaMAXX (an early misread, corrected).

### Slot names and Crown classes
Classes: op = operator setting, **key** = key-only switch, run = runtime, remote = set by the MegaNet
server, · = Crown never reads it. States are for keys Jade `0900` / Jade `4700` / Crown USA / Crown CAN.

| Slot | Feature | Class (Crown) | States |
|---|---|---|---|
| 00 | Free game (Power Solitaire family) | op | 3/3/3/3 |
| 01 | Allow game continue | op | 3/3/3/3 |
| 02 | Coin-op / rental mode | op | 2/2/2/2 |
| 03 | Licensed content support | op | 3/3/3/3 |
| 04 | Bonus replay | op | 3/3/3/3 |
| 05 | Price display / games per $ | op | 2/2/2/3 |
| 06 | (unused by Crown; key-only in Sapphire 2) | · | 0 |
| 07 | Split-column (Power Solitaire) | op | 3 |
| 08 | Erotic/kids category defaults | op | 2 |
| 09 | Trivia: show correct answer | op | 3 |
| 0A | Trivia round bonus | op | 3 |
| 0B | Free-play companion: idle adverts/attract | **key** | 1 |
| 0C | Local tournament in progress | run | 3 |
| 0D | Six Stars operator shortcut | op | 2 |
| 0E | Free game (Power Solitaire 2) | op | 3 |
| 0F | Pay-per-time (CCO) | **key** | 1 |
| 10 | (unused) | · | 3 |
| 11 | Golf has women (Ruby 2 only) | · | 1 |
| 12 | Photo Hunt hints | op | 3 |
| 13 | Merit Money | op | 3 |
| **14** | **TournaMAXX (network tournaments / MegaNet)** | **key** | **1/1/0/0** |
| 15 | TouchTunes music timer from six stars | op | 3 |
| 16 | Player-selectable language | op | 2 |
| 17 | Auto-clear high scores | op | 2 |
| 18 | (unused) | · | 1 |
| 19 | Moan sounds | op | 3 |
| 1A | Six-star access: high scores (Ruby 2/Sapphire); server-set from Jade on | remote | 3 |
| 1B | Six-star access: bookkeeping (Ruby 2/Sapphire) | · | 3 |
| 1C | Six-star access: volume (Ruby 2/Sapphire) | · | 3 |
| 1D | (read in GetNVRAM only) | **key** | 0 |
| 1E / 1F | Nudity allowed / nudity level | op | 3 |
| 20 | Show deck cards | op | 2 |
| 21 | Checkerz rules | op | 0/0/0/2 |
| 22 | Fan time | op | 3 |
| 23 | Language buttons show flags | op | 2 |
| 24 | Merit-thon / tournament bookkeeping | **key** | 0 |
| 25 | Six-star access: touch calibration (Ruby 2/Sapphire) | · | 3 |
| 26 | Tri-Towers face-up cards | op | 3 |
| 27 | Strip-club rewinds | op | 3 |
| 28 | Erotic games | op | 2 |
| 29 | Free play | op | 2 |
| 2A | Easy mode | op | 2 |
| 2B / 2C | Power Trivia same category / question mode | op | 2 / 3 |
| 2D | My Merit | op | 3/0/0/0 |
| 2E | Continue bonus round | op | 2 |
| 2F | Special screen / demo mode | **key** | 0 |
| 30 | Theft deterrent | op | 2 |
| 31 | Lease mode (TimeBomb) | **key** | 0 |
| 32 | Six-star access: TournaMAXX update (Ruby 2/Sapphire) | · | 3/3/0/0 |
| 33 | Promo credits | op | 3 |
| 34 | Linked games (Mega-Link) | op | 3 |
| 35 | No names in high scores | op | 2 |
| 36 | MegaWeb filter | op | 1 (locked on) |
| 37 | TouchTunes / hi-res video | op | 2/0/0/0 |
| 38 | MegaWeb | op | 2/0/0/0 |
| 39 | Prize Zone | op | 3/3/0/0 |
| 3A | Premium erotic | op | 2/2/0/0 |
| 3B | E-Channel | op | 3/3/0/0 |
| 3C | Educational attract | op | 3 |
| 3D | Price display / free-play pricing | op | 2/0/0/0 |
| 3E | Hot Topics / downloadable content | op | 3/3/0/0 |
| 3F | Coin setup / NJ rental | **key** | 1 |
| 40 | Premium-erotic ad screen | op | 3/3/0/0 |
| 41 | Attract-mode sounds | op | 3 |
| 42 | Operator Web | op | 2/0/0/0 |
| 43 | Scrolling marquee text | **key** | 0 |
| 44 | ShowTenders | op | 3/3/0/0 |
| 45 | Fantasy Sports (CDM) | op | 3/3/0/0 |
| 46 | Card-back advertising | op | 3 |
| 47 | Hide TournaMAXX ranking/events screens | **key** | 0 |
| 48–4A, 4C–4F | (unused by any Linux build) | · | various |
| 4B | Force slow senior game play | op | 0 |

Totals for Crown: 53 operator settings, 10 key-only switches, 1 runtime, 1 remote, 15 unused.

Timeline across builds (`Docs/04` has the full 7-build table):
- MegaNet services (0x36–0x40) arrive with Sapphire.
- Pay-per-time, lease, demo and marquee (0x0F, 0x31, 0x2F, 0x43) and Operator Web/ShowTenders/Fantasy/
  card-back ads (0x42–0x46) arrive with Jade.
- Senior play (0x4B) and the TournaMAXX-ranking switch (0x47) arrive with Jade 2.
- The six-star access set (0x1A–0x1C, 0x25, 0x32) is dropped after Sapphire 2.
- The Crown keys lock off every MegaNet service the Jade keys offer.

Method used: resolve the slot argument of every option-API call (`scripts/p10-slotcalls.py`), plus
direct NVRAM `base+slot` accesses. A slot is "operator" if a menu handler writes it.

---

## 9. Game table, prices and enables

**Gen 4**: game ids are the values of the generated enum `xml_gameinfo::GameIds`, recovered from
`enum_GameIds_tag` in `libenums.so`. The enum is sparse — ids 0x000–0x12B are real games (exactly the
range the key's 300-byte price array at 0x1B0 and 300-bit bitmap at 0x3BF cover) and a second block at
0x2718+ holds pseudo-entries that are *not* key-addressable (`g_menu`, `calibrate`, `browser`,
`layout`, `installer`, …). That second block is why reading the id order out of `gamedata.xml` or
`settings.xml` fails. Merging four ION builds pins **293 of 301** dense ids conflict-free; the Force
line is only partly pinned. Display names come from `<Description>` in each build's
`/usr/local/gamedata/config/gamedata.xml`. Ground check: decoding a genuine ION 2014 key with the
merged table and comparing against that machine's own `settings.xml` `GAME_ACTIVE` list scores a
Jaccard overlap of 0.79, with every residual explained (pseudo-entries, or games the operator turned
off); `gamedata.xml` order scores 0.43–0.58. [verified]


- **Game ID = record order** in the game table: Linux `/usr/local/share/merit/config/gamedata.dat`, DOS
  `C:\MERIT2\DATA\GAMEDATA.DAT`. Same text format: records start with `*`, `//` comments, one field per
  line.
- Linux fields: support-file name, DLL, description, directory, tournament rounds, max players, linkable
  units, idle name, language mask (hex), replay score, (unused), high-colour, sex flag, **other flags**
  (hex).
  - Other-flags bits: 0 H2H, 1 pro sports, 2 differs on Force/Maxx, 3 Merit-thon, 4 Prize Zone II,
    5 card-back ads, **6 Force-only**, 7 continuable.
  - Flags must be parsed as hex.
- DOS fields: same first nine (cost instead of language mask on 3.06), plus load-skips (default 20),
  high colour, sex flag, new/unused. There are no other-flags.
- Counts:

  | Build | Games |
  |---|---|
  | MAXX 3.06 | 51 |
  | 2K | 52 |
  | 2K Plus | 58 |
  | Diamond / Platinum | 63 |
  | Double Diamond | 69 |
  | Emerald / Titanium (and the "2"s) | 84 |
  | Sapphire | 146 |
  | Crown | 195 |
- Gen 3 enable rule (`SetGamePriceAndStatusFromKey`): the D2 bitmap bit, then Force-only games are
  disabled unless `ForceChk1()`. Price comes from the D1 list, else the default price.
- Example, Crown USA key: 101 games enabled; 13 at price 2 (Merit-thon events, Checkerz, Lonestar);
  default price 1.

### Where each family keeps its games and prices [P21]

| Family | Games | Prices |
|---|---|---|
| XL, DOS MAXX, Force 2002 | one nibble per id 0x00-0x3F in D1[0..0x1F], 0 = not on the key | the nibble *is* the price per play on Diamond/Platinum/2K/3.06; a class code on Emerald/Titanium |
| Ruby 2, Force 2003 | opt-out list in D1 (bit 7 set = disable), everything else on | `(id, price)` pairs in the same list; default D2[0x22] |
| Sapphire, Sapphire 2, Force 2004 | bitmap D1[0x12 + id/8] | price list D1[0..0x11]; default D2[2] |
| Jade, Crown, Force 2005/2006, ION 2006 | bitmap D2[0x14 + id/8] | price list D1[0..0x1B]; default D1[0x2A] |
| Force/ION 2007+ | 300-bit bitmap at 0x3BF (on the 2007 builds a nonzero price means enabled) | one byte per game at 0x1B0: low nibble price, high nibble continue cost |

Ground check for the Gen 1/2 reading: on fresh DOS NVRAM images a nibble of 1 gives per-game price 1,
2 gives 2 and 0 gives all-zero flags, with no exceptions (Docs/21 C2).

### Game names per release [P21: `scripts/data/game_tables.json`]

A game id means nothing without the table it indexes, and the tables differ per release, so the
editor carries **26**: 24 release `GAMEDATA.DAT` / `gamedata.dat` tables (DOS from `analysis/p16`,
Linux from `analysis/p14`, `analysis/p19/bin` and `analysis/p21/gamedata`) plus the two Gen 4 enum
tables (`ION4`, 293 names; `FORCE4`, filled from ION). Every one of the 33 releases maps to its own
software's table first; where no image exists the nearest is used and flagged (XL R1 / Super 5000 /
XL 6000 → MAXX 3.06, XL Gold → MAXX 2K).

- Ruby, Ruby 2 and Force 2003 keep `/usr/local/share/merit` on partition 7, so their table is
  `/config/gamedata.dat` there (`scripts/p21-gamedata.sh`).
- **Force 2006 ships a stale table**: its only image's `gamedata.dat` is entry-for-entry Force 2003's
  (102 games) while the Force 2006 key prices Crown-era ids up to 0xC1. Force 2006 and ION 2006
  therefore use Crown's 195-entry table.
- Force Gen 4 ids agree with the ION enum on **all 168 ids that could be pinned**, so ION fills the
  Force gaps - which closes the earlier "most Force-line ids unnamed" gap.
- Across the whole corpus, every enabled game on every DS1991-era dump now resolves to a name
  (asserted in `scripts/test-mtkeytool.py`).

---

## 10. NVRAM (the per-machine mirror of the key and operator settings)

### Storage
- **DOS:** the file named by `XLNVRFILE` (normally `C:\NVRAM.DAT`, 32 KB) **or** the I/O board's
  battery-backed SRAM at physical `0xC8000`. MEGACDLL exports `_NVRAMDATA`, `GETNVRAM_`, `PUTNVRAM_`.
  TournaMAXX-era DOS also has `C:\NTNVRAM.DAT`.
- **Linux:** `/var/config/nvram.dat` (64 KB Ruby 2, 128 KB later), with a backup in
  `/home/maxx/var.bak/config/`. Jade/Crown add a `db_nvram` database; TournaMAXX keeps
  `/var/merit/tournamaxx/ntnvram.dat`.

### Header (all versions)
| Offset | Field |
|---|---|
| 0x00 | valid flag (bad checksum ⇒ "NVRAM version mismatch or invalid checksum, clearing NVRAM") |
| 0x01–0x08 | copy of key ID0. A different key ⇒ "Dallas Key mismatch, re-initing NVRAM" |
| 0x09 | layout **base version**. A mismatch ⇒ "Bad NVRAM base version, exp %d, got %d" and clear |

### DOS layouts (base version is one counter shared by XL and MAXX)
| Base | Builds | Size | Options | Coin block | Books (offset, record, capacity) |
|---|---|---|---|---|---|
| 0x45 / 0x49 / 0x4A | XL 6000 R02 / R04 / R07 | 0x76F4–0x77E0 | 0x108 | 0x29 | 0x168, 42, 64 |
| 0x4D | MAXX 3.06 | 0x7B7B | 0x108 | 0x29 | 0x168, 42, 64 |
| 0x50 | XL Gold R00, MAXX 2K V4.00/4.01 | 0x7BC6 | 0x138 | 0x29 | 0x198, 42, 64 |
| 0x53 | XL Gold R01, 2K Plus | 0x7BCB/0x7BE3 | 0x138 | 0x29 | 0x198, 42, 64 |
| 0x59 | MAXX Diamond | 0x6CCF | 0x445 | 0x3F5 | 0x4A5, 36, 64 |
| 0x5A | XL Platinum, Double Platinum | 0x6CE5 | 0x445 | 0x3F5 | 0x4A5, 36, 64 |
| 0x5D | MAXX Double Diamond | 0x73FF | 0x445 | 0x3F5 | 0x4A5, 36, 72 |
| 0x65 | MAXX Emerald, XL Titanium | 0x7ECB | 0x3CF | 0x38D (rev copy 0x385) | 0x42F, 36, 84 |
| 0x66 | MAXX Emerald 2, XL Titanium 2 | 0x7F07 | 0x3CF | 0x38D | 0x42F, 36, 84 |

Coin block = 6 coins, then 6 credits, then 6 pulses (one byte each).

### DOS named settings (from SETUP.DLL; see the method in §12)
| Setting | 3.06 / XL 6000 | 2K / XL Gold | Diamond / Platinum | Double Diamond | Emerald / Titanium |
|---|---|---|---|---|---|
| total credits cur/life (u32) | 0x3C/0x40 | 0x6C/0x70 | 0x27/0x2B | 0x27/0x2B | 0x27/0x2B |
| free credits cur/life (u32) | 0x44/0x48 | 0x74/0x78 | 0x2F/0x33 | 0x2F/0x33 | 0x2F/0x33 |
| free-play credits cur/life | — | — | 0x37/0x3B | 0x37/0x3B | 0x37/0x3B |
| B2 coins, 6×f32 cur/life | 0xBC/0xD4 | 0xEC/0x104 | 0x3BD/0x3D5 | 0x3BD/0x3D5 | 0x355/0x36D |
| security PIN (str4) | 0xD33 (3.06 only) | 0xD63 | 0xF13 (Diamond; Platinum none) | 0x1033 | 0x116B |
| adult hours off/on (u8) | 0xD2C/0xD2D (3.06) | 0xD5C/0xD5D | | | |
| volume (u32) | 0x6764 (3.06) | 0x6797 | 0x58B8 / 0x58CA | 0x5FDA | 0x6A50 |
| tournament play / paid w/o PIN / claimed | 0x177C/84/8C (u32) | 0x17B3/BB/C3 | 0xF56/58/5A (Plat +4) | 0x107A/7C/7E | 0x11B2/B4/B6 |
| TouchTunes credits (u16) | — | — | — | 0x73F1 | 0x7E8D |

- MAXX 3.06 is **2K minus 0x30** below 0xE00. XL 6000 matches 3.06 and XL Gold matches 2K (same
  MEGACDLL access fingerprints). Neither XL 6000 nor XL Gold has been checked against a real NVRAM
  [inferred].

### DOS per-game books (record per game ID)
| Field | 36-byte record (Diamond → Emerald 2) | 42-byte record (3.06, 2K, XL 6000, XL Gold) |
|---|---|---|
| menu flags (0x03 on, 0x02 available, 0 not on key) | +0 u8 | +0 u8 |
| price per play | +1 u16 bits 0–3 | +1 u32 bits 0–7 |
| current books (credits) | +1 u16 bits 4–15 (max 4095) | +1 u32 bits 8–31 |
| lifetime books | +3 u32 | +5 u32 |
| loader skips (default 20) | +7 u8 | +9 u8 |
| current play time short/avg/long (s) | +8 u32 packed bits 0–9 / 10–19 / 20–31 | +0xA / +0xE / +0xC u16 (stored short, **long**, avg) |
| current games by player count 1–4 | +0xE 4×u16 | +0x12 4×u16 |
| lifetime time / players | +0x16 / +0x1C | +0x1A / +0x22 |

Some 3P/4P lifetime counters hold stray values (Platinum: `0x00507350`, which looks like a pointer) —
game-side overwrites, ignore them.

### Linux layouts
- Two families:
  - **Ruby-style** (Ruby 2 base 0x0A; Sapphire, Sapphire 2): options 0x3DA, coins 0x3C8, revision copy
    0x384.
  - **Jade-style** (Jade, Jade 2, Crown; base 0x10): options **0x8E**, coins 0x7C, currencies 0x40,
    revision copy 0x38.
- Base 0x10 is shared by Sapphire 2 and Jade/Crown, so pick the family by where the `R..` revision copy
  sits.
- Jade = Crown up to 0x49B, then −8 bytes from ~0x12C4. Crown appends ~1.1 KB of download-content
  counters.
- Crown map highlights:
  - 0x3C six-star PIN;
  - 0xE6+4·game per-game status/price;
  - 0x468/0x46C security lock mask / PIN;
  - 0x471/0x480 theft-deterrent PIN / week;
  - 0x12F0 default language;
  - 0x15280 volume;
  - 0x15360/0x15380 currency type / **value of credit (f32, 0.25)**;
  - 0x15714 **current credits (u16)**;
  - 0x156B0… pay-per-time;
  - 0x157DC/0x157E0 TouchTunes/TournaMAXX credits;
  - 0x157E8/0x157F1 location / operator number;
  - 0x159B4 copy of the key game bitmap.
- Named settings in other builds (Ruby 2 / Sapphire / Jade): `Docs/08` table and
  `analysis/p11/linux_fields.json`.
- Linux credit books live outside NVRAM, in `/var/config/amusement.db`:
  - **SQLite 2.1**, XOR-obfuscated with the repeating key `FC F1 BE 53`;
  - table `amusement_creditbooks(credit_type, curr_credits, life_credits, srvr_credits)`;
  - rows are not parsed yet (modern SQLite cannot open v2 files) [open].
- Real-data sanity values:
  - six-star PIN 4123 on factory images;
  - volume 38–86;
  - Jade V14.21 keyless image shows 641 credits;
  - Emerald 2 played image: 91 812 lifetime credits; Eleven Ball 14 353 lifetime credits;
  - Titanium V3.00 keyless crack leaves part number `SA305274` (fake territory 74) in NVRAM.

---

## 11. Recipes (how to do things here)

Run WSL tools from the **PowerShell tool** as `wsl bash /mnt/f/...script.sh`, because Git-Bash rewrites
`/mnt` paths; put complex arguments inside a script file. Windows Python uses `F:/` paths.

```bash
python scripts/mtkey.py decrypt "<key>_full_<serial>"          # identify scheme, write .dec232
python scripts/mtkey.py scan "Key Info & Dumps/New Keys"       # decrypt every dump found
python scripts/keyinfo.py <key> --games analysis/p14/MAXX_Crown_V16.10_-_New.gamedata.dat
python scripts/p6-craft.py <key> SA999901 <out>                # change ID0 only (same serial/passwords)
python scripts/p17-reserial.py <key> 82 00400004CA02 analysis/p17   # move a Jade/Crown key to a new ROM serial
python scripts/nvram.py <nvram file> [--key <dump>] [--games <GAMEDATA.DAT>] [--json]
python scripts/gamedata.py <gamedata.dat> [--json]
```

- To boot-test a key in MegaPPBox (GUI only; the user runs it):
  - use the product's stock "New" image, not a "Keyless"/"Patched" one, which bypasses or alters the
    key path;
  - pick a key whose serial is in that build's window;
  - "Dallas Key mismatch, re-initing NVRAM" then a normal boot = **accepted**; "Invalid Key", a key
    error or a shutdown = rejected;
  - the NVRAM gets reset.
- Extract files from rig images read-only: `scripts/p9-extract.sh` (NVRAM), `p13-extract-setup.sh`
  (SETUP.DLL), `p14-gamedata.sh` (Linux), `p16-dosgamedata.sh` (DOS), `p15-books.sh`. These use
  debugfs for ext2 and mtools at offset 63·512 for FAT.
  **Set `MTOOLS_SKIP_CHECK=1`**, or the Double Platinum image is silently skipped.

---

## 12. Reverse-engineering techniques that worked

1. **Watcom LE flattening.** `scripts/le_flatten.py` turns MEGACDLL.EXE / SETUP.DLL into a flat image at
   base 0x10000 with fixups applied.
   - It handles **import-by-ordinal** fixups and records each import's **additive**
     (`<flat>.imports.txt`: `va module:ordinal type +additive`).
   - It writes `.seeds.txt` (entry + fixup targets) for Ghidra.
2. **Ghidra headless** (11.3.2 in WSL, projects `~/ghidra-proj/mtkey` and `mtelf`).
   - Raw flat images find no functions unless seeded (`scripts/ghidra/seed.py`: entry + code-pointer
     fixups + Watcom prologue scan `[push r]* 55 89 E5`).
   - A running import locks its project, so use the other project or objdump.
   - Watcom register-call arguments are dropped by the decompiler; read the assembly for call arguments.
3. **Export names.** Every MEGACDLL is a CauseWay DLL exporting 155–723 named symbols
   (`scripts/le_exports.py` → `VA name ordinal`). `_NVRAMDATA` is ordinal **129** (Diamond onward) or
   **135** (MAXX/2K).
4. **SETUP.DLL NVRAM map.** SETUP imports `_NVRAMDATA` by ordinal; each fixup's additive **is the
   NVRAM offset**.
   - Label each offset by the string pointers within ±0x60 bytes (`scripts/p13-setupmap.py`).
   - Find arrays by an `imul reg,reg,stride` just before the access (`scripts/p16-dosarrays.py`).
   - Loop bounds give record counts.
   - Labels are text on 2K and later, but button-graphic names (`cow3`, `secpin`, `SetVol`) on 3.06.
5. **Linux:** symbols make it easy.
   - `KeyMgr::*` in opsetup.so is the key field map.
   - Setter functions (`STM_VolumeControl::ChangeSystemVolume`, …) pin NVRAM fields
     (`scripts/p11-*.py`).
   - Option slots: resolve the last immediate pushed before `IsOptionOn`/`SetOptionValue`.
6. **Fingerprinting builds without images.** Count absolute references to `_NVRAMDATA + offset` per
   build. Identical per-offset reference counts mean the same layout; this is how XL 6000 = 3.06 and
   XL Gold = 2K were established.
7. **Falsify before trusting.** The SA claim was tested by crafting keys that differ only in ID0. The
   Crown cipher was tested by a 0-byte diff against independent plaintext. Passwords were tested by
   regenerating the stored ones.

Pitfalls met:
- Emerald signature math is unsigned.
- gamedata flags are hex.
- DOS volume is the *last* `volloop` access.
- B2 coins are floats.
- Value-of-credit is f32; current credits on Linux is u16.
- Two blank (all-zero) NVRAM files share a hash; that does not mean they are the same version.
- Git-Bash has no `strings`.
- `rm` is blocked by the safety hook; move stale files aside instead.

---

## 13. Script catalogue (scripts/)

| Area | Scripts |
|---|---|
| Key crypto | `mtkey.py` (Gen 1–3 schemes incl. MCROWN), **`mtkey4.py`** (Gen 4 ADD/XOR ciphers + checksum), **`mtpass.py`** (every DS1991 password set), `keyinfo.py`, **`keyinfo4.py`** (Gen 4 field decode), `p6-craft.py`, `p17-reserial.py`, `p1-crown-solve.py`, `p3-crown-verify.py`, `p1-verify-crypto.py` |
| **Key editor** | **`mtkeytool.py`** (GUI), **`mtkeylib.py`** (model for all 4 generations), **`test-mtkeytool.py`** (regression suite), `data/{options,games}.json`, **`data/option_catalog.json`** (labels, descriptions, per-release classes), **`data/game_tables.json`** (26 game tables) |
| **Option meanings / game tables / packaging (P21)** | **`p21-optcatalog.py`** (build the option catalogue), `p21-help.py` (harvest Merit's help strings from `opsetup.so`), `p21-gen4slots.py` (Gen 4 menu vs key-only), `p21-gametables.py` (collect every release's game table), `p21-gamedata.sh` (extract the partition-7 tables), **`p21-build-exe.py`** (one-file Windows build via PyInstaller), `p21-update-share.py`, `p21b-update-docs.py` |
| Force / ION analysis | `p18-recover.py`, `p18-xorsolve.py` (identify a key with no serial), `p19-accessors.sh` (disassemble every `KeyManager` accessor), `p19-enum2.py` / `p19-enum3.py` (lift a generated enum table out of `libenums.so`), `p19-games4.py`, `p19-grid4.py` (cross-key differential) |
| Image extraction (read-only, WSL) | `p19-probe.sh`, `p19-find.sh`, `p19-extract.sh`, `p19-libs.sh`, `p19-xml.sh`, `p19-settings.sh` |
| DOS images | `le_flatten.py`, `le_exports.py`, `xref.py`, `immref.py`, `funcstart.py`, `callers.py`, `dis.sh`, `symdis.sh`, `disoff.sh` |
| Ghidra | `ghidra/{seed.py, import.sh, import_all.sh, import_linux.sh, decomp_at.py, decomp.sh, elf.sh, decomp_sym.py, refs_decomp.py, nvram_refs.py}` |
| Acceptance / serial | `p2-signatures.py`, `p2-blkvcode.py`, `p2-pwscan.py`, `p2-linsig.py`, `p5-rangescan.py`, `p5-rangedis.sh`, `p7-umms.py` |
| Options | `p10-slotcalls.py`, `p12-slotcalls.sh`, `p12-slotclass.py` |
| NVRAM | `nvram.py` (decoder), `p8-nvram-dos.py`, `p8-aggregate.py`, `p8-align.py`, `p11-fields.py`, `p11-semantic.py`, `p13-setupmap.py`, `p13-dossemantic.py`, `p16-dosarrays.py`, `p16-dosgames.py` |
| Extraction (read-only) | `p9-extract.sh`, `p13-extract-setup.sh`, `p14-gamedata.sh`, `p15-books.sh`, `p16-dosgamedata.sh` |
| Games | `gamedata.py` |

---

## 14. Status and open items (2026-10-03)

Done and verified:
- **the whole Force / ION line**: containers, both Gen 4 ciphers (22/22 dumps byte-exact + round-trip),
  every DS1991 password set (48/49 reproduced), signatures for every year;
- the **Gen 4 field map**, read out of `KeyManager` in the ION 2014 binary and cross-checked against
  the checksum the code itself computes;
- **all 120 option slots named**, exactly, from the generated enum tables;
- the Gen 4 game-id enum (293 of 301 for the ION line);
- a **key editor covering all 33 releases** (`scripts/mtkeytool.py`, standalone copy in `Run/`, plus a
  one-file `Run/Megatouch Key Tool.exe`), with a regression suite that loads 107 dumps, round-trips
  every one, generates all 33 releases, and checks the layout, name and serial rules;
- **what each option slot does** (67 of 120 in Merit's own help text) and **who sets it**, per release;
- **per-release game names** (26 tables) and the per-family game/price layouts;
- the **serial-window check** for every release, including the three Force builds proven byte-identical
  to their Maxx siblings;
- crypto for every version, including the recovered Crown scheme;
- acceptance logic, with the SA digits unchecked (emulator-confirmed);
- dual-platform DOS builds;
- the Maxx/Force platform bit;
- serial windows for every Linux build;
- territory numbering;
- all 80 option slots named and classified across 7 Linux builds;
- NVRAM layouts and named settings for every DOS and Linux layout;
- per-game books with names;
- re-serialising keys for emulators.

Open:
1. ~~Confirm the `8723879f e2432487` signature belongs to Force/ION keys.~~ **Closed** — it does not;
   the Force modifier lands on byte 0 (§5b). A **genuine ION 2014 key dump** is still wanted: the only
   sample is internally inconsistent (country code 1 with territory `USA-STD`, date decoding to 1977).
2. Parse SQLite 2 rows of `amusement.db` (Linux credit books).
3. Name the DOS option slots per layout. `nvram.py` currently shows Crown names for DOS options,
   which is wrong; the key editor labels them from the catalogue instead (see item 9).
4. Check the XL 6000 / XL Gold layouts on a real image, and add XL 6000 game names; XL R1 / Super 5000
   are unmapped.
5. Emerald/Titanium meaning of the D1 game nibble (a class code, not the price); Crown scratchpad byte count (60 assumed).
6. `SA002001` (odd signature); Sapphire V12.01 `HDIsOk` hard-disk check (not analysed).
7. MegaNet server-side serial checks: out of scope.
8. The Gen 4 serial-bound tokens at 0x012 and the three copies at 0x3F0. Across six otherwise
   byte-identical ION 2009 keys these are the *only* differing bytes, and nothing in `start` reads
   0x3F0 — likely the programmer's own anti-clone marker.
9. Which options the **DOS** operator menus offer: the DOS keys carry the same 80-slot table, but
   `SETUP.DLL` reaches most slots through an index table that has not been traced, so only 16-21 per
   layout are confirmed as menu settings. Likewise the **Force 2007-2011 operator menus** are not
   among the extracted files, so those keys are classified from ION 2011.
10. ~~Labels for most of the Force-line game ids.~~ **Closed** - the Force ids agree with the ION enum
    on all 168 that could be pinned, so ION fills the gaps. 8 ION ids out of 301 remain unlabelled (an
    extractor limitation on fall-through switch leaves, not an unknown in the format).
11. The Gen 4 NVRAM layout: settings moved to `/merit/settings.xml` plus SQLite and `/config/nvram.dat`
    shrank to 5 792 B, so none of the §10 NVRAM work carries over.
12. The executable self-read integrity check inside `KeyManager::Check` (surface N).

<!-- p20: Force/ION + Gen 4 content merged -->

<!-- p21b: option meanings, per-release game names, per-family layouts -->

<!-- p21c: Force / ION woven through every topic -->
