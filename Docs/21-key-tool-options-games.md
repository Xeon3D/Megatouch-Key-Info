# 21 — Option meanings, menu vs key-only, per-release game names, serial windows (key tool v2)

Scope: the user's change list for the key editor (`scripts/mtkeytool.py`, model `scripts/mtkeylib.py`):
readable option text with descriptions, operator-menu options separated from key-only ones, game
names from each release, a serial check against the release's window, and a Windows `.exe`.
Doing it exposed three layout errors carried since P1, corrected here and in place in `Docs/01`
and `Docs/18`.

Evidence: `scripts/p21-*.py|sh`, `analysis/p21/` (disassembly, per-build slot classes, Merit help
text, extracted game tables), `scripts/data/option_catalog.json`, `scripts/data/game_tables.json`.

## Answer in one paragraph

Every DS1991-era key — the XL/DOS MAXX ones included — carries the same 2-bit option table;
the region `Docs/01` called a Gen 1/2 "per-game table" is that option table, and the Gen 1/2
games live in the D1 nibbles. Each DS1991 family keeps its games differently (DOS nibbles, a
Ruby pair list, a Sapphire price list + bitmap in D1, a Crown price list + bitmap in D2), so the
editor now decodes four DS1991 layouts plus Gen 4. Option slots are classified per release from
that release's own operator menus (ION builds via `MenuSystem::SETUP_OPTION`/`SetOptionValue`/
`NVRAMMap::SetGameOption`), and 67 of the 120 slots are described in Merit's own help text lifted
from `opsetup.so`. Game names come from each release's own game table (25 tables; Force/ION 2006
fall back to Crown). The serial check uses the windows of `Docs/05` plus three Force builds
proven byte-identical to Maxx builds.

## Corrections to earlier phases

**C1 — Gen 1/2 D2[0..0x13] is the option table, not a per-game table** (`Docs/01` Gen 0/1 table,
`Docs/04` header). Test: for every DOS NVRAM in `analysis/p9` with a matching key, compare the key's
2-bit states with the 80 operator-option bytes at that layout's option base (`Docs/08`):

| Result over 18 DOS images (3.06 → Emerald 2, Platinum, Titanium) | |
|---|---|
| slots the key locks (state 0/1) whose stored byte equals the lock | **100 %** in every image |
| state 2 (selectable, default off) stored as 0 on fresh images | 9/9 … 12/12 |
| state 3 (selectable, default on) stored as 1 | 89–100 % |

Under the old reading the Emerald key would enable H2H Photo Hunt (0x22), H2H Trivia (0x24) and
Bowling (0x44), all of which are off in that machine's per-game records.

**C2 — Gen 1/2 games are the D1 nibbles.** One nibble per game id 0x00–0x3F (D1[0..0x1F]); 0 =
game not on the key. On Diamond, Platinum, 2K and 3.06 the value is the price per play (fresh NVRAM
per-game records: nibble 1 → price 1, 2 → 2, 0 → flags 0, no exceptions). On Emerald/Titanium it is
a class code (2 for most games that cost 1 credit). Ids ≥ 0x40 are not on the key.

**C3 — Sapphire is laid out differently from Jade/Crown** (`Docs/01` Gen 3, `Docs/18` platform
table). From the Sapphire V12.01 binary:

| Field | Sapphire (and Force 2004) | Jade / Crown |
|---|---|---|
| option table | **D2[0x16..0x2B], 22 bytes = 88 slots** (`KeyMgr::ExplodeOptions` reads key+0x26+i, i<0x16) | D2[0..0x13], 80 slots |
| price list | D1[0..0x11]; `F<p>` + ids, or `(id, price)` pairs when D1[0] = 0 (`GetGamePriceFromKey`) | D1[0..0x1B] |
| game enable bitmap | **D1[0x12 + id/8]** (`SetGamePriceAndStatusFromKey` via `DallasKeyP2`) | D2[0x14 + id/8] |
| default price | **D2[2]** (`GetGamePriceFromKey` reads `DallasKeyP3+0x12`; 1 on all three keys) | D1[0x2A] |
| territory | D2[4] | D1[0x20] |

So the `Docs/18` statement "Maxx Sapphire D2[0x1C] = 7F, bit 3 set" reads an option byte; on
Sapphire the Bowling (0x44) bit is D1[0x1A] bit 3: **clear on the genuine Maxx Sapphire key SA306501,
set on the Force 2004 key** — as the platform-bit rule predicts. SA305945's D1 is byte-identical to
the Force 2004 key's, so that "Sapphire" key carries Force game data.

**C4 — Ruby 2 / Force 2003 games** (`SetGamePriceAndStatusFromKey`, Ruby 2 V11.00): D1 is a list
scanned to 0x2F: a byte with bit 7 set disables game `byte & 0x7F` (1 byte); otherwise `(id,
price)`; `FF` ends. Unlisted games are on at the default price `DallasKeyP3+0x32` = D2[0x22]
(1 on both Ruby keys).

## Option slots: what each does, and who sets it

`scripts/data/option_catalog.json` (built by `scripts/p21-optcatalog.py`):

- **Labels and descriptions.** 67 slots carry Merit's own operator help text (`<b>Label</b>|text`
  strings, harvested from 8 `opsetup.so` builds by `scripts/p21-help.py`); the rest are written from
  the enum name plus the functions that read or write the slot, and say so. Five slots that the
  Jade/Crown code uses differently from Merit's later ION name (0x0C, 0x0F, 0x2F, 0x43, 0x47) show the
  Crown-era meaning on Jade/Crown keys and mention the later name.
- **Classes per build.** Gen 3 from P12 (`analysis/p12/slot_classes_all.json`). Gen 4 from
  `scripts/p21-gen4slots.py` over `start` + `opsetup.so` + libs: ION 2011 / ION 2014 / Touch2Play 2013
  = 69 menu, 18 key-only, 33 unused; Firefly 74 / 13 / 33 (its unlock options are menu-set).
  TournaMAXX (0x14) is key-only on Crown but a menu toggle on ION ("Select Tournament Mode") —
  still only when the key leaves it selectable. Force 2011 uses an older `KeyManager::Option(int)`
  API and its operator menus are not among the extracted binaries, so Force 2007–2011 keys show
  the ION 2011 classification, labelled "nearest".
- **DOS.** SETUP.DLL addresses only 16–21 option slots directly (the rest through an index table),
  so DOS keys show those as "operator menu" and the others as "not traced" — never as key-only.

## Game names per release

`scripts/data/game_tables.json` (`scripts/p21-gametables.py`): 25 game tables (DOS GAMEDATA.DAT
from `analysis/p16`; Linux gamedata.dat from `analysis/p14`, `analysis/p19/bin`, and newly
`analysis/p21/gamedata` via `scripts/p21-gamedata.sh` — Ruby/Ruby 2/Force 2003 keep
`/usr/local/share/merit` on partition 7, so the file is `/config/gamedata.dat` there) plus the Gen 4
enum tables. Every key version maps to its own software's table first; XL R1/Super 5000/XL 6000 use
MAXX 3.06 and XL Gold uses MAXX 2K (no images), marked "nearest".

- Force 2006: the only image's `gamedata.dat` is entry-for-entry Force 2003's (102 games) while the
  Force 2006 key prices Crown-era ids up to 0xC1 (Merit-thons) — a stale file. Force 2006 and ION 2006
  use Crown's table.
- Force Gen 4 ids agree with the ION enum on all 168 pinned ids, so ION fills the Force gaps.
- Across the whole corpus every enabled game on a DS1991-era key now has a name (test suite).

## Serial windows the editor checks

`mtkeylib.check_serial(version, serial)`: CRC, family, window. New since `Docs/05`, from binary
identity of the packed `start` launchers (md5):

| Force build | identical to | window |
|---|---|---|
| Force 2003.5 v11.00 | Maxx Ruby 2 V11.00 | Ruby 2 (verified) |
| Force 2005 v14.00 | Maxx Jade V14.00 | Jade (verified) |
| Force 2005.5 v15.10 | Maxx Jade 2 V15.10 | Jade (verified) |
| Force 2003 v10.09, 2004, 2006; ION 2006 | — (different or missing binary) | nearest Maxx sibling, flagged "inferred" |

The extracted Force `start` files are the packed launchers, which is why the window constants do not
show in them. Gen 4: family must be DS1995 (0A) or DS1996 (0C/8C) and large enough for the
release's block offset (ION 2013 needs 7 KB → DS1996 only); no window (`Docs/19`).

## Tool changes (P21)

- Options tab: grouped (operator menu / key only / game / server / unused / not traced), readable
  label, one-line description, detail pane with the full text, its source and Merit's name.
- Games tab: names from the release's own table, a "Game names from" switch, Merit's per-game flags;
  Gen 3 prices decoded from the price list (they were read as nibbles before), Gen 1/2 from the D1
  nibbles, Ruby from its list, 2007 keys enabled by price (no bitmap in that generation).
- Change button serial: live CRC / family / window check, "Fix CRC", "Suggest a valid serial";
  confirms before applying a serial the release would reject. Same check in New key, Verify and on
  open.
- `Run/Megatouch Key Tool.exe`: one-file Windows build (PyInstaller 6.22.3 in `build/venv`,
  `scripts/p21-build-exe.py`), self-tested by launching the packaged exe in `--selftest` mode on a
  Crown, Emerald, Sapphire and ION 2009 key.
- `scripts/test-mtkeytool.py --gui`: all checks pass (107 dumps, 19 edit cycles, 33 generated
  releases, new layout/name/serial checks: Crown USA 101 games / 13 at price 2, price list restored
  byte-exact after an edit, Crown 53 menu / 10 key-only, CAN-VER2 rejected by Crown, a suggested
  serial accepted by every release).

## Open

1. Emerald/Titanium meaning of the D1 nibble value (class code, not price).
2. Force 2007–2011 operator menus (not extracted) for a Force-specific classification.
3. The DOS option index table in SETUP.DLL (would complete the DOS menu/key split).
