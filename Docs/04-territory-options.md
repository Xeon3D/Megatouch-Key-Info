# 04 — Territory, pricing and option locks (partial)

> **Superseded in part by `Docs/19` (P19).** All 120 option slots are now named exactly, lifted
> from the generated enum `xml_gameoptions::enum_GameOptionIndex_tag` in `libenums.so`
> (Force/ION 2007+ builds). The table is byte-identical across ION 2011, ION 2014, Touch2Play
> 2013 and Firefly 2010, and it agrees with every slot this document pinned by hand for Crown
> (0x0D six-star, 0x11 golf-has-women, 0x14 TournaMAXX, 0x31 lease), so slots 0x00–0x4F apply
> to the Gen 3 keys documented here as well. Use `Docs/19` for slot names; this document
> remains canonical for territory, currency and the Gen 3 2-bit packing.

Evidence: `scripts/p4-territory.py`, `analysis/p4_optcalls.txt` + `analysis/p4_options_table.txt`
(`scripts/p4-optcalls.sh`), `analysis/p1/crown_keymgr.c`, `GetGamePriceFromKey` disassembly.

## Territory

The last two digits of the part number are a territory number; the key also carries the territory
**name** (and, from Sapphire on, a numeric country code). Numbering is consistent across generations:

| Suffix | Name on key | Seen on | Gen 3 country code |
|---|---|---|---|
| 01 | USA-STD (Ruby: `STD-USA`) | M1, 2K, XL Gold, Diamond, Platinum, Emerald, Titanium, Ruby, Sapphire, Jade, Crown | 0 |
| 04 | S EUROPE | MAXX 2K | — |
| 05 | PORTUGAL | MAXX 2K, Ruby 2 | — |
| 08 | (no dump) — Diamond hard-codes a data patch for `SA304208` | — | — |
| 09 | USA-VER1 | MAXX 2K | — |
| 14 | USA-VER2 | M1 | — |
| 33 | CAN-VER2 / USA-CANV2 | Diamond, Jade, Crown | 1 |
| 45 | USA-STD (!) | Sapphire SA305945 | — |

Oddities: `SA002001` (Emerald cipher, 10/01/01) is named CAN-VER2 despite suffix 01 and carries a
different signature `dd621086 21400293` that matches none of the signatures extracted so far (it is
Titanium's raw constant with only bytes 0/1/2/4/7 transformed) — likely a non-production or
other-product key; open. `SA305945` says USA-STD with suffix 45.

What the territory drives:
- `NJ…` name ⇒ New-Jersey mode (all versions: DOS `0x2adc8`, Linux `IsNJKey`; NJ rental mode is an
  NVRAM bit, `IsNJRentalMode`).
- Country code (Gen 3, D1[0x2E]): 0 = USA (`IsUSAKey`), 1 = Canada (coin-setup branch), 3/4 = UK
  family (renames "Crazy-Golf", "Race Cards", "21 Pontoon"; 3 also flips two NVRAM defaults).
- Coin channels, currency names (scratch), default language mask, lockout value — all per key, so a
  territory is really a bundle of these defaults (see `Docs/01` field maps).
- Gen 1 D0[0x28] dword differs by region (`0011007F` USA, `0020006F` Europe/Portugal, `0030008F` Canada).

## Game list & prices (Gen 3 DATA1)

`GetGamePriceFromKey(game)`: scan D1[0..0x1B]; a byte ≥ 0xF0 sets the running price to its low nibble,
any other byte is a game ID offered at the running price. Unlisted games fall back to D1[0x2A]
(D1[0x1F] for games 0x71–0x74 and 0xA3–0xA8). Example Jade USA-STD: `F2 00 0E 1A 26 34 35 45 53 75 …`
= price 2 for games 0x00, 0x0E, 0x1A, …

## Option table (Gen 3: D2[0..0x13] = 80 × 2-bit states; Gen 1/2 same place for the game table)

`IsOptionSelectable(i)` ⇔ state ∈ {2, 3}; `IsOptionOn` / `SetOptionValue` wrap it with NVRAM state.
Index → operator-menu feature (from call sites in Crown `opsetup.so`; index = last immediate pushed,
so treat single-site entries with care):

| idx | Feature | idx | Feature |
|---|---|---|---|
| 0x00 | Free game (Solitaire) | 0x22 | Fan time |
| 0x01 | Allow game continue | 0x23 | Language buttons have flags |
| 0x02 | Coin-op / rental mode | 0x24 | (bookkeeping; next to `NTournSupported`/`AnyTournaChamp` — TournaMAXX candidate) |
| 0x03 | Licensed content support | 0x26 | Face-up cards (Tri-Towers) |
| 0x04 | Bonus replay | 0x27 | Strip-club rewinds |
| 0x05 | Price display / N games per $ | 0x28 | Erotic / kids category |
| 0x07 | Split-column (Power Sol.) | 0x29 | Free play / rental |
| 0x08 | Game category defaults | 0x2A | Easy mode |
| 0x09 | Show correct answer | 0x2B/0x2C | Power Trivia rules |
| 0x0A | Trivia round bonus | 0x2D | My Merit |
| 0x0D | Six Stars | 0x2E | Continue bonus round |
| 0x0E | Free game (Power Sol.) | 0x30 | Theft deterrent |
| 0x12 | Photo Hunt hints | 0x33 | Promo credits |
| 0x13 | Merit Money | 0x34 | Linked games |
| 0x14 | MegaNet / tournaments (coin-setup + MegaNet menus) | 0x35 | No names in high scores |
| 0x15 | Music timer | 0x36 | MegaWeb filter |
| 0x16 | Player-selectable language | 0x37 | Hi-res / TournaMAXX main menu (`TTM_Main`) |
| 0x17 | Auto-clear high scores | 0x38 | MegaWeb |
| 0x19 | Moan sounds | 0x39 | Prize Zone |
| 0x1E | Nudity | 0x3A | Premium erotic |
| 0x20 | Show deck cards | 0x3B | E-Channel |
| 0x21 | Checkerz rules | 0x3C | Educational attract |
|  |  | 0x3D | Price display / free play / promo |
|  |  | 0x3E | Hot Topics |
|  |  | 0x3F | (coin setup / NJ rental) |
|  |  | 0x40 | Premium-erotic ad screen |
|  |  | 0x41 | Attract-mode sounds |
|  |  | 0x42 | Operator Web |
|  |  | 0x44 | ShowTenders mode |
|  |  | 0x45 | Fantasy Sports |
|  |  | 0x46 | Card-back ad support |
|  |  | 0x4B | Force slow senior game play |

### State semantics (confirmed P7: `IsOptionOn`, `SetOptionValue`, `FUN_082419f0`)
bit 1 = operator may change it, bit 0 = value / default.

| State | Meaning |
|---|---|
| 0 | locked **off** (option hidden/unavailable) |
| 1 | locked **on** |
| 2 | operator-selectable, default off |
| 3 | operator-selectable, default on |

The operator's current choice lives in NVRAM `[0x8E + idx]`.

### Corrections / confirmations (P7)
- **0x14 = TournaMAXX** (network tournaments). `NTournSupported` tests NVRAM `[0xA2]` = `0x8E+0x14`
  first; `MegaNetOptionsAvalible` falls back to it; coin setup gates tournament buttons on it.
  Jade keys `0900…`/`4700…` have it **1 (forced on)**; both Crown keys have it **0 (locked off)**,
  which is exactly "TournaMAXX had to be enabled in the Crown key".
- ~~0x37 TournaMAXX candidate~~ reclassified P7: `TTM_*` is the **TouchTunes** jukebox menu
  (`TTM_TTunesSetup`, `TTM_SetTimer`, `TTM_ViewErrorLog`); 0x37 = TouchTunes integration / hi-res
  (needed for TouchTunes remote setup). It also requires the platform check.
- 0x24 = tournament/Merit-thon bookkeeping view (shown if `NTournSupported(0xE)`, `AnyTournaChamp()` or
  option 0x24); NVRAM `[0xB2]` (= `0x8E+0x24`) drives the "meritthon" `tri*.dat` setup in `InitVars`.
- Crown keys also lock off every MegaNet service (0x38 MegaWeb, 0x39 Prize Zone, 0x3A premium
  erotic, 0x3B E-Channel, 0x3E Hot Topics, 0x42 Operator Web, 0x44 ShowTenders, 0x45 Fantasy Sports)
  that the Jade keys offer. Full per-key dump: `analysis/p7/option_states.txt`.

### D2[0x14..0x2F] = per-game enable bitmap (Gen 3)
`SetGamePriceAndStatusFromKey(game)`: enabled ⇔ bit `0x80 >> (game & 7)` of `D2[0x14 + game/8]`
(28 bytes → game IDs 0x00–0xDF). Games flagged Force-only are additionally disabled unless
`ForceChk1()`. `FUN_0823ef60` force-sets a few of these bits in two special NVRAM modes; `FudgeOnGames`
does the same for others. The "platform bit" D2[0x1C] bit 3 used by the gate falls inside this
bitmap (game ID 0x44).

## Complete option-slot table (P8, 2026-10-03)

Names from operator-menu toggles (`opsetup.so`) cross-checked with the `start.elf`/`opsetup.so` functions that read NVRAM `0x8E+slot`
(`analysis/p8/option_slots_crown.tsv`). "(no reader found in Crown)" = the slot exists on keys but Crown code never reads it. States: Jade `0900…`, Jade `4700…`, Crown USA `FF00…`, Crown CAN `6D00…`.

| Slot | Feature | J0900 | J4700 | Cr USA | Cr CAN |
|---|---|---|---|---|---|
| 0x00 | Free game (Power Solitaire family) | 3 | 3 | 3 | 3 |
| 0x01 | Allow game continue | 3 | 3 | 3 | 3 |
| 0x02 | Coin-op / rental mode | 2 | 2 | 2 | 2 |
| 0x03 | Licensed content support | 3 | 3 | 3 | 3 |
| 0x04 | Bonus replay | 3 | 3 | 3 | 3 |
| 0x05 | Pricing display / games-per-$ (prize-bucks table, MegaWeb rate) | 2 | 2 | 2 | 3 |
| 0x06 | (no reader found in Crown) | 0 | 0 | 0 | 0 |
| 0x07 | Split-column (Power Sol.) | 3 | 3 | 3 | 3 |
| 0x08 | Erotic/kids category defaults | 2 | 2 | 2 | 2 |
| 0x09 | Trivia: show correct answer | 3 | 3 | 3 | 3 |
| 0x0A | Trivia round bonus | 3 | 3 | 3 | 3 |
| 0x0B | Free-play companion: idle adverts/attract (used with 0x29) | 1 | 1 | 1 | 1 |
| 0x0C | Local tournament in progress / tournament mode | 3 | 3 | 3 | 3 |
| 0x0D | Six Stars (operator shortcut) | 2 | 2 | 2 | 2 |
| 0x0E | Free game (Power Sol. 2) | 3 | 3 | 3 | 3 |
| 0x0F | Pay-per-time (CCO) | 1 | 1 | 1 | 1 |
| 0x10 | (no reader found in Crown) | 3 | 3 | 3 | 3 |
| 0x11 | Golf has women (Ruby 2) | 1 | 1 | 1 | 1 |
| 0x12 | Photo Hunt hints | 3 | 3 | 3 | 3 |
| 0x13 | Merit Money | 3 | 3 | 3 | 3 |
| 0x14 | TournaMAXX (network tournaments) | 1 | 1 | 0 | 0 |
| 0x15 | TouchTunes music timer from six stars | 3 | 3 | 3 | 3 |
| 0x16 | Player-selectable language | 2 | 2 | 2 | 2 |
| 0x17 | Auto-clear high scores | 2 | 2 | 2 | 2 |
| 0x18 | (no reader found in Crown) | 1 | 1 | 1 | 1 |
| 0x19 | Moan sounds | 3 | 3 | 3 | 3 |
| 0x1A | Six-star access: high scores (Ruby 2/Sapphire); TournaMAXX-server-set from Jade on | 3 | 3 | 3 | 3 |
| 0x1B | Six-star access: bookkeeping (VBB) (Ruby 2/Sapphire) | 3 | 3 | 3 | 3 |
| 0x1C | Six-star access: volume control (Ruby 2/Sapphire) | 3 | 3 | 3 | 3 |
| 0x1D | (read in GetNVRAM only) | 0 | 0 | 0 | 0 |
| 0x1E | Nudity allowed | 3 | 3 | 3 | 3 |
| 0x1F | Nudity level | 3 | 3 | 3 | 3 |
| 0x20 | Show deck cards | 2 | 2 | 2 | 2 |
| 0x21 | Checkerz rules | 0 | 0 | 0 | 2 |
| 0x22 | Fan time | 3 | 3 | 3 | 3 |
| 0x23 | Language buttons show flags | 2 | 2 | 2 | 2 |
| 0x24 | Merit-thon / tournament bookkeeping | 0 | 0 | 0 | 0 |
| 0x25 | Six-star access: touch calibration (Ruby 2/Sapphire) | 3 | 3 | 3 | 3 |
| 0x26 | Tri-Towers face-up cards | 3 | 3 | 3 | 3 |
| 0x27 | Strip-club rewinds | 3 | 3 | 3 | 3 |
| 0x28 | Erotic games | 2 | 2 | 2 | 2 |
| 0x29 | Free play | 2 | 2 | 2 | 2 |
| 0x2A | Easy mode | 2 | 2 | 2 | 2 |
| 0x2B | Power Trivia same category | 2 | 2 | 2 | 2 |
| 0x2C | Power Trivia question mode | 3 | 3 | 3 | 3 |
| 0x2D | My Merit | 3 | 0 | 0 | 0 |
| 0x2E | Continue bonus round | 2 | 2 | 2 | 2 |
| 0x2F | Special screen/demo mode (forces game bits; alternate main-screen build) | 0 | 0 | 0 | 0 |
| 0x30 | Theft deterrent | 2 | 2 | 2 | 2 |
| 0x31 | Lease mode (TimeBomb) | 0 | 0 | 0 | 0 |
| 0x32 | Six-star access: TournaMAXX update (Ruby 2/Sapphire) | 3 | 3 | 0 | 0 |
| 0x33 | Promo credits | 3 | 3 | 3 | 3 |
| 0x34 | Linked games (Mega-Link) | 3 | 3 | 3 | 3 |
| 0x35 | No names in high scores | 2 | 2 | 2 | 2 |
| 0x36 | MegaWeb filter | 1 | 1 | 1 | 1 |
| 0x37 | TouchTunes / hi-res video | 2 | 0 | 0 | 0 |
| 0x38 | MegaWeb | 2 | 0 | 0 | 0 |
| 0x39 | Prize Zone | 3 | 3 | 0 | 0 |
| 0x3A | Premium erotic | 2 | 2 | 0 | 0 |
| 0x3B | E-Channel | 3 | 3 | 0 | 0 |
| 0x3C | Educational attract | 3 | 3 | 3 | 3 |
| 0x3D | Price display / free-play pricing | 2 | 0 | 0 | 0 |
| 0x3E | Hot Topics / downloadable content | 3 | 3 | 0 | 0 |
| 0x3F | (coin setup, NJ rental related) | 1 | 1 | 1 | 1 |
| 0x40 | Premium-erotic ad screen | 3 | 3 | 0 | 0 |
| 0x41 | Attract-mode sounds | 3 | 3 | 3 | 3 |
| 0x42 | Operator Web | 2 | 0 | 0 | 0 |
| 0x43 | Scrolling marquee text | 0 | 0 | 0 | 0 |
| 0x44 | ShowTenders | 3 | 3 | 0 | 0 |
| 0x45 | Fantasy Sports (CDM) | 3 | 3 | 0 | 0 |
| 0x46 | Card-back advertising | 3 | 3 | 3 | 3 |
| 0x47 | Hide TournaMAXX ranking/events screens | 0 | 0 | 0 | 0 |
| 0x48 | (no reader found in Crown) | 1 | 1 | 1 | 1 |
| 0x49 | (no reader found in Crown) | 3 | 3 | 3 | 3 |
| 0x4A | (no reader found in Crown) | 2 | 2 | 2 | 2 |
| 0x4B | Force slow senior game play | 0 | 0 | 0 | 0 |
| 0x4C | (no reader found in Crown) | 1 | 1 | 1 | 1 |
| 0x4D | (no reader found in Crown) | 3 | 3 | 3 | 3 |
| 0x4E | (no reader found in Crown) | 2 | 2 | 2 | 2 |
| 0x4F | (no reader found in Crown) | 3 | 3 | 3 | 3 |

## Operator settings vs key-only switches (P10, 2026-10-03)

Method: every call to the option API in Crown `opsetup.so` with its slot argument resolved (`scripts/p10-slotcalls.py`,
`analysis/p10/slotcalls.tsv`), plus direct NVRAM `0x8E+slot` reads/writes in `start.elf`/`opsetup.so` (`analysis/p10/slot_classes.tsv`).
A slot is an **operator setting** if an operator-menu handler writes it (`SetOptionValue` or a `Set…`/`Toggle…` writer). It is a
**key feature switch** if no menu writes it: the operator menus only read it to show or hide screens, or only the game reads it.
Its value then comes from the key alone (state 0 = off, 1 = on). States below are Jade 0900 / Jade 4700 / Crown USA / Crown CAN.

### Key feature switch (10)

| Slot | Feature | Key states |
|---|---|---|
| 0x0B | Free-play companion: idle adverts/attract (used with 0x29) | 1/1/1/1 |
| 0x0F | Pay-per-time (CCO) | 1/1/1/1 |
| 0x14 | TournaMAXX (network tournaments) | 1/1/0/0 |
| 0x1D | (read in GetNVRAM only) | 0/0/0/0 |
| 0x24 | Merit-thon / tournament bookkeeping | 0/0/0/0 |
| 0x2F | Special screen/demo mode (forces game bits; alternate main-screen build) | 0/0/0/0 |
| 0x31 | Lease mode (TimeBomb) | 0/0/0/0 |
| 0x3F | (coin setup, NJ rental related) | 1/1/1/1 |
| 0x43 | Scrolling marquee text | 0/0/0/0 |
| 0x47 | Hide TournaMAXX ranking/events screens | 0/0/0/0 |

### Runtime state (1)

| Slot | Feature | Key states |
|---|---|---|
| 0x0C | Local tournament in progress / tournament mode | 3/3/3/3 |

### Remote (MegaNet server) (1)

| Slot | Feature | Key states |
|---|---|---|
| 0x1A | Six-star access: high scores (Ruby 2/Sapphire); TournaMAXX-server-set from Jade on | 3/3/3/3 |

### Operator setting (53)

| Slot | Feature | Key states |
|---|---|---|
| 0x00 | Free game (Power Solitaire family) | 3/3/3/3 |
| 0x01 | Allow game continue | 3/3/3/3 |
| 0x02 | Coin-op / rental mode | 2/2/2/2 |
| 0x03 | Licensed content support | 3/3/3/3 |
| 0x04 | Bonus replay | 3/3/3/3 |
| 0x05 | Pricing display / games-per-$ (prize-bucks table, MegaWeb rate) | 2/2/2/3 |
| 0x07 | Split-column (Power Sol.) | 3/3/3/3 |
| 0x08 | Erotic/kids category defaults | 2/2/2/2 |
| 0x09 | Trivia: show correct answer | 3/3/3/3 |
| 0x0A | Trivia round bonus | 3/3/3/3 |
| 0x0D | Six Stars (operator shortcut) | 2/2/2/2 |
| 0x0E | Free game (Power Sol. 2) | 3/3/3/3 |
| 0x12 | Photo Hunt hints | 3/3/3/3 |
| 0x13 | Merit Money | 3/3/3/3 |
| 0x15 | TouchTunes music timer from six stars | 3/3/3/3 |
| 0x16 | Player-selectable language | 2/2/2/2 |
| 0x17 | Auto-clear high scores | 2/2/2/2 |
| 0x19 | Moan sounds | 3/3/3/3 |
| 0x1E | Nudity allowed | 3/3/3/3 |
| 0x1F | Nudity level | 3/3/3/3 |
| 0x20 | Show deck cards | 2/2/2/2 |
| 0x21 | Checkerz rules | 0/0/0/2 |
| 0x22 | Fan time | 3/3/3/3 |
| 0x23 | Language buttons show flags | 2/2/2/2 |
| 0x26 | Tri-Towers face-up cards | 3/3/3/3 |
| 0x27 | Strip-club rewinds | 3/3/3/3 |
| 0x28 | Erotic games | 2/2/2/2 |
| 0x29 | Free play | 2/2/2/2 |
| 0x2A | Easy mode | 2/2/2/2 |
| 0x2B | Power Trivia same category | 2/2/2/2 |
| 0x2C | Power Trivia question mode | 3/3/3/3 |
| 0x2D | My Merit | 3/0/0/0 |
| 0x2E | Continue bonus round | 2/2/2/2 |
| 0x30 | Theft deterrent | 2/2/2/2 |
| 0x33 | Promo credits | 3/3/3/3 |
| 0x34 | Linked games (Mega-Link) | 3/3/3/3 |
| 0x35 | No names in high scores | 2/2/2/2 |
| 0x36 | MegaWeb filter | 1/1/1/1 |
| 0x37 | TouchTunes / hi-res video | 2/0/0/0 |
| 0x38 | MegaWeb | 2/0/0/0 |
| 0x39 | Prize Zone | 3/3/0/0 |
| 0x3A | Premium erotic | 2/2/0/0 |
| 0x3B | E-Channel | 3/3/0/0 |
| 0x3C | Educational attract | 3/3/3/3 |
| 0x3D | Price display / free-play pricing | 2/0/0/0 |
| 0x3E | Hot Topics / downloadable content | 3/3/0/0 |
| 0x40 | Premium-erotic ad screen | 3/3/0/0 |
| 0x41 | Attract-mode sounds | 3/3/3/3 |
| 0x42 | Operator Web | 2/0/0/0 |
| 0x44 | ShowTenders | 3/3/0/0 |
| 0x45 | Fantasy Sports (CDM) | 3/3/0/0 |
| 0x46 | Card-back advertising | 3/3/3/3 |
| 0x4B | Force slow senior game play | 0/0/0/0 |

### Not used by Crown (15)

| Slot | Feature | Key states |
|---|---|---|
| 0x06 | (no reader found in Crown) | 0/0/0/0 |
| 0x10 | (no reader found in Crown) | 3/3/3/3 |
| 0x11 | Golf has women (Ruby 2) | 1/1/1/1 |
| 0x18 | (no reader found in Crown) | 1/1/1/1 |
| 0x1B | Six-star access: bookkeeping (VBB) (Ruby 2/Sapphire) | 3/3/3/3 |
| 0x1C | Six-star access: volume control (Ruby 2/Sapphire) | 3/3/3/3 |
| 0x25 | Six-star access: touch calibration (Ruby 2/Sapphire) | 3/3/3/3 |
| 0x32 | Six-star access: TournaMAXX update (Ruby 2/Sapphire) | 3/3/0/0 |
| 0x48 | (no reader found in Crown) | 1/1/1/1 |
| 0x49 | (no reader found in Crown) | 3/3/3/3 |
| 0x4A | (no reader found in Crown) | 2/2/2/2 |
| 0x4C | (no reader found in Crown) | 1/1/1/1 |
| 0x4D | (no reader found in Crown) | 3/3/3/3 |
| 0x4E | (no reader found in Crown) | 2/2/2/2 |
| 0x4F | (no reader found in Crown) | 3/3/3/3 |

Operator settings can still be locked by the key: e.g. 0x36 MegaWeb filter is locked on (1) on all four keys,
0x4B senior game play is locked off (0), and the Crown keys lock off every MegaNet service (0x38, 0x39, 0x3A, 0x3B, 0x3E,
0x40, 0x42, 0x44, 0x45) that the Jade keys leave selectable.

## Slot classes in every Linux build (P12, 2026-10-03)

Same method as above, run on each build (`scripts/p12-slotclass.py`, `analysis/p12/slot_classes_all.txt`). op = operator setting,
**key** = key-only switch, run = runtime state, remote = set only by the MegaNet server, · = not used by that build.
Slots that Crown never reads but older builds use are named here from the Ruby 2/Sapphire menu handlers.

| Slot | Feature | Ruby 2 | Sapph | Sapph 2 | Jade | Jade 14.21 | Jade 2 | Crown |
|---|---|---|---|---|---|---|---|---|
| 0x00 | Free game (Solitaire) | op | op | op | op | op | op | op |
| 0x01 | Allow game continue | op | op | op | op | op | op | op |
| 0x02 | Coin-op / rental mode | · | · | **key** | op | op | op | op |
| 0x03 | Licensed content support | op | op | op | op | op | op | op |
| 0x04 | Bonus replay | op | op | op | op | op | op | op |
| 0x05 | Price display / N games per $ | op | op | op | op | op | op | op |
| 0x06 | (no reader found in Crown) | · | · | **key** | · | · | · | · |
| 0x07 | Split-column (Power Sol.) | op | op | op | op | op | op | op |
| 0x08 | Game category defaults | op | op | op | op | op | op | op |
| 0x09 | Show correct answer | op | op | op | op | op | op | op |
| 0x0A | Trivia round bonus | op | op | op | op | op | op | op |
| 0x0B | Free-play companion: idle adverts/attract (used with 0x29) | **key** | **key** | **key** | **key** | **key** | **key** | **key** |
| 0x0C | Local tournament in progress / tournament mode | **key** | run | run | run | run | run | run |
| 0x0D | Six Stars | op | op | op | op | op | op | op |
| 0x0E | Free game (Power Sol.) | op | op | op | op | op | op | op |
| 0x0F | Pay-per-time (CCO) | · | · | · | **key** | **key** | **key** | **key** |
| 0x10 | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x11 | Golf has women (Ruby 2) | op | · | · | · | · | · | · |
| 0x12 | Photo Hunt hints | op | op | op | op | op | op | op |
| 0x13 | Merit Money | · | op | op | op | op | op | op |
| 0x14 | MegaNet / tournaments (coin-setup + MegaNet menus) | **key** | **key** | **key** | **key** | **key** | **key** | **key** |
| 0x15 | Music timer | op | op | op | op | op | op | op |
| 0x16 | Player-selectable language | op | op | op | op | op | op | op |
| 0x17 | Auto-clear high scores | op | op | op | op | op | op | op |
| 0x18 | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x19 | Moan sounds | op | op | op | op | op | op | op |
| 0x1A | Six-star access: high scores (Ruby 2/Sapphire); TournaMAXX-server-set from Jade on | op | op | op | remote | remote | remote | remote |
| 0x1B | Six-star access: bookkeeping (VBB) (Ruby 2/Sapphire) | op | op | op | · | · | · | · |
| 0x1C | Six-star access: volume control (Ruby 2/Sapphire) | op | op | op | · | · | · | · |
| 0x1D | (read in GetNVRAM only) | **key** | **key** | **key** | **key** | **key** | **key** | **key** |
| 0x1E | Nudity | op | op | op | op | op | op | op |
| 0x1F | Nudity level | op | op | op | op | op | op | op |
| 0x20 | Show deck cards | op | op | op | op | op | op | op |
| 0x21 | Checkerz rules | op | op | op | op | op | op | op |
| 0x22 | Fan time | op | op | op | op | op | op | op |
| 0x23 | Language buttons show flags | op | op | op | op | op | op | op |
| 0x24 | Merit-thon / tournament bookkeeping | **key** | **key** | **key** | **key** | **key** | **key** | **key** |
| 0x25 | Six-star access: touch calibration (Ruby 2/Sapphire) | op | op | op | · | · | · | · |
| 0x26 | Tri-Towers face-up cards | op | op | op | op | op | op | op |
| 0x27 | Strip-club rewinds | op | op | op | op | op | op | op |
| 0x28 | Erotic games | · | op | op | op | op | op | op |
| 0x29 | Free play | op | op | op | op | op | op | op |
| 0x2A | Easy mode | op | op | op | op | op | op | op |
| 0x2B | Power Trivia same category | op | op | op | op | op | op | op |
| 0x2C | Power Trivia question mode | op | op | op | op | op | op | op |
| 0x2D | My Merit | · | op | op | op | op | op | op |
| 0x2E | Continue bonus round | op | op | op | op | op | op | op |
| 0x2F | Special screen/demo mode (forces game bits; alternate main-screen build) | · | · | · | **key** | **key** | **key** | **key** |
| 0x30 | Theft deterrent | op | op | op | op | op | op | op |
| 0x31 | Lease mode (TimeBomb) | · | · | · | **key** | **key** | **key** | **key** |
| 0x32 | Six-star access: TournaMAXX update (Ruby 2/Sapphire) | op | op | op | · | · | · | · |
| 0x33 | Promo credits | · | op | op | op | op | op | op |
| 0x34 | Linked games (Mega-Link) | op | op | op | op | op | op | op |
| 0x35 | No names in high scores | op | op | op | op | op | op | op |
| 0x36 | MegaWeb filter | · | op | op | op | op | op | op |
| 0x37 | TouchTunes / hi-res video | · | op | op | op | op | op | op |
| 0x38 | MegaWeb | · | op | op | op | op | op | op |
| 0x39 | Prize Zone | · | op | op | op | op | op | op |
| 0x3A | Premium erotic | · | op | op | op | op | op | op |
| 0x3B | E-Channel | · | op | op | op | op | op | op |
| 0x3C | Educational attract | · | op | op | op | op | op | op |
| 0x3D | Price display / free-play pricing | · | op | op | op | op | op | op |
| 0x3E | Hot Topics / downloadable content | · | op | op | op | op | op | op |
| 0x3F | (coin setup, NJ rental related) | · | **key** | **key** | **key** | **key** | **key** | **key** |
| 0x40 | Premium-erotic ad screen | · | op | op | op | op | op | op |
| 0x41 | Attract-mode sounds | · | · | op | op | op | op | op |
| 0x42 | Operator Web | · | · | · | op | op | op | op |
| 0x43 | Scrolling marquee text | · | · | · | **key** | **key** | **key** | **key** |
| 0x44 | ShowTenders | · | · | · | op | op | op | op |
| 0x45 | Fantasy Sports (CDM) | · | · | · | op | op | op | op |
| 0x46 | Card-back advertising | · | · | · | op | op | op | op |
| 0x47 | Hide TournaMAXX ranking/events screens | · | · | · | · | **key** | **key** | **key** |
| 0x48 | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x49 | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x4A | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x4B | Force slow senior game play | · | · | · | · | op | op | op |
| 0x4C | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x4D | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x4E | (no reader found in Crown) | · | · | · | · | · | · | · |
| 0x4F | (no reader found in Crown) | · | · | · | · | · | · | · |

Timeline read from the table: MegaNet services (0x36–0x40) arrive with Sapphire; pay-per-time, lease mode, demo mode and the marquee (0x0F, 0x31, 0x2F, 0x43) with Jade; Operator Web, ShowTenders, Fantasy Sports, card-back ads (0x42–0x46) with Jade; senior play (0x4B) and the TournaMAXX-ranking switch (0x47) with Jade 2; the six-star access set (0x1A–0x1C, 0x25, 0x32) is dropped after Sapphire 2. TournaMAXX (0x14) is a key-only switch in every build.
