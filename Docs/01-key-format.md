# 01 — Key format (all generations)

Evidence: `scripts/mtkey.py` (crypto, byte-exact vs keyflasher: `p1-verify-crypto.py` → 21/21), the
cross-key grid `analysis/p1/raw_keygrid.txt` (`p1-keygrid.py`, 23 unique keys), Crown `opsetup.so`
`KeyMgr::*` decompile (`analysis/p1/crown_keymgr.c`), Crown `start.elf` key readers
(`analysis/p1/crown_start_key.c`), DOS Diamond V6.03 loader (`analysis/p2/dia603_*.asm`).

## Physical container

- Dallas DS1991 MultiKey (family `0x02`) up to Ruby; Ruby 2 → Crown keys seen on family `0x82`
  buttons (DS1991-compatible command set). Jade/Jade 2/Crown **require** family `0x82` (see `Docs/05`).
- 3 secure subkeys, each `[ID 8][PW 8][DATA 48]`, + 64-byte scratchpad. Subkey reads need the 8-byte
  password; a wrong password makes the button return pseudo-random data (that is what the garbage
  subkey 2 in `MJADE_full_64000000C235D602` / SA307933 is).
- keyflasher files: `*_full_<serial>` = 256-byte image + 8-byte serial suffix; `*_decrypted_*` = 232-byte
  plaintext `ID0 D0 ID1 D1 ID2 D2 SCRATCH`. Serial string order = OneWire print order (CRC … family);
  the ROM byte order used by the games is the reverse (`family, s1..s6, crc`).
- In-memory (both DOS and Linux) each subkey is `[ID 8][PW 8][DATA 48]`, so code offset `P+X` ↔ DATA[X-0x10].
  Linux globals: `DallasKeyP1/P2/P3`, `DallasKeyScratch`, `k_laser` (ROM), `k_id1..3`, `k_data1..3`.

## Cipher (per byte, per subkey, seeds chained ID → DATA)

`enc = ((plain ^ laserMath[i%4]) + seed) & 0xFF; seed += inc`. Subkey s starts at
`seed = blkVCode[s] + 8*inc` (s = 0..2); scratch uses `blkVCode[3]` and its own byte count.
laserMath is 4 bytes derived from the laser ROM.

| Scheme | blkVCode | inc | scratch bytes | laserMath | Used by |
|---|---|---|---|---|---|
| none ("M1") | — | 0 | — | 0 | XL R1, Super 5000, XL 6000, MAXX (V3.06) |
| XGOLD/M2K | 55 54 53 52 | 0x31 | 64 | formula A | XL Gold, MAXX 2K/2K Plus |
| XPLAT/MDIAMOND | 55 54 53 52 | 0x31 | 64 | formula B | XL Platinum/Double Platinum, MAXX Diamond/Double Diamond |
| XTIT/MEMERALD | 73 3C AA E7 | 0x31 | 64 | formula C | XL Titanium/Titanium 2, MAXX Emerald/Emerald 2 |
| MRUBY | 61 E3 5A 13 | 0x17 | 48 | Ruby formula | Ruby 2 (Linux) |
| MSAPPHIRE | A7 67 9A AA | 0x53 | 60 | Sapphire formula | Sapphire / Sapphire 2 |
| MJADE | FF 35 5A 4B | 0x16 | 60 | Jade formula | Jade / Jade 2 |
| **MCROWN (new)** | **12 78 37 F3** | 0x16 | 60* | `[((k3-k4)-k5)^k1^7F, (((k1+k2)-k3)-k4)^F3, (k4+BC)^(2k2+k1), 2k4+k5+k1+7F]` | Crown V16.10 |

blkVCodes confirmed in the DOS binaries by the 4×`movb` init (`p2-blkvcode.py`); Crown from
`ReadKeyData`/`USBReadKeyData`; Crown laserMath from `merit_encrypt@0x0828bee0`, verified by decrypting
`MCROWN_full_FF004000036F1F82` to the known plaintext `Crown USA-STD/key` with **0 differing bytes**.
(*scratch count 60 not yet proven — the known plaintext scratch is all zero.)

**Linux transport detail:** on USB I/O-board machines the host computes the DS1991 passwords, the
board's EZ-USB firmware reads the subkeys and returns them XOR-masked with a 4-byte "decrypt value"
(`USBIO::GetDecryptVal`, firmware RAM 0x1C34); the host unmasks, then runs the normal cipher. Nicholas'
keyless patch replays these USB transfers, which is why it never needed the cipher.

## Passwords (the real version discriminator)

Each version family has its own 3×8-byte password init constants, combined with laserMath
(keyflasher `*PasswordGenerator`). Pairs that share cipher+signature (XL Gold/2K, Platinum/Diamond,
Titanium/Emerald) still have **different** passwords, so their keys are not interchangeable unless the
software carries both password sets (see `Docs/02`). M1-era keys use one fixed password
`CC E3 AA F0 0F 3C AE CE` on all subkeys (also hard-coded in MAXX 3.06 at `0xC0814`).
Merit used x86 instruction bytes as some constants (Diamond `83 F8 01 76 22 56 8B F0` = `cmp eax,1; jbe …`).

## Three layout generations (plaintext)

Offsets are into each subkey's 48-byte DATA (D0/D1/D2) or the 64-byte scratch (SC).

### IDs (all generations)
- ID0 = part number `SA` + 4 digits + 2-digit territory (`SA304201`).
- ID1 = programming date `MM/DD/YY`. ID2 = revision `R00`/`R01` (space- or NUL-padded).

### Gen 0/1 — XL R1 → MAXX Double Diamond (signature in D0[0..7])
| Field | Where | Notes |
|---|---|---|
| signature | D0[0..7] | `11223344 55667788` (XL R1), `QRSTUfw\x88` (Super 5000), `PRSTUfw\x89` (XL 6000 → Double Diamond) |
| coin channels | D0[8..0x17] | 4 × 4 bytes (`01 01 01 00`; Portugal `05 02 0A 00 / 01 01 05 00 …`). SA301901 keys get these forced to 1 in Diamond (`0x2abc8`) |
| region/lang dword | D0[0x28..0x2B] | byte-swapped on load (`0x2aa24`): `0011007F` USA, `0020006F` S.Europe/Portugal, `0030008F` Canada, `0001007F` M1 |
| per-game nibbles | D1[0..0x1F] | **the game table**: one nibble per game id 0x00–0x3F, 0 = not on the key; Diamond/Platinum/2K/3.06 value = price per play, Emerald/Titanium a class code (*corrected P21*, `Docs/21` C2) |
| D1[0x20..0x27] | e.g. `062B1231 292023xx` | open |
| option table | D2[0..0x13] | ~~2 bits per game~~ **the same 80 × 2-bit option table as Gen 3** (*corrected P21*: matches every DOS NVRAM's operator-option bytes, `Docs/21` C1), MSB-first (`0x2ab0c`); Diamond force-clears slots 0x28, 0x2D, 0x2F in code |
| territory name | D2[0x18..0x21] | `USA-STD`, `CAN-VER2`, `PORTUGAL`, `S EUROPE`, `USA-VER1/2`; `NJ…` triggers the New-Jersey path |
| currency names | SC[8·i] | e.g. `DM1`,`DM2`,`DM5` on S EUROPE key |

### Gen 2 — Titanium, Emerald, Ruby (signature still D0[0..7])
Same map as Gen 1 except: signature `e8420886 67400282` (Titanium) or `dd621043 21100293`
(Emerald) / `de621043 21100293` (Ruby); D1 holds per-game price nibbles (`2222…`) on Ti/Emerald and a
game-ID list on Ruby; Ruby scratch carries extra data (and a trailing 16-byte block).

### Gen 3 — Sapphire, Jade, Crown (signature moved to D0[0x28..0x2F])
Field map from Crown `KeyMgr` (Jade identical). *P21:* Sapphire (and Force 2004) differ — options at
D2[0x16..0x2B] (88 slots), price list D1[0..0x11], game bitmap D1[0x12..], default price D2[2],
territory D2[4]; Ruby 2 / Force 2003 keep games as a D1 `(id, price)` list (`Docs/21` C3, C4):

| Field | Where | Source |
|---|---|---|
| TournaMAXX game cost (5 b), prize mode (2 b), prize rate (5 b) | D0[1] bits0-4 / bits5-6, rate = (D0[2]&0xF)·2 \| D0[1]>>7 | `GetTournGameCost/PrizeMode/PrizeRate` |
| default language mask | D0[3..6] (LE dword) | `GetDefaultLangMask` |
| coin channels ×6 | D0[7+4i], D0[8+4i], D0[9+4i] | `SetupCoinDefaultsFromKey`, `GetChannelDefaults` |
| lockout value | D0[0x27] | `GetLockoutValue` |
| signature | D0[0x28..0x2F] | `8723879f e2432498` Jade/Crown, `12345678 90abcdef` Sapphire |
| enabled game-ID list | D1[0..], `FF`-terminated | menu build |
| territory name | D1[0x20..0x29] | `IsNJKey` (`'N','J'`), boot banner "Desc" |
| country code | D1[0x2E] | `GetCountryCode`; 0 = USA (`IsUSAKey`), 1 = Canada (CAN keys), 3/4 = UK-style game renames ("Crazy-Golf", "Race Cards", "21 Pontoon") |
| **options ×80** | D2[0..0x13], 2 bits each MSB-first | `ExplodeOptions`; `IsOptionSelectable` ⇔ state ∈ {2,3} |
| platform flag | D2[0x1C] bit 3 | must match the cabinet/platform check or the signature fails (`FUN_0823ff40`) |
| currency names ×6 | SC[8i..8i+7], value = atoi(name+5) | `GetCurrencyType`, `SetupCoinDefaultsFromKey` |

Open: meaning of each of the 80 option indices (TournaMAXX enable is one of them) and the 2-bit
state semantics beyond "2/3 = selectable" → `Docs/04`.

## Notes on the dump sets
- `Key Info & Dumps/New Keys` is a strict superset of `Keys` (+ `MCROWN_full_6D…`, `SA002001_*`).
- `F:/TouchPPBox Folder/keys` adds `M2K_full_DD…`, `MJADE_full_64…` (SA307933, subkey 2 unreadable),
  `MCROWN_full_FF004000036F1F82`, `MRUBY_full_1122334455667788` (synthetic serial), and hand-made
  plaintext `*_multikey_*` files (XL R1/5000/Gold CD) from the earlier emulator project — those are
  crafted, not dumps.
- The two copies of `MCROWN_full_6D000000CB053702` differ only in scratch (one carries Canadian coin
  names `$10/$11/$14`, `59¢`).
