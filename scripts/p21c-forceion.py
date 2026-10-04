"""p21c-forceion.py - weave the Force / ION findings through every topic of the handover docs and the
share pages, instead of leaving them in their own late sections.

Targets (each guarded by a sentinel, every anchor asserted - a missed anchor is an error):
  keyinfo-human.md                     new "products and their keys" section; Force/ION in what is on a
                                       key, territories, switches (incl. the per-key product switches),
                                       serial ranges, games, settings memory; sections renumbered
  keyinfo.md                           product/release table, model numbers, the Gen 4 key-only switch
                                       states, SA305945 reading
  share/megatouch-security-keys.html   findings cards, new "Products" section, Gen 4 in key anatomy,
                                       Force/ION rows in acceptance and territory, Force/ION key states
                                       in option locks, Force/ION games, Gen 4 settings memory
then regenerates share/megatouch-keys-guide.html from keyinfo-human.md (p20-update-share.py).

Facts used (all on disk): Docs/18, Docs/19, Docs/21; key states from the dumps in
`Key Info & Dumps/Force - ION` via scripts/mtkeylib.py; SA305945 password check (MSAPPHIRE set).

    python scripts/p21c-forceion.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUMAN = os.path.join(ROOT, 'keyinfo-human.md')
AGENT = os.path.join(ROOT, 'keyinfo.md')
PAGE = os.path.join(ROOT, 'share', 'megatouch-security-keys.html')
SENT_MD = '<!-- p21c: Force / ION woven through every topic -->'


def rep(s, a, b, count=1):
    assert s.count(a) == count, 'anchor found %d times (want %d): %r' % (s.count(a), count, a[:90])
    return s.replace(a, b)


# ----------------------------------------------------------------------------- shared tables

PRODUCTS_MD = """## 2. The products and their keys

Merit sold three product lines on one code base, and every one of them used these keys:

- **Megatouch XL / MAXX** (1997-2005): the bartop and upright Maxx machines, XL R1 to MAXX Crown.
- **Megatouch Force** (2002-2011): a newer cabinet with its own motherboard.
- **Megatouch ION** (2006-2014), plus **Touch2Play** (2013) and **Firefly** (2010) built on the ION
  software.

| Key era | Maxx / XL | Force | ION and others | Button |
|---|---|---|---|---|
| Generation 1 (DOS) | XL R1, Super 5000, XL 6000, MAXX 3.06, XL Gold, MAXX 2K / 2K Plus, XL Platinum, Diamond, Double Diamond | - | - | DS1991 |
| Generation 2 | XL Titanium, Emerald (DOS); Ruby 2 (Linux) | Force 2002 (a DOS build), Force 2003 / 2003.5 | - | DS1991, then DS1425 |
| Generation 3 | Sapphire, Jade, Crown | Force 2004, 2005 / 2005.5, 2006 | ION 2006 | DS1425 |
| Generation 4 (2007 format) | - | Force 2007 - 2011 | ION 2007 - 2014, Touch2Play 2013, Firefly 2010 | DS1995 (ION 2007), DS1996 (all others) |

Model numbers seen on Force and ION keys: Force 2002 `SA3050`, 2003 `SA3059`, 2004 `SA3068`, 2005
`SA3083`, 2006 `SA3501`/`SA3504`; ION 2006 `SA3505`; Force 2007 `SA3526`, 2008 `SA3542`/`SA3543`, 2009
`SA3570`/`SA3572`, 2010 `SA3579`, 2011 `SA3603`/`SA3604`; ION 2007 `SA3522`/`SA3523`, 2008
`SA3547`/`SA3548`, 2009 `SA3559`/`SA3560`, 2010 `SA3590`, 2011 `SA3605`/`SA3607`, 2012
`SA3614`/`SA3617`, 2013 `SA3623`/`SA3624`, 2014 `SA3628`/`SA3630`. As on the Maxx side, the software
never checks these.

**Force and ION are the Maxx software of the same year.** Three Force programs are byte-for-byte the
Maxx one: Force 2003.5 is Maxx Ruby 2 V11.00, Force 2005 is Maxx Jade V14.00, Force 2005.5 is Maxx Jade
2 V15.10. Up to 2006 a Force or ION key uses its Maxx cousin's scrambling exactly; only the signature
and the password recipe differ. Force 2003 does not even differ in those - its passwords and signature
are Ruby 2's, so a Force 2003 key and a Ruby 2 key differ only in the model number and the games
listed.

**The key decides which product a machine becomes.** On the shared programs the key carries a
"platform" flag (the on/off bit of game 0x44, Bowling, a Force-only game); every Force and ION key of
the DS1991 era has it set, every Maxx Crown key has it clear. The 2007-and-later keys go further: a
whole group of switches only Merit can set turns the same software into Touch2Play, KidZpace, MindSpark,
a lease machine or a UAE prize machine (section 7). On every standard Force and ION key they are all
locked off.

**Force and ION split at the signature.** From 2007 to 2010 a Force key and an ION key of the same year
use the same scrambling and the same layout; only the 8-byte signature tells them apart (ION 2008's is
Force 2008's written backwards). In 2011 the Force line ended and ION continued with new scrambling
constants every year.

One curiosity: a key labelled `SA305945` is a genuine Maxx Sapphire key (Sapphire scrambling, Maxx
Sapphire passwords and signature) that carries the Force model number `SA3059` and the Force 2004 game
list. Merit's own help text mentions "MAXX-to-FORCE upgraded games", and this looks like the key for
such an upgrade - an inference, not proven.

"""

FORCE_SWITCHES_MD = """### What Merit decides on a Force / ION key

On the 2007-and-later software 18 switches have no operator control at all. They are what Merit sold,
or withheld, per key - mostly whole product variants. Their state on every genuine Force and ION key in
the collection (0 locked off, 1 forced on, 3 operator may change it):

| # | Switch | Force 2007 | 2008 | 2009 | 2010 | 2011 | ION 2007 | 2008 | 2009 | 2014 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0x14 | TournaMAXX (an operator menu choice on ION, but the key can lock it) | 1 | 3 | 1 | 1 | 1 | 3 | 3 | 3 | 3 |
| 0x0B | TournaMAXX allowed in free play | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| 0x0C | TournaMAXX price differs from regular price | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 0x0F | Rental mode: 5-row price table | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 0x10 | Touch2Play mode | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x2F | Senior mode | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x31 | Lease mode (time bomb) | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x39 | Prize Zone | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 3 | 0 |
| 0x3F | Quick pricing | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| 0x43 | MindSpark mode | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x47 | Premiere tournament terminal | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x52 | Operator setup from Six Stars | 3 | 3 | 3 | 3 | 0 | 3 | 3 | 3 | 0 |
| 0x59 | KidZpace mode | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x5C | Allow coin-in table changes | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 0x5D | UAE prize mode | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x6D | MegaNet without TournaMAXX | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0x72 | Download selector | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

(Disable free credits 0x1D and alternate language selection 0x51 complete the 18; the first is off and
the second operator-changeable on all of them.) The pattern is clear: TournaMAXX is always available on
Force and ION keys - forced on for Force, the operator's choice on ION - unlike the Maxx Crown keys,
which lock it off. The product-variant switches are off on every standard key; a Touch2Play, KidZpace or
MindSpark machine is the same software with a different key. The ION 2014 sample also locks off Prize
Zone and the six-star route into operator setup, but that sample is suspect (section 12).

On the DS1991-era Force and ION keys TournaMAXX is forced on for Force 2005 and operator-changeable for
Force 2006 and ION 2006.

"""

GAMES_FORCE_MD = """
On the Force side the game tables are smaller than their Maxx siblings at first (Force 2003: 102 games,
Force 2004: 146) and then the same as the Maxx software they share (Force 2005 / 2005.5: 173 / 180). The
2007-and-later keys have room for 300 games, and their numbering carries straight on from the Maxx one:
game 0 is still Solitaire and 4 is still Match 'Em Up, with retired games keeping their number (the ION
table calls it `g_match_removed`). Genuine keys enable 137 (Force 2009) to 200 (ION 2014) games; on the
2007 keys, which predate the on/off list, a game is on when it has a price. The only Force 2006 disk
image carries a stale copy of Force 2003's game table, so Force 2006 and ION 2006 keys are named from
Crown's.
"""

NVRAM_FORCE_MD = """
**Force and ION.** Up to 2006 the Force machines keep the same `nvram.dat` as the Maxx software they
share. From 2007 the settings moved into XML files (`/merit/settings.xml`) and an SQLite database, and
`nvram.dat` shrank to 5,792 bytes; that layout has not been mapped yet.
"""

# ----------------------------------------------------------------------------- keyinfo-human.md


def human(s):
    s = rep(s, "- **Merit locked features on the key.** Every Sapphire, Jade and Crown key carries 80 two-bit\n"
               "  switches; the Force/ION keys from 2007 carry 120, one byte each.",
            "- **Merit locked features on the key.** Every key up to 2006 carries 80 two-bit switches (88 on\n"
            "  Sapphire), Maxx, XL, Force and ION alike; the Force/ION keys from 2007 carry 120, one byte each.")
    s = rep(s, "  the key is what decides which product the machine becomes.\n",
            "  the key is what decides which product the machine becomes. On the 2007-and-later keys Merit also\n"
            "  uses the key to turn the same software into Touch2Play, KidZpace or MindSpark machines.\n")
    # renumber sections 2..11 -> 3..12 (and the cross-references), then insert the new section 2
    for n in range(11, 1, -1):
        s = rep(s, '\n## %d. ' % n, '\n## %d. ' % (n + 1))
    s = s.replace('(section 7)', '(section 8)').replace('(section 6)', '(section 7)')
    s = rep(s, '\n---\n\n## 3. How the contents are protected',
            '\n---\n\n' + PRODUCTS_MD + '---\n\n## 3. How the contents are protected')
    # what is on a key: four generations, in order, with the Force/ION members
    s = rep(s, 'The rest changed over the years, in three generations.',
            'The rest changed over the years, in four generations.')
    s = rep(s, "**Titanium, Emerald and Ruby keys:** the same structure with new signature values.",
            "**Titanium, Emerald and Ruby keys** (and Force 2002 / 2003): the same structure with new signature\n"
            "values. Ruby 2 and Force 2003 list the games to switch *off* instead.")
    a = s.index('**Force 2007 and ION 2007 onward** were reorganised again')
    b = s.index('**Sapphire, Jade and Crown keys** were reorganised:')
    c = s.index('\n---\n', b)
    gen4, gen3 = s[a:b], s[b:c]
    gen3 = rep(gen3, '**Sapphire, Jade and Crown keys** were reorganised:',
               '**Sapphire, Jade and Crown keys** (and Force 2004-2006, ION 2006) were reorganised:')
    s = s[:a] + gen3.rstrip('\n') + '\n\n' + gen4.rstrip('\n') + '\n' + s[c:]
    s = rep(s, 'SA3031; Sapphire SA3059 and SA3065; Crown SA3511 and SA3513)',
            'SA3031; Ruby 2 SA3056 and SA3061; Crown SA3511 and SA3513)')
    # territories
    s = rep(s, "| 01 | USA-STD | almost everything |", "| 01 | USA-STD | almost everything, including every Force key and ION up to 2010 |")
    s = rep(s, "| 09 | USA-VER1 | MAXX 2K |", "| 09 | USA-VER1 | MAXX 2K; ION 2011, 2012, 2013 |")
    s = rep(s, "- One Sapphire key says USA-STD but ends in 45.",
            "- One Sapphire key says USA-STD but ends in 45. It is a Maxx Sapphire key carrying the Force model\n"
            "  number and game list - probably a Maxx-to-Force upgrade key (section 2).")
    s = rep(s, "Any territory name starting with **NJ** switches the machine into New Jersey mode in every version.",
            "Any territory name starting with **NJ** switches the machine into New Jersey mode in every version.\n"
            "The 2007-and-later keys keep the territory as text too, next to a country code, a New Jersey\n"
            "exception number and the MegaNet server address for that market (`us.accessmerit.com` on the USA\n"
            "keys). The only ION 2014 key in the collection contradicts itself here: country code 1 (Canada)\n"
            "with the territory text `USA-STD`.")
    # switches: plain labels instead of internal names, then the Force/ION per-key table
    a = s.index('| # | switch | what it is |')
    b = s.index('The full list of 120 is in `Docs/19`')
    s = s[:a] + """| # | Switch |
|---|---|
| 0x02 | Rental mode |
| 0x0D | Six Stars, the hidden operator shortcut |
| 0x11 | Women golfers in Golf |
| 0x14 | TournaMAXX |
| 0x1E | Allow nudity |
| 0x29 | Free play |
| 0x31 | Lease mode (time bomb) |
| 0x3D | Coinless coin-op |
| 0x5C | Operator may edit the coin-in table |
| 0x67 | Firefly mode |

""" + s[b:]
    s = rep(s, "\n### What the switches do\n", "\n" + FORCE_SWITCHES_MD + "### What the switches do on Crown\n")
    s = rep(s, "| Crown USA and Canada | locked off |",
            "| Crown USA and Canada | locked off |\n| Force 2005, 2007, 2009, 2010, 2011 | forced on |\n"
            "| Force 2006, 2008; ION 2006 - 2014 | operator may change it |")
    # serial ranges
    s = rep(s, "| Crown | DS1425 | `0040 00031380` – `0040 00053FFF` |",
            "| Crown | DS1425 | `0040 00031380` – `0040 00053FFF` |\n"
            "| Force 2003.5 | as Ruby 2 | the same program as Ruby 2 V11.00 |\n"
            "| Force 2005, 2005.5 | as Jade | the same programs as Jade V14.00 and Jade 2 V15.10 |\n"
            "| Force 2003, 2004, 2006; ION 2006 | probably as their Maxx sibling | no copy of their program to check |\n"
            "| Force / ION 2007 and later | no range | but the button must be a DS1995 or DS1996 big enough for the key |")
    # games and settings memory
    s = rep(s, "\nThe USA Crown key enables 101 games, 13 of them at 2 credits.\n",
            "\nThe USA Crown key enables 101 games, 13 of them at 2 credits.\n" + GAMES_FORCE_MD)
    s = rep(s, "  an old SQLite version 2 file XOR-scrambled with a 4-byte pattern. Reading its rows is still to do.\n",
            "  an old SQLite version 2 file XOR-scrambled with a 4-byte pattern. Reading its rows is still to do.\n"
            + NVRAM_FORCE_MD)
    return s


# ----------------------------------------------------------------------------- keyinfo.md

AGENT_PRODUCTS = """### Product lines and releases [Docs/18, Docs/19, Docs/21]

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

"""

AGENT_GEN4_STATES = """### Gen 4 key-only switches on real keys [verified from the dumps, P21c]

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

"""


def agent(s):
    s = rep(s, '\n## 1. The physical key', '\n' + AGENT_PRODUCTS + '## 1. The physical key')
    s = rep(s, '\n### What each slot does, and who sets it', '\n' + AGENT_GEN4_STATES + '### What each slot does, and who sets it')
    s = rep(s, '| 45 | USA-STD (!) | Sapphire SA305945 | — |',
            '| 45 | USA-STD (!) | Sapphire SA305945 (Maxx Sapphire key with the Force model number, §0) | — |')
    return s


# ----------------------------------------------------------------------------- research page

PRODUCTS_HTML = """
  <section id="products">
    <div class="sec-head"><h2>Products</h2><span class="tag">Maxx / XL, Force and ION on one code base</span></div>
    <p>Merit sold three lines that all use these keys: <strong>XL / MAXX</strong> (1997–2005),
    <strong>Force</strong> (2002–2011, its own cabinet and motherboard) and <strong>ION</strong>
    (2006–2014), plus Touch2Play and Firefly on the ION software. They are not separate systems:
    <strong>Force and ION run the Maxx software of the same year</strong> and the key decides which
    product the machine becomes.</p>
    <div class="tbl"><table>
      <thead><tr><th>Key era</th><th>XL / MAXX</th><th>Force</th><th>ION and others</th><th>Button</th></tr></thead>
      <tbody>
        <tr><td>Gen 1 (DOS)</td><td>XL R1 → MAXX Double Diamond</td><td>—</td><td>—</td><td>DS1991</td></tr>
        <tr><td>Gen 2</td><td>Titanium, Emerald (DOS); Ruby 2</td><td>Force 2002 (DOS), 2003 / 2003.5</td><td>—</td><td>DS1991 → DS1425</td></tr>
        <tr><td>Gen 3</td><td>Sapphire, Jade, Crown</td><td>Force 2004, 2005 / 2005.5, 2006</td><td>ION 2006</td><td>DS1425</td></tr>
        <tr><td>Gen 4</td><td>—</td><td>Force 2007–2011</td><td>ION 2007–2014, Touch2Play 2013, Firefly 2010</td><td>DS1995 / DS1996</td></tr>
      </tbody>
    </table></div>
    <ul class="plain">
      <li><strong>Same programs.</strong> Force 2003.5 is byte-for-byte Maxx Ruby&nbsp;2 V11.00, Force 2005
      is Jade V14.00 and Force 2005.5 is Jade&nbsp;2 V15.10.</li>
      <li><strong>Same keys, nearly.</strong> Up to 2006 a Force or ION key uses its Maxx cousin's cipher;
      only the signature and the password recipe differ. Force 2003 keys share Ruby&nbsp;2's passwords
      <em>and</em> signature — they differ only in the model number and the games listed.</li>
      <li><strong>The key picks the product.</strong> DS1991-era Force and ION keys enable the Force-only
      game 0x44 (Bowling), which the shared software checks against the motherboard. From 2007, key-only
      switches turn the same software into Touch2Play, KidZpace, MindSpark, UAE-prize or lease machines —
      all locked off on standard keys.</li>
      <li><strong>Force and ION split at the signature.</strong> 2007–2010 Force and ION keys share cipher
      and layout; ION 2008's signature is Force 2008's reversed. Force ended in 2011; ION got new cipher
      constants every year after.</li>
      <li><strong>An upgrade key.</strong> <code>SA305945</code> is a genuine Maxx Sapphire key (Maxx
      passwords and signature) carrying the Force model number SA3059 and the Force 2004 game list —
      probably a "MAXX-to-FORCE" upgrade key, a phrase Merit's own help text uses. Inferred.</li>
    </ul>
  </section>
"""

GEN4_ANATOMY_HTML = """    <h3>From 2007: one plain memory block</h3>
    <p>Force 2007 and ION 2007 onward use a DS1995 (2&nbsp;KB) or DS1996 (8&nbsp;KB) memory button: no
    compartments, <strong>no passwords</strong>, one 1024-byte block behind a six-byte keystream keyed by
    the serial and a per-year constant, closed by a 16-bit checksum. It holds the part number, a Unix
    timestamp, territory text and country code, the MegaNet server and web-portal addresses, the
    signature, six coin channels, a price byte for each of 300 games, 120 option bytes and a 300-bit game
    list (field map under "The 2007 key format").</p>
"""

OPTIONS_FORCE_HTML = """    <h3>What Merit decides on a Force / ION key</h3>
    <p>On the 2007-and-later software 18 slots have no operator control. Their states on every genuine
    Force / ION key in the collection (0 locked off, 1 forced on, 3 operator may change):</p>
    <div class="tbl"><table>
      <thead><tr><th>Slot</th><th>Key-only switch</th><th>Force 07 · 08 · 09 · 10 · 11</th><th>ION 07 · 08 · 09 · 14</th></tr></thead>
      <tbody>
        <tr><td class="mono">0x14</td><td>TournaMAXX (menu choice on ION, but key-gated)</td><td class="mono">1 · 3 · 1 · 1 · 1</td><td class="mono">3 · 3 · 3 · 3</td></tr>
        <tr><td class="mono">0x0B</td><td>TournaMAXX allowed in free play</td><td class="mono">1 · 1 · 1 · 1 · 1</td><td class="mono">1 · 1 · 1 · 0</td></tr>
        <tr><td class="mono">0x0C</td><td>TournaMAXX price differs from regular</td><td class="mono">1 · 1 · 1 · 1 · 1</td><td class="mono">1 · 1 · 1 · 1</td></tr>
        <tr><td class="mono">0x0F</td><td>Rental mode: 5-row price table</td><td class="mono">1 · 1 · 1 · 1 · 1</td><td class="mono">1 · 1 · 1 · 1</td></tr>
        <tr><td class="mono">0x10</td><td>Touch2Play mode</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x59</td><td>KidZpace mode</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x43</td><td>MindSpark mode</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x5D</td><td>UAE prize mode</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x47</td><td>Premiere tournament terminal</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x31</td><td>Lease mode (time bomb)</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x2F</td><td>Senior mode</td><td class="mono no">0 · 0 · 0 · 0 · 0</td><td class="mono no">0 · 0 · 0 · 0</td></tr>
        <tr><td class="mono">0x39</td><td>Prize Zone</td><td class="mono">3 · 3 · 3 · 3 · 0</td><td class="mono">3 · 3 · 3 · 0</td></tr>
        <tr><td class="mono">0x52</td><td>Operator setup from Six Stars</td><td class="mono">3 · 3 · 3 · 3 · 0</td><td class="mono">3 · 3 · 3 · 0</td></tr>
        <tr><td class="mono">0x5C</td><td>Allow coin-in table changes</td><td class="mono">1 · 1 · 1 · 1 · 1</td><td class="mono">1 · 1 · 1 · 1</td></tr>
      </tbody>
    </table></div>
    <p>The product variants are key-only and off on every standard key: a Touch2Play, KidZpace or
    MindSpark machine is the same software with a different key. TournaMAXX is never locked off on a Force
    or ION key — forced on for Force, the operator's choice on ION — unlike the Maxx Crown keys. (The
    remaining four key-only slots: MegaNet without TournaMAXX and the download selector are off, quick
    pricing on, alternate language selection operator-changeable.)</p>
"""

GAMES_FORCE_HTML = """    <h3>Force and ION games</h3>
    <p>Force game tables start smaller than their Maxx siblings (Force 2003: 102 games, Force 2004: 146)
    and then match the Maxx software they share (Force 2005 / 2005.5: 173 / 180). The 2007-and-later keys
    have room for 300 games and keep the Maxx numbering — 0 is still Solitaire, 4 Match 'Em Up, and a
    retired game keeps its number (<code>g_match_removed</code>). Genuine keys enable 137 (Force 2009) to
    200 (ION 2014) games; the 2007 keys, which predate the on/off list, enable a game by giving it a
    price. The only Force 2006 image carries a stale copy of Force 2003's table, so Force 2006 and ION 2006
    keys are named from Crown's.</p>
    <p><strong>Settings memory.</strong> Up to 2006 Force keeps the same <code>nvram.dat</code> as the
    Maxx software it shares. From 2007 the settings moved to XML (<code>/merit/settings.xml</code>) and
    SQLite, and <code>nvram.dat</code> shrank to 5,792 bytes — not mapped yet.</p>
"""


def page(s):
    # findings
    s = rep(s, 'Emulator test: Diamond, Emerald and Jade keys relabelled with the made-up part number SA999901 all boot normally.</p>',
            'Emulator test: Diamond, Emerald and Jade keys relabelled with the made-up part number SA999901 all boot normally. '
            'The same rule covers the DS1991-era Force and ION keys, which use their Maxx cousin\'s cipher; on the 2007-and-later keys '
            'the gate is the signature at <code>0x0F5</code> plus a checksum (part-number edits there were not boot-tested).</p>')
    s = rep(s, 'mean the same thing on XL, MAXX and Crown keys. The key also stores the territory name and, from Sapphire on, a country code.</p>',
            'mean the same thing on XL, MAXX, Crown, Force and ION keys (every Force key and ION up to 2010 is 01; ION 2011–2013 use 09 USA-VER1). '
            'The key also stores the territory name and, from Sapphire on, a country code.</p>')
    s = rep(s, 'The XL and DOS MAXX keys carry the same table; Sapphire keys have 88 slots.</p>',
            'The XL and DOS MAXX keys carry the same table; Sapphire keys have 88 slots. On Force and ION keys TournaMAXX is never locked off, '
            'and from 2007 the key also chooses the product variant: Touch2Play, KidZpace, MindSpark, UAE prize and lease mode are key-only switches, '
            'off on every standard key.</p>')
    s = rep(s, '<span class="pill ok">Confirmed</span> Every Linux build, no DOS build.</div>',
            '<span class="pill ok">Confirmed</span> Linux builds 2002–2006, Force included; dropped in 2007.</div>')
    s = rep(s, 'A failure shuts the game down at boot with "KEY RANGE MISMATCH". keyflasher can rewrite contents but not that serial.</p>',
            'A failure shuts the game down at boot with "KEY RANGE MISMATCH". keyflasher can rewrite contents but not that serial. '
            'Force 2003.5 and 2005 / 2005.5 run the very same programs, so the same ranges apply; the 2007-and-later Force and ION software '
            'has no range check, only a button-type rule.</p>')
    # products section + toc
    s = rep(s, '\n  <section id="anatomy">', PRODUCTS_HTML + '\n  <section id="anatomy">')
    s = rep(s, '<a href="#anatomy">Key anatomy</a>', '<a href="#products">Products</a><a href="#anatomy">Key anatomy</a>')
    # key anatomy
    s = rep(s, '<span class="tag">DS1991 MultiKey, 256 bytes</span>',
            '<span class="tag">DS1991 MultiKey 256 bytes, then a 1 KB block from 2007</span>')
    s = rep(s, '<tr><td>Gen 2</td><td>Titanium, Emerald, Ruby</td>', '<tr><td>Gen 2</td><td>Titanium, Emerald, Ruby; Force 2002, 2003</td>')
    s = rep(s, '<tr><td>Gen 3</td><td>Sapphire, Jade, Crown</td><td>DATA0[0x28..0x2F]</td><td class="mono">1234567890abcdef · 8723879fe2432498</td></tr>',
            '<tr><td>Gen 3</td><td>Sapphire, Jade, Crown; Force 2004–2006, ION 2006</td><td>DATA0[0x28..0x2F]</td>'
            '<td class="mono">1234567890abcdef · 8723879fe2432498 · 8624879f… · 342190fa…</td></tr>\n'
            '        <tr><td>Gen 4</td><td>Force 2007–2011, ION 2007–2014</td><td>block 0x0F5</td><td>one per release (Force/ION table below)</td></tr>')
    i = s.index('<section id="anatomy">')
    j = s.index('</section>', i)
    s = s[:j] + GEN4_ANATOMY_HTML + '  ' + s[j:]
    # acceptance
    s = rep(s, '<tr><td>Crown</td><td>Crown</td><td class="mono">12 78 37 F3</td><td class="mono">8723879f e24324 98/87</td></tr>',
            '<tr><td>Crown</td><td>Crown</td><td class="mono">12 78 37 F3</td><td class="mono">8723879f e24324 98/87</td></tr>\n'
            '        <tr><td>Force 2002 (DOS)</td><td>Force 2002 (Ruby-style init)</td><td class="mono">73 3C AA E7</td><td class="mono">dd621043 21100293</td></tr>\n'
            '        <tr><td>Force 2003 / 2003.5</td><td>Ruby (identical)</td><td class="mono">61 E3 5A 13</td><td class="mono">de621043 21100293</td></tr>\n'
            '        <tr><td>Force 2004</td><td>Force 2004</td><td class="mono">A7 67 9A AA</td><td class="mono">12345678 90abcdef</td></tr>\n'
            '        <tr><td>Force 2005 / 2005.5</td><td>Force 2005</td><td class="mono">FF 35 5A 4B</td><td class="mono">8723879f e2432498</td></tr>\n'
            '        <tr><td>Force 2006</td><td>Force / ION 2006</td><td class="mono">12 78 37 F3</td><td class="mono">8624879f e2432498</td></tr>\n'
            '        <tr><td>ION 2006</td><td>Force / ION 2006</td><td class="mono">12 78 37 F3</td><td class="mono">342190fa 11880410</td></tr>\n'
            '        <tr><td>Force / ION 2007–2014</td><td>none — no passwords</td><td>per-year keystream</td><td>per release, plus a 16-bit checksum</td></tr>')
    s = rep(s, '<code>cmp eax,1; jbe …</code>.</p>',
            '<code>cmp eax,1; jbe …</code>.</p>\n    <p>Force and ION reuse the Maxx cipher of their year but carry their own password recipe, so on the '
            'DS1991-era hardware a Force key cannot be read as a Maxx key — except Force 2003, whose recipe and signature are '
            'Ruby&nbsp;2\'s. The password generators reproduce the passwords stored in 48 of the 49 dumps across both lines.</p>')
    # territory
    s = rep(s, '<th>Country code (Gen 3)</th>', '<th>Country code (Gen 3 / 2007+)</th>')
    s = rep(s, '<tr><td class="mono">01</td><td>USA-STD</td><td>every generation</td>',
            '<tr><td class="mono">01</td><td>USA-STD</td><td>every generation; every Force key, ION 2006–2010</td>')
    s = rep(s, '<tr><td class="mono">09</td><td>USA-VER1</td><td>MAXX 2K</td>', '<tr><td class="mono">09</td><td>USA-VER1</td><td>MAXX 2K; ION 2011–2013</td>')
    s = rep(s, '<tr><td class="mono">33</td><td>CAN-VER2 / USA-CANV2</td><td>Diamond, Jade, Crown</td><td class="mono">1</td></tr>',
            '<tr><td class="mono">33</td><td>CAN-VER2 / USA-CANV2</td><td>Diamond, Jade, Crown</td><td class="mono">1</td></tr>\n'
            '        <tr><td class="mono">45</td><td>USA-STD</td><td>one Maxx Sapphire key with a Force model number (see Products)</td><td>—</td></tr>')
    s = rep(s, '"Crazy-Golf", "Race Cards", "21 Pontoon").</p>',
            '"Crazy-Golf", "Race Cards", "21 Pontoon").</p>\n    <p>The 2007-and-later keys keep the territory as text plus a country code, a New Jersey exception '
            'number and the MegaNet server address for the market (<code>us.accessmerit.com</code>). The only ION 2014 key in the collection '
            'contradicts itself: country code 1 (Canada) with territory text <code>USA-STD</code>.</p>')
    # option locks: Force/ION per-key states after the Force 2007-2011 note
    i = s.index('<h3>How the slots changed across releases</h3>')
    s = s[:i] + OPTIONS_FORCE_HTML.lstrip(' ') + '\n    ' + s[i:]
    # games + settings memory: end of the Force / ION section
    i = s.index('<section id="forceion">')
    j = s.index('</section>', i)
    s = s[:j] + GAMES_FORCE_HTML + '  ' + s[j:]
    return s


def main():
    for path, fn in ((HUMAN, human), (AGENT, agent)):
        s = open(path, encoding='utf-8').read()
        if SENT_MD in s:
            print(os.path.basename(path), 'already updated, skipped')
            continue
        s = fn(s).rstrip('\n') + '\n\n' + SENT_MD + '\n'
        open(path, 'w', encoding='utf-8').write(s)
        print(os.path.basename(path), 'updated')
    s = open(PAGE, encoding='utf-8').read()
    sent = '<!-- p21c: Force / ION woven through findings, products, anatomy, acceptance, territory, options, games -->'
    if sent in s:
        print('megatouch-security-keys.html already updated, skipped')
    else:
        s = page(s).rstrip('\n') + '\n' + sent + '\n'
        open(PAGE, 'w', encoding='utf-8').write(s)
        print('megatouch-security-keys.html updated')
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'p20-update-share.py')],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(r.stderr)


if __name__ == '__main__':
    main()
