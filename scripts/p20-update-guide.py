"""p20-update-guide.py - fold the Force/ION + Gen 4 findings into keyinfo-human.md,
the plain-language guide. Companion to p20-update-docs.py (which does keyinfo.md).

Every edit is an exact-string replacement that must apply; a sentinel at the end of the
file makes a second run a no-op, because several edits are insertions whose anchor text
survives and would otherwise duplicate.

    python scripts/p20-update-guide.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'keyinfo-human.md')
SENTINEL = '<!-- p20: Force/ION + Gen 4 content merged -->'

EDITS = [

("""A guide to the Dallas iButton keys used by Merit Megatouch machines, from the XL (1997) to the MAXX Crown
(2005).""",
 """A guide to the Dallas iButton keys used by Merit Megatouch machines, from the XL (1997) all the way to
ION 2014 - that is both the Maxx/XL line and the Force / ION line, plus Touch2Play and Firefly."""),

("""- **Merit locked features on the key.** Every Sapphire, Jade and Crown key carries 80 two-bit
  switches. Each feature can be forced off, forced on, or left to the operator. TournaMAXX is
  switch 0x14: forced on in the Jade keys, locked off in the Crown keys.""",
 """- **Merit locked features on the key.** Every Sapphire, Jade and Crown key carries 80 two-bit
  switches; the Force/ION keys from 2007 carry 120, one byte each. Each feature can be forced off,
  forced on, or left to the operator. TournaMAXX is switch 0x14: forced on in the Jade keys, locked off
  in the Crown keys. **Every switch now has its real name**, read out of the game software itself.
- **Force and ION are the same software as the Maxx of the same year.** Force 2002-2006 and ION 2006
  keys use byte-identical scrambling to their Maxx counterparts; only the signature differs. One
  program really does serve several products - Maxx Ruby 2 and Force 2003.5 share a game binary, and
  the key is what decides which product the machine becomes.
- **In 2007 Merit changed the button.** Force 2007 and ION 2007 onward dropped the DS1991 MultiKey for
  a plain memory button with **no passwords at all** - just a 1 KB block behind a weak scrambler."""),

("""The key is a **Dallas DS1991 MultiKey** iButton: a small steel button with a 1-Wire chip inside. Later
machines use the **DS1425**, which works the same way but reports a different family code (0x82
instead of 0x02).""",
 """Up to 2006 the key is a **Dallas DS1991 MultiKey** iButton: a small steel button with a 1-Wire chip
inside. Later machines use the **DS1425**, which works the same way but reports a different family code
(0x82 instead of 0x02).

From **Force 2007 and ION 2007** Merit switched to an ordinary memory button - a **DS1995** (2 KB,
family 0x0A) for ION 2007 and a **DS1996** (8 KB, family 0x0C or 0x8C) for everything after. These have
no protected compartments and no passwords whatsoever: the whole key is a single 1024-byte block
sitting in plain memory, and the only thing between a reader and the contents is the scrambler. The
software picks which layout to expect purely from the button's family code."""),

("""| Jade | Jade, Jade 2 |
| Crown | Crown |""",
 """| Jade | Jade, Jade 2, **Force 2005** |
| Crown | Crown, **Force 2006, ION 2006** |

The Force keys of the DS1991 era reuse their Maxx cousin's scrambling exactly - Force 2002 is Emerald,
Force 2003 is Ruby, Force 2004 is Sapphire. Force 2003 even uses the *same passwords* as Maxx Ruby 2,
so those two are interchangeable apart from the signature.

**The 2007-and-later keys work differently.** There are no passwords, and the scrambler is a repeating
six-byte pattern built from the button's serial and a per-year constant. That is weak enough to break
knowing nothing at all: the contents always begin with the part number `SAnnnn`, and six known
characters give away the whole pattern; long runs of blank data print it outright. Working backwards
from the pattern even recovers the button's serial number, which is how two unlabelled dumps in the
collection were identified. Each of these keys also carries a 16-bit checksum, so a careless edit is
caught at boot."""),

("""**Sapphire, Jade and Crown keys** were reorganised:""",
 """**Force 2007 and ION 2007 onward** were reorganised again, into one 1 KB block:
- the part number, a **programming date stored as a timestamp** rather than as text, and the revision;
- the **territory name** and a country code;
- the **MegaNet server address** and the **web portal address**, as plain readable text
  (`us.accessmerit.com`, `meritgames.com/us-portal.htm`);
- the **signature**, now about a quarter of the way in;
- six **coin channels** with values, credits and credit values;
- a **price for each of 300 game slots**, two prices packed into every byte (play and continue);
- **120 feature switches**, a whole byte each;
- a **300-bit game list**;
- a **16-bit checksum**;
- and, right at the end, a few bytes tied to the button's serial that the game never even reads.

**Sapphire, Jade and Crown keys** were reorganised:"""),

("""## 6. The 80 feature switches

Sapphire, Jade and Crown keys carry 80 switches of two bits each:""",
 """## 6. The feature switches

Sapphire, Jade and Crown keys carry 80 switches of two bits each; Force/ION keys from 2007 carry 120,
a whole byte each. The meanings are the same:"""),

("""The machine stores the operator's choice for each switch. It only uses that choice when the key allows
the operator to change the switch; otherwise the key wins.""",
 """The machine stores the operator's choice for each switch. It only uses that choice when the key allows
the operator to change the switch; otherwise the key wins.

**All of them are now named.** The later Force/ION programs carry a built-in table translating each
switch number into its internal name, and it was lifted out whole. The same table appears unchanged in
ION 2011, ION 2014, Touch2Play 2013 and Firefly 2010, and it agrees with everything previously worked
out by hand for Crown - so the first 80 names apply to the Sapphire, Jade and Crown keys as well. A
sample of the more interesting ones:

| # | switch | what it is |
|---|---|---|
| 0x02 | `enable_rental_mode_inx` | rental mode |
| 0x0D | `six_stars_enabled_inx` | the hidden six-star operator menu |
| 0x11 | `golf_has_women_inx` | women golfers in the golf game |
| 0x14 | `tournamaxx_enabled_inx` | TournaMAXX |
| 0x1E | `allow_nudity_inx` | adult content |
| 0x29 | `free_play_enabled_inx` | free play |
| 0x31 | `lease_mode_enabled_inx` | lease / time-bomb mode |
| 0x3D | `enable_coinless_coinop_inx` | coinless operation |
| 0x5C | `allow_coin_in_table_modification` | operator may edit the coin table |
| 0x67 | `firefly_mode_enabled` | Firefly mode |

The full list of 120 is in `Docs/19`, and the key editor shows every switch by name."""),

("""What this means in practice:
- **A blank DS1991 re-flashed with Jade or Crown data will not boot**, even though it decodes
  perfectly.""",
 """**The 2007-and-later machines dropped this check entirely.** Once the scrambling itself was keyed to
the button's serial a range check became redundant: a key written for one button simply turns to
garbage on another and fails its signature and its checksum. Every genuine Force/ION key is still from
a Merit batch, but nothing in the software looks.

What this means in practice:
- **A blank DS1991 re-flashed with Jade or Crown data will not boot**, even though it decodes
  perfectly."""),

("""| Tool | Does |
|---|---|
| `mtkey.py decrypt <dump>` | identifies the key family and decodes a keyflasher dump (all families, including Crown) |""",
 """| Tool | Does |
|---|---|
| **`mtkeytool.py`** | **the key editor: a window that opens any key from any year, shows every field, switch and game by name, lets you change them and save the result as a new key, re-encrypted for whatever button you choose. It can also generate a blank key for any of the 33 releases.** A ready-to-run copy lives in the `Run/` folder |
| `mtkey.py decrypt <dump>` | identifies the key family and decodes a keyflasher dump (all families, including Crown) |
| `mtkey4.py decrypt <dump>` | the same for the 2007-and-later Force/ION keys |
| `keyinfo4.py <dump>` | readable report for a Force/ION key: fields, switches, games, checksum |"""),

("""| 05 | serial ranges |
| 08 | settings memory |""",
 """| 05 | serial ranges |
| 08 | settings memory |
| 18 | the Force / ION line: buttons, scrambling, passwords, signatures |
| 19 | the 2007-and-later key format, all 120 switch names, game numbering |"""),

("""## 11. Still unknown

- Whether the second Crown signature (ending `87`) belongs to Force/ION keys. A Force key dump would
  settle it.""",
 """## 11. Still unknown

- ~~Whether the second Crown signature (ending `87`) belongs to Force/ION keys.~~ **Settled: it does
  not.** With real Force dumps in hand, Force 2005 turns out to carry exactly the same signature as
  Maxx Jade, and the Force/Maxx difference shows up in the *first* byte instead - Force 2006 reads
  `86 24...` where Crown reads `87 23...`. The `87`-ending variant belongs to a different rule, about
  accented characters in the territory name.
- A **genuine ION 2014 key**. The only one available contradicts itself (it claims Canada while its
  territory text says USA, and its date decodes to 1977), so it is almost certainly hand-made.
- What the few serial-tied bytes at the end of a Force/ION key are for. Six otherwise identical ION
  2009 keys differ *only* in those bytes, and the game never reads them.
- Names for a handful of game slots on the Force side.
- The settings memory of the 2007-and-later machines, which moved to XML files and a database."""),
]


def main():
    s = open(TARGET, encoding='utf-8').read()
    if SENTINEL in s:
        print('keyinfo-human.md already updated (sentinel present), nothing to do')
        return 0
    missing = [old for old, _ in EDITS if old not in s]
    if missing:
        for m in missing:
            print('  !! no match: %r' % m.split('\n')[0][:72])
        print('refusing to write a partial update')
        return 1
    for old, new in EDITS:
        s = s.replace(old, new, 1)
    open(TARGET, 'w', encoding='utf-8').write(s.rstrip() + '\n\n' + SENTINEL + '\n')
    print('keyinfo-human.md: %d edits applied' % len(EDITS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
