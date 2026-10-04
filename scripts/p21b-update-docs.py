"""p21b-update-docs.py - fold the P21 findings into keyinfo.md and keyinfo-human.md.

P21 (Docs/21) corrected three layout readings carried since P1 and added option meanings,
per-release game names and the serial-window check. Those landed in Docs/, but only partly in
the two handover docs. This script finishes the job.

Every anchor is asserted (a missed anchor is an error, never a silent no-op - the P20 lesson)
and each file carries a sentinel, so a second run is a no-op.

    python scripts/p21b-update-docs.py
    python scripts/p21b-update-docs.py --check
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SENTINEL = '<!-- p21b: option meanings, per-release game names, per-family layouts -->'

# ---------------------------------------------------------------- keyinfo.md

AGENT = os.path.join(ROOT, 'keyinfo.md')

SAPPHIRE = """The "platform bit" D2[0x1C] bit 3 used by the Crown gate is game **0x44** in that bitmap (§5).

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
key's, so that Sapphire-labelled key carries Force game data."""

RUBY = """`de621043 21100293` (Ruby). D1 holds price nibbles on Titanium/Emerald and a game-ID list on Ruby.

Ruby 2 / Force 2003 game list (`SetGamePriceAndStatusFromKey`, Ruby 2 V11.00) [code, P21]: D1 is
scanned to offset 0x2F; a byte with **bit 7 set disables** game `byte & 0x7F` and consumes one byte,
any other byte is the first half of an `(id, price)` pair, and `FF` ends the list. Games not named in
the list are **on** at the default price `DallasKeyP3+0x32` = D2[0x22] (1 on both Ruby keys). So a
Ruby key is an opt-*out* list, unlike every other generation."""

FORCEWIN = """- The windows move upward over time (Merit buying consecutive lots), and each build also accepts some
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
  7 KB, so it needs a DS1996."""

SLOTCLASSES = """### What each slot does, and who sets it [P21: `scripts/data/option_catalog.json`]

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
table; their games are the D1 nibbles)."""

GAMENAMES = """- Example, Crown USA key: 101 games enabled; 13 at price 2 (Merit-thon events, Checkerz, Lonestar);
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
  (asserted in `scripts/test-mtkeytool.py`)."""

CATALOGUE = """| **Key editor** | **`mtkeytool.py`** (GUI), **`mtkeylib.py`** (model for all 4 generations), **`test-mtkeytool.py`** (regression suite), `data/{options,games}.json`, **`data/option_catalog.json`** (labels, descriptions, per-release classes), **`data/game_tables.json`** (26 game tables) |
| **Option meanings / game tables / packaging (P21)** | **`p21-optcatalog.py`** (build the option catalogue), `p21-help.py` (harvest Merit's help strings from `opsetup.so`), `p21-gen4slots.py` (Gen 4 menu vs key-only), `p21-gametables.py` (collect every release's game table), `p21-gamedata.sh` (extract the partition-7 tables), **`p21-build-exe.py`** (one-file Windows build via PyInstaller), `p21-update-share.py`, `p21b-update-docs.py` |"""

DONE = """- a **key editor covering all 33 releases** (`scripts/mtkeytool.py`, standalone copy in `Run/`, plus a
  one-file `Run/Megatouch Key Tool.exe`), with a regression suite that loads 107 dumps, round-trips
  every one, generates all 33 releases, and checks the layout, name and serial rules;
- **what each option slot does** (67 of 120 in Merit's own help text) and **who sets it**, per release;
- **per-release game names** (26 tables) and the per-family game/price layouts;
- the **serial-window check** for every release, including the three Force builds proven byte-identical
  to their Maxx siblings;"""

OPEN9 = """9. Which options the **DOS** operator menus offer: the DOS keys carry the same 80-slot table, but
   `SETUP.DLL` reaches most slots through an index table that has not been traced, so only 16-21 per
   layout are confirmed as menu settings. Likewise the **Force 2007-2011 operator menus** are not
   among the extracted files, so those keys are classified from ION 2011.
10. ~~Labels for most of the Force-line game ids.~~ **Closed** - the Force ids agree with the ION enum
    on all 168 that could be pinned, so ION fills the gaps. 8 ION ids out of 301 remain unlabelled (an
    extractor limitation on fall-through switch leaves, not an unknown in the format)."""

AGENT_EDITS = [
    ('The "platform bit" D2[0x1C] bit 3 used by the Crown gate is game **0x44** in that bitmap (§5).',
     SAPPHIRE),
    ('`de621043 21100293` (Ruby). D1 holds price nibbles on Titanium/Emerald and a game-ID list on Ruby.',
     RUBY),
    ('''- The windows move upward over time (Merit buying consecutive lots), and each build also accepts some
  older lots.''', FORCEWIN),
    ('Gen 3 keys hold `D2[0..0x13]` = 80 two-bit states (Gen 1/2 use the same place for their game table).',
     SLOTCLASSES),
    ('''- Example, Crown USA key: 101 games enabled; 13 at price 2 (Merit-thon events, Checkerz, Lonestar);
  default price 1.''', GAMENAMES),
    ('| **Key editor** | **`mtkeytool.py`** (GUI), **`mtkeylib.py`** (model for all 4 generations), **`test-mtkeytool.py`** (regression suite), `data/{options,games}.json` |',
     CATALOGUE),
    ('''- a **key editor covering all 33 releases** (`scripts/mtkeytool.py`, standalone copy in `Run/`), with a
  regression suite that loads 107 dumps, round-trips every one, and generates all 33 releases;''',
     DONE),
    ('''9. Labels for the 8 unpinned ION game ids and most of the Force-line ids (an extractor limitation on
   fall-through switch leaves, not an unknown in the format).''', OPEN9),
    # the DOS-menu question is now stated in full under item 9
    ('''3. Name the DOS option slots per layout. `nvram.py` currently shows Crown names for DOS options, which
   is wrong.''',
     '''3. Name the DOS option slots per layout. `nvram.py` currently shows Crown names for DOS options,
   which is wrong; the key editor labels them from the catalogue instead (see item 9).'''),
    # item 9 became 9 + 10, so the two items after it shift down
    ('''10. The Gen 4 NVRAM layout: settings moved to `/merit/settings.xml` plus SQLite and `/config/nvram.dat`
    shrank to 5 792 B, so none of the §10 NVRAM work carries over.
11. The executable self-read integrity check inside `KeyManager::Check` (surface N).''',
     '''11. The Gen 4 NVRAM layout: settings moved to `/merit/settings.xml` plus SQLite and `/config/nvram.dat`
    shrank to 5 792 B, so none of the §10 NVRAM work carries over.
12. The executable self-read integrity check inside `KeyManager::Check` (surface N).'''),
]

# ---------------------------------------------------------- keyinfo-human.md

HUMAN = os.path.join(ROOT, 'keyinfo-human.md')

H_SWITCH = """The full list of 120 is in `Docs/19`, and the key editor shows every switch by name.

### What each switch does, and who can change it

A number and an internal name still do not say what a switch *does*. Merit's own operator help text
answers that for **67 of the 120**: the later programs carry the help screens as text, and they were
lifted out whole, so for those switches the description in the editor is Merit's wording, not a guess.
The other 53 are described from the program code that reads them, and the editor says which kind of
description you are looking at. Five switches meant something different in the Crown era than the name
Merit later gave them; the editor shows the Crown meaning when you open a Crown-era key.

Each release is also now split by **who sets a switch**: the operator menus, or the key alone. Only
the key-only ones are decided entirely by Merit.

| Release | Operator menu | Key only | Unused by that release |
|---|---|---|---|
| Ruby 2 | 38 | 5 | 37 |
| Sapphire | 51 | 5 | 24 |
| Jade | 52 | 9 | 19 |
| Crown (and Jade 2) | 53 | 10 | 17 |
| ION 2011 / 2014, Touch2Play | 69 | 18 | 33 |
| Firefly | 74 | 13 | 33 |
| DOS machines | 16-20 traced | - | the rest go through a menu table nobody has traced yet |

TournaMAXX is the clearest case of a switch changing hands: key-only on every Linux machine up to
Crown, but on ION it became an ordinary menu choice ("Select Tournament Mode") - which the key can
still take away."""

H_DOCS04 = """The full slot-by-slot table is in `Docs/04-territory-options.md`, and what each switch does, release
by release, in `Docs/21-key-tool-options-games.md`."""

H_GAMES = """The table grew from 51 games (MAXX 3.06) through 84 (Emerald) to 195 (Crown), and to roughly 300 on
the ION machines. On Linux, each game also has flags such as head-to-head, Merit-thon event, Prize
Zone and **Force-only**.

Because the numbering is just a position in a file, **the same number means a different game on a
different release**. The key editor therefore carries 26 of these tables - one per release, plus the
two built into the 2007-and-later programs - and names a key's games from its own release's table. The
few releases with no surviving disk image borrow the nearest one and say so.

Where the games live differs by family:

| Keys | Which games are on | Prices |
|---|---|---|
| XL and DOS MAXX | one half-byte per game; 0 means the game is not on the key | that same half-byte is the price on the older machines; a price class on Emerald and Titanium |
| Ruby 2 | a list of games to switch **off** - everything else is on | prices given as game-and-price pairs, with a default for the rest |
| Sapphire | an on/off map, in a different place from later keys | a price list, with a default |
| Jade, Crown | an on/off map | a price list that sets prices in groups (e.g. "price 2: Checkerz, Lonestar, the Merit-thon events"), with a default |
| Force / ION 2007+ | a 300-game on/off map | one byte per game: the price, plus what a continue costs |

The USA Crown key enables 101 games, 13 of them at 2 credits."""

H_TOOLS = """| **`mtkeytool.py`** | **the key editor: a window that opens any key from any year, shows every field, switch and game by name, lets you change them and save the result as a new key, re-encrypted for whatever button you choose. It can also generate a blank key for any of the 33 releases.** A ready-to-run copy lives in the `Run/` folder, including **`Megatouch Key Tool.exe`** - one Windows file, no Python needed |"""

H_DOC21 = """| 19 | the 2007-and-later key format, all 120 switch names, game numbering |
| 21 | what each switch does and who sets it, per-release game names, serial-range checks |"""

H_OPEN = """- ~~Names for a handful of game slots on the Force side.~~ **Settled:** the Force numbering agrees with
  the ION numbering on all 168 games that could be checked, so the ION names fill the Force gaps. Eight
  of ION's own ~300 slots are still unlabelled.
- The **Force 2007-2011 operator menus**, which were not among the recovered files. Those keys' switches
  are shown with the ION 2011 split between menu and key-only instead."""

HUMAN_EDITS = [
    ('The full list of 120 is in `Docs/19`, and the key editor shows every switch by name.', H_SWITCH),
    ('The full slot-by-slot table is in `Docs/04-territory-options.md`.', H_DOCS04),
    ('''The table grew from 51 games (MAXX 3.06) through 84 (Emerald) to 195 (Crown). On Linux, each game also
has flags such as head-to-head, Merit-thon event, Prize Zone and **Force-only**.

On Sapphire, Jade and Crown keys:
- the **game list** turns each game on or off;
- the **price list** sets prices in groups (e.g. "price 2: Checkerz, Lonestar, the Merit-thon events");
- everything else costs the default price.

The USA Crown key enables 101 games, 13 of them at 2 credits.''', H_GAMES),
    ('| **`mtkeytool.py`** | **the key editor: a window that opens any key from any year, shows every field, switch and game by name, lets you change them and save the result as a new key, re-encrypted for whatever button you choose. It can also generate a blank key for any of the 33 releases.** A ready-to-run copy lives in the `Run/` folder |',
     H_TOOLS),
    ('| 19 | the 2007-and-later key format, all 120 switch names, game numbering |', H_DOC21),
    ('- Names for a handful of game slots on the Force side.', H_OPEN),
    # the ION menu toggle is stated just above now, so qualify the old blanket claim
    ('**TournaMAXX is switch 0x14.** No operator menu can change it, so only the key decides:',
     '**TournaMAXX is switch 0x14.** On the machines up to Crown no operator menu can change it, so\nonly the key decides:'),
]


def apply(path, edits):
    s = open(path, encoding='utf-8').read()
    if SENTINEL in s:
        print('%-18s already updated (sentinel present)' % os.path.basename(path))
        return 0, s, False
    missing = [old for old, _ in edits if s.count(old) != 1]
    if missing:
        for m in missing:
            print('  !! %s: anchor not found exactly once: %r'
                  % (os.path.basename(path), m.split('\n')[0][:70]))
        return 1, s, False
    for old, new in edits:
        s = s.replace(old, new, 1)
    return 0, s.rstrip() + '\n\n' + SENTINEL + '\n', True


def main():
    check = '--check' in sys.argv
    out = []
    for path, edits in ((AGENT, AGENT_EDITS), (HUMAN, HUMAN_EDITS)):
        rc, s, changed = apply(path, edits)
        if rc:
            print('refusing to write a partial update')
            return 1
        out.append((path, s, changed, len(edits)))
    if check:
        for path, _, changed, n in out:
            print('%-18s %s' % (os.path.basename(path), '%d edits would apply' % n if changed else 'no change'))
        return 0
    for path, s, changed, n in out:
        if changed:
            open(path, 'w', encoding='utf-8').write(s)
            print('%-18s %d edits applied, %d lines'
                  % (os.path.basename(path), n, s.count('\n') + 1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
