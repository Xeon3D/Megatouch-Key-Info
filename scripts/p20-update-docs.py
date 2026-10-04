"""p20-update-docs.py - fold the Force/ION + Gen 4 findings (P18-P20) into the two
handover documents at the workspace root. Every edit is an exact-string replacement that
must apply, so a silent no-op is impossible.

    python scripts/p20-update-docs.py            # apply
    python scripts/p20-update-docs.py --check    # report which edits are still pending

Canonical detail stays in Docs/18 and Docs/19; these two files are the condensed handover
(keyinfo.md, technical) and the readable guide (keyinfo-human.md).
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EDITS = {}


def edit(fname, old, new):
    EDITS.setdefault(fname, []).append((old, new))


# ---------------------------------------------------------------- keyinfo.md

edit('keyinfo.md',
     """A self-contained technical handover for another instance. It covers the physical key, the crypto, how a
software version decides to accept a key, what the key controls (territory, games, prices, 80 option
locks), the laser-serial windows, the NVRAM that mirrors the key, and the tooling in this workspace.""",
     """A self-contained technical handover for another instance. It covers the physical key, the crypto, how a
software version decides to accept a key, what the key controls (territory, games, prices, the option
locks), the laser-serial windows, the NVRAM that mirrors the key, and the tooling in this workspace.
It spans **every release from XL R1 (1997) to ION 2014**, i.e. the Maxx/XL line *and* the Force / ION
line, including the Gen 4 keys (DS1995/DS1996) that replaced the DS1991 MultiKey in 2007.""")

edit('keyinfo.md',
     """Canonical per-topic detail lives in `Docs/01`–`Docs/08`.""",
     """Canonical per-topic detail lives in `Docs/01`–`Docs/08` (Maxx/XL), `Docs/18` (Force/ION containers,
ciphers, passwords, signatures) and `Docs/19` (the Gen 4 field map, all 120 option names, game ids).""")

edit('keyinfo.md',
     """  - **Linux line** Ruby 2 (V11) → Crown (V16.10, 2005): i386 ELF `start.elf` (game; `start` is a packed
    launcher, ignore it) + `opsetup.so` (operator setup), g++ 2.9x with **dynamic C++ symbols** (names
    like `KeyMgr::ExplodeOptions` survive).""",
     """  - **Linux line** Ruby 2 (V11) → Crown (V16.10, 2005): i386 ELF `start.elf` (game; `start` is a packed
    launcher, ignore it) + `opsetup.so` (operator setup), g++ 2.9x with **dynamic C++ symbols** (names
    like `KeyMgr::ExplodeOptions` survive).
  - **Force / ION line** Force 2002 (DOS!) → Force 2011 and ION 2006 → ION 2014, plus Touch2Play 2013
    and Firefly 2010 on the same code base. Force 2003 onward are Linux `start` builds; from Force 2007
    the binaries are **not** packed and carry 12 000–17 000 dynamic C++ symbols plus generated
    enum tables in `libenums.so`. The class is `KeyManager` (the later name for `KeyMgr`).
  - **One binary serves several products** — Maxx Ruby 2 V11.00 and Force 2003.5 share a `start` md5,
    as do Jade 2 V15.10 and Force 2005.5. The *key* selects the product, not the binary.""")

edit('keyinfo.md',
     """| Key dumps | `Key Info & Dumps/New Keys` (superset of `Keys`); more in `F:/TouchPPBox Folder/keys` |""",
     """| Key dumps | `Key Info & Dumps/New Keys` (superset of `Keys`); more in `F:/TouchPPBox Folder/keys` |
| Force / ION dumps | `Key Info & Dumps/Force - ION/` (Nicholas keys F2002–F2011 + I2006–I2014, Force 2011 block, ION 2014 USB capture) |
| Force/ION/T2P/Firefly disk images | `H:/Megatouch/Hard Disk Images/<product>/*.img` (use the extracted `.img`, never the archives) |
| Gen 4 binaries + XML configs | `analysis/p19/bin/<tag>/`, `analysis/p19/xml/<tag>/` (extracted read-only) |
| **The key editor** | `scripts/mtkeytool.py` (GUI) on `scripts/mtkeylib.py`; standalone copy in `Run/` |""")

edit('keyinfo.md',
     """## 1. The physical key

- **DS1991 MultiKey** (1-Wire family `0x02`) for XL R1 → Ruby. Ruby 2 → Crown keys are seen on family
  **`0x82`** buttons (DS1425, same command set). Jade, Jade 2 and Crown **require** 0x82 (§7). [verified]""",
     """## 1. The physical key

Two completely different containers across the range:

| Container | Family | Size | Payload | Protection | Used by |
|---|---|---|---|---|---|
| DS1991 MultiKey / DS1425 | `0x02`, `0x82` | 256 B | 3 × [ID 8][PW 8][DATA 48] + 64 B scratch | 3 passwords **and** a byte cipher | XL R1 → Crown, Force 2002–2006, ION 2006 |
| **DS1995** | `0x0A` | 2 KB | one 1024-byte block | **cipher only, no passwords** | ION 2007 |
| **DS1996** | `0x0C` / `0x8C` | 8 KB | one 1024-byte block at a per-version offset | **cipher only, no passwords** | Force 2007–2011, ION 2008–2014, Touch2Play, Firefly |

`KeyManager::Init` branches on `USBIO::GetKeyFamilyCode()`: `0x0C`, `0x8C` or `0x0A` ⇒ the Gen 4
layout, anything else ⇒ the legacy DS1991 layout. Every Gen 4 build still reads DS1991 keys. [code]

- **DS1991 MultiKey** (1-Wire family `0x02`) for XL R1 → Ruby. Ruby 2 → Crown keys are seen on family
  **`0x82`** buttons (DS1425, same command set). Jade, Jade 2 and Crown **require** 0x82 (§7). [verified]""")

edit('keyinfo.md',
     """| **MCROWN** | **12 78 37 F3** | 0x16 | 60 (unproven) | Crown | Crown V16.10 |""",
     """| **MCROWN** | **12 78 37 F3** | 0x16 | 60 (unproven) | Crown | Crown V16.10, **Force 2006, ION 2006** |

**The Force/ION DS1991-era keys reuse the Maxx ciphers byte for byte** [verified, 7/7 dumps byte-exact
and 7/7 encrypt round-trips]: Force 2002 = XTIT/MEMERALD, Force 2003 = MRUBY, Force 2004 = MSAPPHIRE,
Force 2005 = MJADE, Force 2006 and ION 2006 = MCROWN. Only the signature and the password init
constants differ. Force 2003's passwords are *identical* to Maxx Ruby 2's, so those keys are
interchangeable at the crypto layer — consistent with the shared `start` binary.""")

edit('keyinfo.md',
     """### Passwords — the real version discriminator""",
     """### Gen 4 cipher — Force 2007–2011, ION 2007–2014 [verified, 22/22 dumps byte-exact + round-trip]

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

### Passwords — the real version discriminator""")

edit('keyinfo.md',
     """- keyflasher `*_full_` dumps store the passwords in each PW field. For the CAN-VER2 Crown dump they are
  exactly the generator's output for its own 0x02 serial.""",
     """- keyflasher `*_full_` dumps store the passwords in each PW field. For the CAN-VER2 Crown dump they are
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
`DD62108621400293`, and a fourth init table — presumably an engineering/service key. [open, low value]""")

edit('keyinfo.md',
     """## 4. Which keys a version accepts""",
     """## 3b. Gen 4 plaintext layout (Force 2007+, ION 2007+) [code, from `KeyManager` in ION 2014]

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

## 4. Which keys a version accepts""")

edit('keyinfo.md',
     """### Linux signatures [code]""",
     """### Force / ION signatures [verified, straight off the dumps]

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

### Linux signatures [code]""")

edit('keyinfo.md',
     """## 6. Territory (last two digits of the part number) [verified across dumps]""",
     """### Resolved: `…2487` is not the Force variant [verified, P18]

The earlier note that Crown's gate accepts `8723879FE2432498` **or** `8723879FE2432487`, with
`…2487` suspected to be the Force/ION value, is **wrong**. With real Force dumps in hand:

- Force 2005 carries the *same* `8723879FE2432498` as Maxx Jade — so `…2498` is not Maxx-specific.
- Force 2006 carries `8624879FE2432498` against Crown's `8723879FE2432498`: **byte 0 is −1 and byte 1
  is +1**. That is exactly the platform-check modifier ("if D2[0x1C] bit 3 disagrees with the platform
  check the expected first byte is +1"), observed from the key side for the first time.
- `…2487` (= `…2498` − 0x11) therefore belongs to the *other* modifier, the high-bit character in the
  territory name.

Platform bit D2[0x1C] bit 3 across the dumps: set on Force 2004/2005/2006 and ION 2006, clear on every
Gen 1/2 Maxx/XL key and on Maxx Crown. Two keys with the same part number SA3079 differ in it, so it is
a per-key programming choice rather than a property of the SKU. [open: why a Jade-labelled key has it]

---

## 6. Territory (last two digits of the part number) [verified across dumps]""")

edit('keyinfo.md',
     """## 8. The 80 option slots (feature locks) [code; states verified on 4 keys]""",
     """## 8. The option slots (feature locks) — **all named** [code, exact]

Gen 1/2 keys have **no** option table (that region, D2[0..0x13], is their 2-bit-per-game table).
Options start with Gen 3: **80 slots × 2 bits** at D2[0..0x13]. Gen 4 expands to **120 slots × 1 byte**
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

""")

edit('keyinfo.md',
     """## 14. Status and open items (2026-10-03)

Done and verified:""",
     """## 14. Status and open items (2026-10-03)

Done and verified:
- **the whole Force / ION line**: containers, both Gen 4 ciphers (22/22 dumps byte-exact + round-trip),
  every DS1991 password set (48/49 reproduced), signatures for every year;
- the **Gen 4 field map**, read out of `KeyManager` in the ION 2014 binary and cross-checked against
  the checksum the code itself computes;
- **all 120 option slots named**, exactly, from the generated enum tables;
- the Gen 4 game-id enum (293 of 301 for the ION line);
- a **key editor covering all 33 releases** (`scripts/mtkeytool.py`, standalone copy in `Run/`), with a
  regression suite that loads 107 dumps, round-trips every one, and generates all 33 releases;""")

edit('keyinfo.md',
     """Open:
1. Confirm the `8723879f e2432487` signature belongs to Force/ION keys (needs a Force key dump).""",
     """Open:
1. ~~Confirm the `8723879f e2432487` signature belongs to Force/ION keys.~~ **Closed** — it does not;
   the Force modifier lands on byte 0 (§5b). A **genuine ION 2014 key dump** is still wanted: the only
   sample is internally inconsistent (country code 1 with territory `USA-STD`, date decoding to 1977).""")

edit('keyinfo.md',
     """7. MegaNet server-side serial checks: out of scope.""",
     """7. MegaNet server-side serial checks: out of scope.
8. The Gen 4 serial-bound tokens at 0x012 and the three copies at 0x3F0. Across six otherwise
   byte-identical ION 2009 keys these are the *only* differing bytes, and nothing in `start` reads
   0x3F0 — likely the programmer's own anti-clone marker.
9. Labels for the 8 unpinned ION game ids and most of the Force-line ids (an extractor limitation on
   fall-through switch leaves, not an unknown in the format).
10. The Gen 4 NVRAM layout: settings moved to `/merit/settings.xml` plus SQLite and `/config/nvram.dat`
    shrank to 5 792 B, so none of the §10 NVRAM work carries over.
11. The executable self-read integrity check inside `KeyManager::Check` (surface N).""")

edit('keyinfo.md',
     """| Key crypto | `mtkey.py` (all schemes incl. MCROWN), `keyinfo.py`, `p6-craft.py`, `p17-reserial.py` (password generator + CRC8), `p1-crown-solve.py`, `p3-crown-verify.py`, `p1-verify-crypto.py` |""",
     """| Key crypto | `mtkey.py` (Gen 1–3 schemes incl. MCROWN), **`mtkey4.py`** (Gen 4 ADD/XOR ciphers + checksum), **`mtpass.py`** (every DS1991 password set), `keyinfo.py`, **`keyinfo4.py`** (Gen 4 field decode), `p6-craft.py`, `p17-reserial.py`, `p1-crown-solve.py`, `p3-crown-verify.py`, `p1-verify-crypto.py` |
| **Key editor** | **`mtkeytool.py`** (GUI), **`mtkeylib.py`** (model for all 4 generations), **`test-mtkeytool.py`** (regression suite), `data/{options,games}.json` |
| Force / ION analysis | `p18-recover.py`, `p18-xorsolve.py` (identify a key with no serial), `p19-accessors.sh` (disassemble every `KeyManager` accessor), `p19-enum2.py` / `p19-enum3.py` (lift a generated enum table out of `libenums.so`), `p19-games4.py`, `p19-grid4.py` (cross-key differential) |
| Image extraction (read-only, WSL) | `p19-probe.sh`, `p19-find.sh`, `p19-extract.sh`, `p19-libs.sh`, `p19-xml.sh`, `p19-settings.sh` |""")


SENTINEL = '<!-- p20: Force/ION + Gen 4 content merged -->'


def main():
    check = '--check' in sys.argv
    rc = 0
    for fname, edits in EDITS.items():
        path = os.path.join(ROOT, fname)
        s = open(path, encoding='utf-8').read()
        if SENTINEL in s:
            # Several edits are insertions whose anchor text survives, so re-applying would
            # duplicate them. The sentinel makes a second run a no-op.
            print('%-20s already updated (sentinel present), skipped' % fname)
            continue
        applied = pending = already = 0
        for old, new in edits:
            if old in s:
                if not check:
                    s = s.replace(old, new, 1)
                applied += 1
            elif new.split('\n')[0] in s or (new[:80] in s):
                already += 1
            else:
                pending += 1
                rc = 1
                print('  !! edit did not match in %s: %r' % (fname, old.split('\n')[0][:70]))
        if not check:
            open(path, 'w', encoding='utf-8').write(s.rstrip() + '\n\n' + SENTINEL + '\n')
        print('%-20s %d applied, %d already present, %d UNMATCHED'
              % (fname, applied, already, pending))
    return rc


if __name__ == '__main__':
    sys.exit(main())
