# 08 — NVRAM settings per version (in progress)

Evidence: `scripts/le_exports.py` (DOS export names, all 25 images → `analysis/flat/*.exports.txt`),
`scripts/p8-nvram-dos.py` (per-version address/size/base version + reference maps →
`analysis/p8/<ver>.nvmap.tsv`, `summary_dos.json`), Ghidra `scripts/ghidra/nvram_refs.py` +
`scripts/p8-aggregate.py` (Crown → `analysis/p8/crown.nvmap.tsv`, raw `crown_*.nvrefs.tsv`),
Emerald 2 GETNVRAM/PUTNVRAM/init decompiles (`analysis/p8_nvram_*.c`).

New tooling fact: every `MEGACDLL.EXE` exports 155–723 named symbols (CauseWay DLL), e.g.
`_NVRAMDATA`, `GETNVRAM_`, `PUTNVRAM_`, `_MYID`, `_PROGRAMVER`, `_LINK*SETTING`. Use the
`.exports.txt` files to label DOS functions/globals.

## Storage

| Line | Backend | Notes |
|---|---|---|
| DOS | file named by `XLNVRFILE` (path at Emerald 2 `0x18879E`) **or** the I/O board's battery-backed SRAM mapped at physical `0xC8000` (32 KB window), chosen by a hardware flag (`0x1887EE`) | `GETNVRAM_` = fopen/fread/fclose; missing file ⇒ defaults written, "NVRAM FILE MISSING" |
| Linux | `/var/config/nvram.dat`, backup `/home/maxx/var.bak/config/nvram.dat`; Jade/Crown add a `db_nvram` database (`nvram_values`, `menu_layout`, `config`) | TournaMAXX keeps its own `/var/merit/tournamaxx/ntnvram.dat` |

## Header (all versions)

| Offset | Field |
|---|---|
| 0x00 | valid flag (cleared when the checksum fails → "NVRAM version mismatch or invalid checksum, clearing NVRAM") |
| 0x01–0x08 | copy of key ID0 (part number) — mismatch ⇒ "Dallas Key mismatch, re-initing NVRAM" |
| 0x09 | **layout base version** — mismatch ⇒ "Bad NVRAM base version, exp %d, got %d" and clear |
| 0x38–0x3B (Linux) / 0x3ED (DOS Diamond) | copy of key ID2 (revision) |

## Per-version layout identity (DOS)

The base version is one counter shared by the XL and MAXX lines (one codebase). Builds with the same
base version share the NVRAM layout.

| Version | `_NVRAMDATA` | Size | Base ver. |
|---|---|---|---|
| XL R1 | 0x68CC4 | (not found; ≤ 0x8000) | — |
| XL Super 5000 R5B / R5E | 0x797FC / 0x886D0 | (≤ 0x8000) | — |
| XL 6000 R02 | 0xC5284 | 0x76F4 | 0x45 |
| XL 6000 R04 / R07 | 0xD4CE0 / 0xD4E40 | 0x77E0 | 0x49 / 0x4A |
| MAXX V3.06 | 0xD67D0 | 0x7B7B | 0x4D |
| XL Gold R00 | 0xC5364 | 0x7BC7 | 0x50 |
| MAXX 2K V4.00 / V4.01 | 0x10FA7C / 0x10FA1C | 0x7BC6 | 0x50 |
| XL Gold R01 | 0xC55A8 | 0x7BCB | 0x53 |
| MAXX 2K Plus V5.00 | 0x10D2A8 | 0x7BE3 | 0x53 |
| MAXX Diamond V6.03 / V6.20 | 0x14382C | 0x6CCF | 0x59 |
| XL Platinum V1.02 / Double Platinum V2.00 | 0xE9270 / 0xE92A8 | 0x6CE5 | 0x5A |
| MAXX Double Diamond V7.01 / V7.20 | 0x155620 | 0x73FF | 0x5D |
| MAXX Emerald V8.04/8.05/8.20, XL Titanium V3.00 | 0x1790F0… / 0xE9D24 | 0x7ECB | 0x65 |
| MAXX Emerald 2 V9.00/9.01, XL Titanium 2 V4.00 | 0x179FC0… / 0xEA324 | 0x7F07 | 0x66 |

Linux `NVRAMData` sizes: Ruby 2 60 968 B, Sapphire 97 876 B, Jade 88 264 B, Crown 89 372 B
(Crown writes base version 0x10 — the Linux line restarted the counter).

## Crown V16.10 field map (from 571 named functions; `analysis/p8/crown.nvmap.tsv`)

| Offset | Field (from the functions that use it) |
|---|---|
| 0x00–0x09 | header (above) |
| 0x0A | operator/machine mode flags (MegaWeb, dial-in, game serial entry, menu start) |
| 0x1A, 0x34 | TouchTunes machine mode / timer hour |
| 0x38–0x3B | key revision copy |
| 0x3C | six-star PIN |
| 0x40 + 8·i (i<6) | currency names (from key scratch) |
| 0x70 + 2·i | currency values |
| 0x7C / 0x82 / 0x88 + i | coin channel coins / credits / meter pulses (6 channels, from key) |
| **0x8E + slot (0x8E–0xDD)** | **operator values of the 80 key option slots** (`Docs/04`) |
| 0xE6 + 4·game | per-game status/price record (game < 0xC3) |
| 0x398 | TouchTunes credits/state |
| 0x466–0x467 | packed bits: erotic time window, high-score auto-clear week |
| 0x468 | security lock mask (`SecurityIsLocked`) ; 0x46C security PIN |
| 0x471 / 0x47C / 0x480 | theft-deterrent PIN / timer / week |
| 0x484–0x4C0, 0x82C–0x850 | local tournament settings, sequences, winners |
| 0x12EC… | high-score names/records (largest region, to ~0x12C31) |
| 0x12F0 / 0x12F4 | default language / player-selectable languages |
| 0x15280 | system volume (and board-type default) |
| 0x15360–0x15380 | currency type / credit value / game cost basis |
| 0x15384–0x15428 | credit-card / PPP dial-up settings |
| 0x15454 | lease/time-bomb state |
| 0x15465 | category layout (game slots per category) |
| 0x15628–0x15657 | six-star + ShowTenders PIN and time windows |
| 0x15668–0x15688 | MeritMoney schedule and free-game limit |
| 0x1568C–0x156AD | promo-credit PIN, schedule, idle time, free credits |
| 0x156B0–0x156E0 | pay-per-time (CCO) PIN, rates, blocks, timers |
| 0x156D4 | coin/credit mode flags (bit 0x20 = NJ rental mode) |
| 0x15714–0x1572C | current credits, MeritMoney credits |
| 0x15730–0x157E0 | cash settlement / collection: MegaNet, premium and misc fee rates and cumulative totals, operator cut, TouchTunes/TournaMAXX credits |
| 0x157E8 / 0x157F1 | location number / operator game number |
| 0x15808–0x1582C | download / module / time bookkeeping |
| 0x15848–0x15894 | downloadable-content (DDC) play counters |
| 0x158D0 / 0x158D4 + game | game availability / per-game enable (from key bitmap) |
| 0x159B4 (0x1C B) | copy of the key's game bitmap |
| 0x15D18 | timestamp of last key-driven pricing update |

## Option values and coin block per layout (P9, 2026-10-03)

The 80 key option slots are stored in every layout (one byte each, the operator's choice). The
**effective** value combines it with the key: state 0 ⇒ off, 1 ⇒ on, 2/3 ⇒ the stored byte (`IsOptionOn`).

| Layout (base version) | Options base | Coin block (coins, +6 credits, +12 pulses) | Key rev copy | Evidence |
|---|---|---|---|---|
| DOS 0x45–0x4D (XL 6000, MAXX) | **0x108** | 0x29 | ? | "deckpile" + same default byte pattern as later builds in real NVRAM |
| DOS 0x50–0x53 (XL Gold, MAXX 2K, 2K Plus) | **0x138** | 0x29 | ? | "deckpile" + same default byte pattern |
| DOS 0x59/0x5A/0x5D (Diamond, Platinum, Double Diamond) | **0x445** | 0x3F5 | ? | `NTOURNSUPPORTED_`, "deckpile", "LANG" agree |
| DOS 0x65/0x66 (Emerald, Titanium, Emerald 2, Titanium 2) | **0x3CF** | 0x38D | 0x385 | four anchors agree |
| Linux 0x0A (Ruby 2) | **0x3DA** | 0x3C8 | 0x384 | `SetOptionValue`/`IsOptionOn`, `SetupCoinDefaultsFromKey` |
| Linux 0x10 (Crown; Jade/Sapphire: see below) | **0x8E** | 0x7C, currencies 0x40 | 0x38 | Crown symbols |

Ruby 2's layout is the DOS Emerald struct with small shifts; Sapphire/Jade/Crown reorganised it.

## Real NVRAM from the rig images (P9)

`scripts/p9-extract.sh` pulls (read-only, via debugfs/mtools) `C:\NVRAM.DAT` (DOS, 32 768 B) and
`/var/config/nvram.dat` (Linux, 64/128 KB) from every image in `Rigs/05-megappbox-1.03` into
`analysis/p9/nvram/` (+ `manifest.txt` with SHA-256). `scripts/nvram.py` decodes them; `--key <dump>`
adds the key's lock states and reports stored values the key overrides. Full report:
`analysis/p9/nvram_report.txt`.

Observations:
- All DOS rigs run with `set xlsystype=maxx` in `C:\R.BAT` (MAXX cabinet mode).
- Jade V14.00 "New" and Sapphire V12.01 "Played" NVRAM files are all zeros (never initialised), which is
  why their hashes match.
- The Titanium V3.00 keyless crack leaves part number `SA305274` (fake territory 74) in NVRAM.
- The Emerald V8.05 "exefix" image last ran with the `SA002001` key.
- Crown "TournaMAXX test" NVRAM has TournaMAXX (slot 0x14) stored on while the stock USA Crown key
  locks it off; it is the only option the key overrides on that image.
- Linux base version 0x10 is shared by Sapphire 2, Jade and Crown but the struct sizes differ, so the
  base version alone does not identify a Linux layout (Sapphire 2's revision field decodes as "Z").

## Linux layout families (P10)

Shift map from offsets whose named-function sets match exactly (`analysis/p8/{jade,sapphire,ruby2}.nvmap.tsv`):

| Build | Relation to Crown | Evidence |
|---|---|---|
| Jade V14.00 (Jade 2 expected same) | identical up to 0x49B; **−8 bytes from ~0x12C4 on**; Crown appends ~1.1 KB at the end (download-content counters) | 103 offsets matched |
| Sapphire V12.01 / Sapphire 2 | different struct (Ruby-style): options 0x3DA, coins 0x3C8, revision copy 0x384; later fields scattered (+0x34C…+0x2AB4) | 34 offsets matched, no common shift |
| Ruby 2 V11.00 / V11.05 | same Ruby-style head as Sapphire; rest differs | 9 offsets matched |

So the Linux line has two families: **Ruby-style** (Ruby 2, Sapphire, Sapphire 2, base 0x0A/0x10) and **Jade-style**
(Jade, Jade 2, Crown, base 0x10). `scripts/nvram.py` picks between them by where the key-revision copy sits.

## Named settings per Linux build (P11)

`scripts/p11-fields.py` builds a per-build field dictionary (width from the decompiler casts, label from
the most specific users) → `analysis/p11/<build>.fields.json` (Ruby 2 164, Sapphire 219, Jade 270,
Jade 2 276, Crown 270 fields). `scripts/p11-semantic.py` then pins named settings by their distinctive
setter (e.g. `STM_VolumeControl::ChangeSystemVolume`) in every build → `analysis/p11/linux_fields.json`,
which `scripts/nvram.py` uses (build chosen from the part number kept in NVRAM).

| Setting | Type | Ruby 2 | Sapphire | Jade / Jade 2 | Crown |
|---|---|---|---|---|---|
| six-star PIN | u32 | 0x388 | 0x388 | 0x3C | 0x3C |
| security lock mask / PIN | u32 | 0x19A0 / 0x19A4 | 0x2F1C / 0x2F20 | 0x468 / 0x46C | 0x468 / 0x46C |
| theft-deterrent PIN / week | u32 | 0x19A9 / 0x19B8 | 0x2F25 / 0x2F34 | 0x471 / 0x480 | 0x471 / 0x480 |
| default language | u32 | 0x19C4 | 0x2F40 | 0x12E8 | 0x12F0 |
| system volume | u32 | 0xB80C | 0x1485C | 0x15278 | 0x15280 |
| currency type | u32 | 0xD4A0 | 0x16340 | 0x15358 | 0x15360 |
| value of credit | **f32** (0.25 = $0.25) | 0xD4C0 | 0x16360 | 0x15378 | 0x15380 |
| current credits | **u16** | 0x20 | 0x20 | 0x1570C | 0x15714 |
| MeritMoney start h/m, end h/m, free-game limit | u8…u32 | — | 0x17CF4… | 0x15664… | 0x1566C… |
| promo credits start/end hour, idle time, free credits | u8 | — | 0x17D18… | 0x15688… | 0x15690… |
| pay-per-time PIN | str4 | — | 0x17DDC | 0x156A8 | 0x156B0 |
| pay-per-time play / time rates | u32 | — | 0x17DF0 / 0x17DFC | 0x156BC / 0x156C8 | 0x156C4 / 0x156D0 |
| TouchTunes / TournaMAXX credits | u32 | 0xD428 / 0xD42C | 0x162C8 / 0x162CC | 0x157D4 / 0x157D8 | 0x157DC / 0x157E0 |
| location number / operator game number | str | — | — | 0x157E0 / 0x157E9 | 0x157E8 / 0x157F1 |
| last books clear date | u32 time | 0xD5F8 | 0x16498 | — | — |

Real values (sanity check): six-star PIN 4123 on new/default images (Merit's factory default), 123456 and
1234 on played ones; volume 38–86; value of credit 0.25 everywhere; Jade V14.21 keyless has 641 credits.
On Jade/Crown the "currency names" block holds display formats (`$%d`, `%d¢`).

DOS: the operator-setup code is not in MEGACDLL; it lives in SETUP.DLL (next section). *Corrected P16:*
the earlier tentative `0x26` "current credits" byte is not a credit counter; `0x27`/`0x2B` are total
credits current/lifetime (see table below).

## DOS named settings from the operator-setup DLL (P13, extended P16)

The DOS operator menus are `C:\MERIT2\EXEC\SETUP.DLL` (extracted read-only from every image →
`analysis/p13/setup/`). It imports `_NVRAMDATA` from MEGACDLL **by ordinal** (129 for Diamond onward, 135
for MAXX/2K); each import fixup's additive is the NVRAM offset, so every menu access is located exactly.
`scripts/p13-setupmap.py` labels each offset with the menu strings used next to it
(`analysis/p13/*.setup.nvmap.tsv`, 106–114 offsets per version); `scripts/p13-dossemantic.py` pins named
settings → `analysis/p13/dos_fields_by_base.json`, used by `scripts/nvram.py`.

Generated by `scripts/p13-dossemantic.py` (regenerates `dos_fields_by_base.json`). Every credit counter is
a **current/lifetime u32 pair** (label on the current value, lifetime +4); B2 coins are **6 f32 channels**
with the lifetime copy +0x18. MAXX 3.06 has no text labels (button-graphic names), so it is mapped as
"2K − 0x30" below 0xE00: options 0x108/0x138, books 0x168/0x198, PIN `secpin` 0xD33/0xD63, and the
same adult-hours bytes (22, 6) at 0xD2C/0xD5C in both played images; its tournament counters come from
code order in `fn_35438`.

| Setting | Type | MAXX 3.06 (0x4D) | 2K / 2K Plus (0x50/0x53) | Diamond (0x59) | Platinum (0x5A) | Double Diamond (0x5D) | Emerald, Titanium, + "2" (0x65/0x66) |
|---|---|---|---|---|---|---|---|
| total credits (cur / life) | u32 | 0x3C / 0x40 | 0x6C / 0x70 | 0x27 / 0x2B | 0x27 / 0x2B | 0x27 / 0x2B | 0x27 / 0x2B |
| free credits (cur / life) | u32 | 0x44 / 0x48 | 0x74 / 0x78 | 0x2F / 0x33 | 0x2F / 0x33 | 0x2F / 0x33 | 0x2F / 0x33 |
| free-play credits (cur / life) | u32 | — | — | 0x37 / 0x3B | 0x37 / 0x3B | 0x37 / 0x3B | 0x37 / 0x3B |
| B2 coins per channel (cur / life) | 6×f32 | 0xBC / 0xD4 | 0xEC / 0x104 | 0x3BD / 0x3D5 | 0x3BD / 0x3D5 | 0x3BD / 0x3D5 | 0x355 / 0x36D |
| security PIN | str4 | 0xD33 | 0xD63 | 0xF13 | — | 0x1033 | 0x116B |
| adult hours off / on | u8 | 0xD2C / 0xD2D | 0xD5C / 0xD5D | | | | |
| volume | u32 | 0x6764 | 0x6797 | 0x58B8 | 0x58CA | 0x5FDA | 0x6A50 |
| tournament play / paid without PIN / claimed prize | u16 (3.06: u32) | 0x177C/84/8C | 0x17B3/BB/C3 | 0xF56/58/5A | 0xF5A/5C/5E | 0x107A/7C/7E | 0x11B2/B4/B6 |
| TouchTunes credits | u16 | — | — | — | — | 0x73F1 | 0x7E8D |
| per-game books (base, record size) | | 0x168, 42 | 0x198, 42 | 0x4A5, 36 | 0x4A5, 36 | 0x4A5, 36 | 0x42F, 36 |

*Corrected P16:* the volume row previously listed 0x478 for Diamond/Platinum/Double Diamond (a byte
array that reads 0x01010101) and 0x16A for 2K Plus; the regenerated map gives the offsets above (real
values 40, 40, 40, 12; 2K Plus 37 at 0x6797, so 2K and 2K Plus agree).
Real values: Emerald 2 played 91 812 lifetime credits, B2 lifetime coins 1 280 / 60 573 / 29 959 on
channels 1–3; Emerald 8.05 played 71 free credits / 237 free-play credits; 2K Plus 30 185 total / 3 211
free credits.
Also located (Emerald 2 map): the six-star option at 0x3DC next to "SET 6 STAR PIN", high-score settings
0x3E9–0x401, a per-weekday block at 0x3F/0x4D/0x5B (2K: 4 × 7 u32 from 0x7C; tentative).

## DOS per-game books (P16)

The DOS game list is `C:\MERIT2\DATA\GAMEDATA.DAT`, the same format as Linux `gamedata.dat` (game ID =
record order); `scripts/p16-dosgamedata.sh` extracts it read-only from every rig image (`analysis/p16/`)
and `scripts/p16-dosgames.py` builds `analysis/p16/dos_games_by_base.json` (51 games on MAXX 3.06, 52 on
2K, 58 on 2K Plus, 63 on Diamond/Platinum, 69 on Double Diamond, 84 on Emerald/Titanium and the "2"s).
The SETUP.DLL clear-books loops run exactly up to these counts, which ties the array index to the record
order.

Array capacity = records that fit before the next NVRAM array: 64 (0x168 + 64·42 = 0xBE8 and
0x198 + 64·42 = 0xC18, the next arrays in 3.06 and 2K; Diamond/Platinum), 72 (Double Diamond), 84
(Emerald, 0x42F → 0xFFF).

**Builds without an HDD image.** The game side (MEGACDLL) updates the same arrays: XL 6000 R02/R04/R07
use a 42-byte array at 0x168 like MAXX 3.06, and XL Gold R00/R01 one at 0x198 like 2K. The credit fields
fingerprint the same way, with identical per-offset reference counts:
- XL 6000 has 3.06's 0x3C–0x48 credits and 0xBC/0xD4 B2 coins, and no PIN or adult-hours accesses.
- XL Gold has 2K's offsets, PIN and adult hours included.

So the decoder applies those layouts to bases 0x45/0x49/0x4A and 0x50/0x53. XL 6000 has no
GAMEDATA.DAT sample, so its books print without names. XL Double Platinum V2.00 was missing from earlier
extractions: mtools rejects its FAT unless `MTOOLS_SKIP_CHECK=1` is set, which the extraction scripts now
do. Its SETUP.DLL map, game table and NVRAM match Platinum (base 0x5A).

The array was located with `scripts/p16-dosarrays.py` (every `_NVRAMDATA` access preceded by
`imul reg,reg,stride`). Record layout (from the code that clears, displays and edits it):

| Field | 36-byte record (Diamond → Emerald 2) | 42-byte record (MAXX 3.06, 2K, 2K Plus) |
|---|---|---|
| menu flags (bit 0 on menu, bit 1 available) | +0 u8 | +0 u8 |
| price per play | +1 u16 bits 0–3 | +1 u32 bits 0–7 |
| current books (credits) | +1 u16 bits 4–15 (max 4095) | +1 u32 bits 8–31 |
| lifetime books | +3 u32 | +5 u32 |
| loader skips (GAMEDATA default 20) | +7 u8 | +9 u8 |
| current play time shortest / average / longest (s) | +8 u32 packed: bits 0–9 / 10–19 / 20–31 | +0xA / +0xE / +0xC u16 |
| current games by player count 1–4 | +0xE 4×u16 | +0x12 4×u16 |
| lifetime play time | +0x16 (packed as above) | +0x1A / +0x1E / +0x1C u16 |
| lifetime games by player count 1–4 | +0x1C 4×u16 | +0x22 4×u16 |

"Clearing current books" zeroes the current block (36-byte: +8 for 0xE bytes and the 12-bit counter);
"Clearing lifetime books" zeroes the lifetime block (+0x16 for 0xE bytes and the u32 at +3).
Checks on real NVRAM: shortest ≤ average ≤ longest in every played record; Jumble games carry price 2;
Bowling and the H2H games have flags 0 (not on the key). A few records hold stray values in the 3P/4P
lifetime counters. In the two affected Platinum records the pair reads 0x00507350, which looks like a
DOS flat pointer, so this is a game-side overwrite and not a layout error.
`scripts/nvram.py` prints the books with names for every DOS layout (`--games <GAMEDATA.DAT>`
overrides the list). Example, Emerald 2 played: Eleven Ball 14 353 lifetime credits, Boxxi 12 225,
Funky Monkey 5 385.

## Game table (P14)

Game IDs (used by the key's game list, price list and game bitmap, and by NVRAM per-game records) are
the record order in `/usr/local/share/merit/config/gamedata.dat` (extracted for Sapphire → Crown into
`analysis/p14/`; 146–195 games). `scripts/gamedata.py` parses it, including the flag byte (hex): H2H,
pro sports, Force/Maxx variant, Merit-thon event, Prize Zone II, card-back ads, **Force only**,
continuable. Game 0x44 is Bowling (Force only), which is the "platform bit" of the key gate (`Docs/02`).
`scripts/keyinfo.py <key> --games <gamedata.dat>` prints a key with game names, prices and option classes.

## Books outside NVRAM (P15)

Linux keeps credit books in `/var/config/amusement.db`: an **SQLite 2.1** database XOR-obfuscated with the
repeating key `FC F1 BE 53` (decoded copies in `analysis/p15/*/amusement.db.decoded`). Schema:
`amusement_creditbooks(credit_type, curr_credits, life_credits, srvr_credits)`. The Jade V14.21 played
image has rows; reading them needs a small SQLite 2 record parser (modern SQLite cannot open v2 files).

## Next steps

Done: Linux maps for all builds; layout families split; decoder for real files (header, coins, options,
named Linux settings, `--key` effective options).

Done P16: DOS per-game books with names; MAXX 3.06 settings; credit pairs and B2 lifetime coins.

1. SQLite 2 row parser for `amusement.db` (credit books per credit type).
2. XL 6000 / XL Gold: layouts inferred from MEGACDLL (above), unverified on a real NVRAM; XL 6000 game
   names need its GAMEDATA.DAT. XL R1 / Super 5000 not mapped. All need an HDD image.
3. Name the DOS option slots per layout (the decoder currently borrows the Crown slot names, which do
   not apply to DOS).
