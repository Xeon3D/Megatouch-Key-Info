# Megatouch security keys, explained

A guide to the Dallas iButton keys used by Merit Megatouch machines, from the XL (1997) all the way to
ION 2014 - that is both the Maxx/XL line and the Force / ION line, plus Touch2Play and Firefly. It explains what is on a key, how a machine decides whether to accept it, what the key controls,
and how the machine's settings memory relates to it. Everything here comes from reading the original
game software, decrypting real key dumps and testing in the MegaPPBox emulator. Where something is a
best guess rather than proven, the text says so.

---

## The short version

- **The model number does not pick the software.** A key's part number (`SA3048`, `SA3511`, …) is never
  checked. What matters is whether the software can **unlock** the key (passwords), **decode** it
  (cipher) and find the right **signature** inside. Several part numbers work on one version because
  Merit sold several products with identical key contents. We proved this in the emulator: keys
  relabelled with the made-up number SA999901 booted normally.
- **The last two digits are the territory**, and the numbering is the same on every generation
  (01 = USA standard, 33 = Canada, 05 = Portugal, …).
- **Merit locked features on the key.** Every key up to 2006 carries 80 two-bit switches (88 on
  Sapphire), Maxx, XL, Force and ION alike; the Force/ION keys from 2007 carry 120, one byte each. Each feature can be forced off,
  forced on, or left to the operator. TournaMAXX is switch 0x14: forced on in the Jade keys, locked off
  in the Crown keys. **Every switch now has its real name**, read out of the game software itself.
- **Force and ION are the same software as the Maxx of the same year.** Force 2002-2006 and ION 2006
  keys use byte-identical scrambling to their Maxx counterparts; only the signature differs. One
  program really does serve several products - Maxx Ruby 2 and Force 2003.5 share a game binary, and
  the key is what decides which product the machine becomes. On the 2007-and-later keys Merit also
  uses the key to turn the same software into Touch2Play, KidZpace or MindSpark machines.
- **In 2007 Merit changed the button.** Force 2007 and ION 2007 onward dropped the DS1991 MultiKey for
  a plain memory button with **no passwords at all** - just a 1 KB block behind a weak scrambler.
- **The Linux machines only accept keys from serial ranges Merit bought.** Ruby 2 through Crown check
  the button's factory serial number. The older DOS machines don't check it at all.

---

## 1. What a key is

Up to 2006 the key is a **Dallas DS1991 MultiKey** iButton: a small steel button with a 1-Wire chip
inside. Later machines use the **DS1425**, which works the same way but reports a different family code
(0x82 instead of 0x02).

From **Force 2007 and ION 2007** Merit switched to an ordinary memory button - a **DS1995** (2 KB,
family 0x0A) for ION 2007 and a **DS1996** (8 KB, family 0x0C or 0x8C) for everything after. These have
no protected compartments and no passwords whatsoever: the whole key is a single 1024-byte block
sitting in plain memory, and the only thing between a reader and the contents is the scrambler. The
software picks which layout to expect purely from the button's family code.

Inside are:
- **three protected compartments** ("subkeys"). Each has an 8-byte name, an 8-byte password and 48
  bytes of data;
- a 64-byte **scratchpad** (unprotected).

Two things to know about it:
- **A wrong password does not cause an error.** The button just returns random-looking bytes. A
  machine "rejects" a key by reading garbage and finding nothing sensible.
- **Every button has a unique, laser-burned serial number** (the ROM ID) that can never be changed. It
  has three parts: a family code, a 6-byte serial and a checksum. Merit used this serial to tie each
  key's encryption to that one physical button.

Key dumps made with Nicholas Navaroli's **keyflasher** are 264-byte files named like
`MCROWN_full_6D000000CB053702`: the 256-byte encrypted contents followed by the serial. Note that the
serial is printed backwards: checksum first, family code last. `…02` is a DS1991 and `…82` a DS1425.

---

## 2. The products and their keys

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

---

## 3. How the contents are protected

Two layers protect each key.

**Passwords.** Each compartment has its own password, computed from the button's serial using a recipe
specific to each product family. A machine can only open keys whose password recipe it knows. This is
what *really* separates one product's keys from another's. Even products that share everything else
(XL Gold and MAXX 2K, Platinum and Diamond, Titanium and Emerald) have different password recipes.
Merit had a sense of humour here: some of the "secret" constants are just bytes of x86 machine code.

**Scrambling.** The data is scrambled byte by byte with a simple rolling cipher. Each byte is mixed
with four bytes derived from the serial, then shifted by a counter that advances each byte. The
starting values and step size differ per product family:

| Family | Used by |
|---|---|
| M1 (no scrambling, one fixed password) | XL R1, Super 5000, XL 6000, MAXX (V3.06) |
| XL Gold / 2K | XL Gold, MAXX 2K, 2K Plus |
| Platinum / Diamond | XL Platinum, Double Platinum, MAXX Diamond, Double Diamond |
| Titanium / Emerald | XL Titanium, Titanium 2, MAXX Emerald, Emerald 2 |
| Ruby | MAXX Ruby 2 |
| Sapphire | Sapphire, Sapphire 2 |
| Jade | Jade, Jade 2, **Force 2005** |
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
caught at boot.

keyflasher handles every family except **Crown**, which was recovered for this project. The two clues
were a known Crown key and the Crown game code. The result decodes the USA Crown key to the expected
contents with no differing bytes.

Because both layers depend on the serial, **you cannot copy a key's dump onto another button and have
it work**. It has to be re-encrypted for the new button's serial, which this project's tools can do.

---

## 4. What is on a key

Every key starts with three short labels:
- **Part number**: `SA` + four-digit model + two-digit territory, e.g. `SA304201` = model 3042
  (MAXX Diamond), territory 01 (USA).
- **Programming date**: `MM/DD/YY`.
- **Revision**: `R00`, `R01`, …

The rest changed over the years, in four generations.

**Older keys (XL through Double Diamond):**
- the signature (8 bytes at the start of the data);
- coin settings;
- a region code (USA, Europe, Canada);
- a game table: which games are on, and on most releases each game's price;
- the same 80 feature switches as later keys (section 7);
- the territory name (`USA-STD`, `CAN-VER2`, `PORTUGAL`, …);
- currency names in the scratchpad.

**Titanium, Emerald and Ruby keys** (and Force 2002 / 2003): the same structure with new signature
values. Ruby 2 and Force 2003 list the games to switch *off* instead.

**Sapphire, Jade and Crown keys** (and Force 2004-2006, ION 2006) were reorganised:
- **TournaMAXX settings**: game cost, prize mode and prize rate;
- **default languages**;
- **coin settings** for 6 channels (coins, credits and meter pulses);
- the **signature**, now in the middle of the first compartment;
- the **price list**: groups of games each with a price, plus a default price for the rest;
- the **territory name** and a **country code** (0 USA, 1 Canada, 3/4 UK-style game renames such as
  "Crazy-Golf" and "21 Pontoon");
- **80 feature switches** (section 7);
- a **game list**: one on/off bit for each of up to 224 games;
- **currency names** such as `$10` and `59¢` in the scratchpad.

**Force 2007 and ION 2007 onward** were reorganised again, into one 1 KB block:
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

---

## 5. How a machine decides to accept a key

A version accepts a key when **all** of these hold:

1. it knows a **password recipe** that opens the key;
2. it can **unscramble** the contents;
3. the contents carry that version's **signature**;
4. on the Linux machines (Ruby 2 to Crown), the button's **serial is in the accepted range**
   (section 8).

On the Force and ION machines the test is identical, with their own signature values. Because Force
and ION of the same year share a cipher, the signature is the only thing separating them:

| Year | Force | ION |
|---|---|---|
| 2005 | `8723879FE2432498` (same as Maxx Jade) | - |
| 2006 | `8624879FE2432498` | `342190FA11880410` |
| 2007 | `64563647452C2837` | `42367123EF235334` |
| 2008 | `E72136AB30C92156` | `5621C930AB3621E7` (the Force value reversed) |
| 2009 | `6874328C954F6743` | `213566732E476A32` |
| 2010 | `CFB4A9611BB72003` | `29342DA908FBC6DE` |
| 2011 | `90322BBAA4370CFE` | - |
| 2014 | - | `93E41C6E20911B9B` |

The ION 2014 program does one more thing while checking a key: it **reads its own program file** from
disk and inspects it, an anti-tamper measure sitting inside the key check itself.

**What does *not* matter is the model number.** The software compares the part number only with the
copy it saved last time. If they differ, you see "Dallas Key mismatch, re-initing NVRAM": the machine
wipes its settings and carries on. That's why several model numbers work on one version (M1 SA3022 and
SA3031; Ruby 2 SA3056 and SA3061; Crown SA3511 and SA3513). They are different products or territories
with the same key family.

**Tested:** Diamond, Emerald and Jade keys with only their part number changed to the non-existent
SA999901 booted normally in the emulator. So did an Emerald key relabelled with a Titanium part number.

### The signatures

| Version | Signature (hex / text) |
|---|---|
| XL R1 | `11223344 55667788` |
| XL Super 5000 | `QRSTUfw` + 0x88 |
| XL 6000 → MAXX Double Diamond | `PRSTUfw` + 0x89 |
| XL Titanium | `e8420886 67400282` (or the Emerald signature on a MAXX cabinet) |
| MAXX Emerald, Emerald 2 | `dd621043 21100293` |
| Ruby 2 | `de621043 21100293` |
| Sapphire, Sapphire 2 | `12345678 90abcdef` |
| Jade, Jade 2, Crown | `8723879f e2432498` (Crown also accepts one ending `87`) |

### One program, two cabinets
From XL Gold onward each DOS release runs on both **XL** and **MAXX** cabinets, and each carries **two
password recipes**, one per cabinet. The startup files decide which applies:
- `SET XLSYSTYPE=MAXX` selects MAXX;
- on XL Gold and 2K, `SET XLNEWIO=YES` selects the newer I/O board.

So the key must match the **cabinet**, not just the software:
- XL Titanium software on a MAXX cabinet wants an Emerald key;
- XL Titanium software on an XL cabinet wants a Titanium key;
- Diamond software on an XL cabinet wants a Platinum key.

Emerald's "XL" recipe pairs with no real key, so Emerald was effectively MAXX-only, with Titanium as
its XL twin.

Merit also left a development switch: `XLKEYFILE=<file>` makes the DOS software read the key from a file
instead of the button.

### Maxx or Force
The Linux software is shared between the MAXX and the Force/ION products. The key decides which one the
machine becomes:
- The software checks whether it is running on the Force motherboard (Intel 810 with CMI8738 sound).
- The key carries a matching flag: the on/off bit for game 0x44, **Bowling**, which is a Force-only
  game.
- If the two disagree, the signature check fails and the machine crashes on purpose.
- In practice, a Force key won't boot a MAXX and a MAXX key won't boot a Force.

The software also refuses to run at all on a motherboard it doesn't recognise. It knows four
Merit-approved boards.

---

## 6. Territories

The last two digits of the part number:

| Digits | Name on the key | Seen on |
|---|---|---|
| 01 | USA-STD | almost everything, including every Force key and ION up to 2010 |
| 04 | S EUROPE | MAXX 2K |
| 05 | PORTUGAL | MAXX 2K, Ruby 2 |
| 09 | USA-VER1 | MAXX 2K; ION 2011, 2012, 2013 |
| 14 | USA-VER2 | original MAXX |
| 33 | CAN-VER2 | Diamond, Jade, Crown |

A territory is really a bundle of defaults: coin values, currency names, default language, country code.
Any territory name starting with **NJ** switches the machine into New Jersey mode in every version.
The 2007-and-later keys keep the territory as text too, next to a country code, a New Jersey
exception number and the MegaNet server address for that market (`us.accessmerit.com` on the USA
keys). The only ION 2014 key in the collection contradicts itself here: country code 1 (Canada)
with the territory text `USA-STD`.

Two oddities:
- One Sapphire key says USA-STD but ends in 45. It is a Maxx Sapphire key carrying the Force model
  number and game list - probably a Maxx-to-Force upgrade key (section 2).
- One key, `SA002001`, has a signature no software version uses (probably a prototype or other-product
  key).

---

## 7. The feature switches

Every key up to 2006 carries 80 switches of two bits each (Sapphire keys 88), the XL and DOS MAXX
keys included; Force/ION keys from 2007 carry 120, a whole byte each. The meanings are the same:

| Value | Meaning |
|---|---|
| 0 | locked **off**: the feature is hidden |
| 1 | locked **on** |
| 2 | operator can change it; starts off |
| 3 | operator can change it; starts on |

The machine stores the operator's choice for each switch. It only uses that choice when the key allows
the operator to change the switch; otherwise the key wins.

**All of them are now named.** The later Force/ION programs carry a built-in table translating each
switch number into its internal name, and it was lifted out whole. The same table appears unchanged in
ION 2011, ION 2014, Touch2Play 2013 and Firefly 2010, and it agrees with everything previously worked
out by hand for Crown - so the first 80 names apply to the Sapphire, Jade and Crown keys as well. A
sample of the more interesting ones:

| # | Switch |
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

The full list of 120 is in `Docs/19`, and the key editor shows every switch by name.

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
still take away.

**TournaMAXX is switch 0x14.** On the machines up to Crown no operator menu can change it, so
only the key decides:

| Key | TournaMAXX |
|---|---|
| Jade (both keys examined) | forced on |
| Crown USA and Canada | locked off |
| Force 2005, 2007, 2009, 2010, 2011 | forced on |
| Force 2006, 2008; ION 2006 - 2014 | operator may change it |

That matches the folklore that "TournaMAXX had to be enabled in the Crown key". The Crown keys also lock
off every MegaNet online service the Jade keys allow: MegaWeb, Prize Zone, premium erotic, E-Channel,
Hot Topics, Operator Web, ShowTenders and Fantasy Sports.

### What Merit decides on a Force / ION key

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

### What the switches do on Crown

Of Crown's 80 switches:
- **53** are **operator settings** the key can lock or unlock;
- **10** are **key-only**: no menu can change them;
- **1** is runtime state, set by the game itself;
- **1** is set by the MegaNet server;
- **15** are unused by Crown. Some were used by older versions.

Key-only switches:
- **0x0B** free-play idle adverts;
- **0x0F** pay-per-time;
- **0x14** TournaMAXX;
- **0x1D** an internal flag the game only reads;
- **0x24** Merit-thon tournament bookkeeping;
- **0x2F** demo mode;
- **0x31** lease mode ("time bomb");
- **0x3F** New Jersey rental coin setup;
- **0x43** scrolling marquee;
- **0x47** hiding the TournaMAXX ranking screens.

Operator settings, by area:

| Area | Switches |
|---|---|
| Game rules | Free game, allow continue, bonus replay, trivia options, Photo Hunt hints, Checkerz rules, easy mode, Tri-Towers face-up cards, continue bonus round |
| Content | Nudity and nudity level, erotic games, strip-club rewinds, moan sounds, premium erotic, card-back advertising |
| Money | Coin-op/rental mode, price display, free play, promo credits, Merit Money |
| Machine | Player-selectable language, language flags, auto-clear high scores, no names in high scores, theft deterrent, fan time, attract sounds, educational attract, senior play speed, Mega-Link, Six Stars shortcut |
| Online | MegaWeb (and its filter), Prize Zone, E-Channel, Hot Topics, Operator Web, ShowTenders, Fantasy Sports, TouchTunes |

How the switches changed across releases:
- **Sapphire** added the online services.
- **Jade** added pay-per-time, lease mode, demo mode, the marquee, Operator Web, ShowTenders, Fantasy
  Sports and card-back ads.
- **Jade 2** added senior play and the TournaMAXX-ranking switch.
- After **Sapphire 2**, the "six-star access" switches went away. They chose what the six-star
  operator shortcut could reach: high scores, bookkeeping, volume, calibration, TournaMAXX update.

The full slot-by-slot table is in `Docs/04-territory-options.md`, and what each switch does, release
by release, in `Docs/21-key-tool-options-games.md`.

---

## 8. Serial-number ranges (Linux machines, 2002-2006 only)

From Ruby 2 on, the software reads the button's factory serial and refuses to run ("KEY RANGE MISMATCH")
unless it falls inside the batches Merit bought:

| Version | Button type | Accepted serials |
|---|---|---|
| Ruby 2 | DS1425 (0x82) | `0040 00000000` – `0040 000189C1` |
| | DS1991 (0x02) | two specific Merit batches around `00B0xxxx` |
| Sapphire, Sapphire 2 | DS1425 | `0040 00010680` – `0040 00024000` |
| Jade, Jade 2 | DS1425 | `0040 00022917` – `0040 00053FFF` |
| Crown | DS1425 | `0040 00031380` – `0040 00053FFF` |
| Force 2003.5 | as Ruby 2 | the same program as Ruby 2 V11.00 |
| Force 2005, 2005.5 | as Jade | the same programs as Jade V14.00 and Jade 2 V15.10 |
| Force 2003, 2004, 2006; ION 2006 | probably as their Maxx sibling | no copy of their program to check |
| Force / ION 2007 and later | no range | but the button must be a DS1995 or DS1996 big enough for the key |

**The 2007-and-later machines dropped this check entirely.** Once the scrambling itself was keyed to
the button's serial a range check became redundant: a key written for one button simply turns to
garbage on another and fails its signature and its checksum. Every genuine Force/ION key is still from
a Merit batch, but nothing in the software looks.

What this means in practice:
- **A blank DS1991 re-flashed with Jade or Crown data will not boot**, even though it decodes
  perfectly. The serial is the wrong type and outside the range, and keyflasher cannot change a serial.
- Older Jade keys (serials below 0x31380) work on Jade but not on Crown.
- The **DOS machines have no serial check at all**.

Other protections around this check:
- The machine re-reads the serial while running and shuts down ("SECURITY KEY MISMATCH") if the key
  changes or disappears for more than 10 checks in a row.
- A debugger trap catches anyone setting breakpoints on the check. It logs the joke message "Not Jersey
  Key, Not Dallas Key, must be Florida Key".

### The Canadian Crown key
The `CAN-VER2` Crown dump in the collection is on a DS1991 button (serial `…CB0537`, type 0x02). By the
rules above, Crown would shut it down at boot. Its passwords are exactly what keyflasher produces for
that button, so it was most likely Crown data copied onto a blank. A **re-serialised copy** for emulator
use is in `analysis/p17/MCROWN_full_8900400004CA0282`. It has the same contents on a made-up DS1425
serial inside Crown's range. It can't be put on a real DS1991, whose serial is fixed.

---

## 9. Games and prices

Every version has a game table file, and **a game's number is its position in that file**:
- DOS: `C:\MERIT2\DATA\GAMEDATA.DAT`;
- Linux: `/usr/local/share/merit/config/gamedata.dat`.

The table grew from 51 games (MAXX 3.06) through 84 (Emerald) to 195 (Crown), and to roughly 300 on
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

The USA Crown key enables 101 games, 13 of them at 2 credits.

On the Force side the game tables are smaller than their Maxx siblings at first (Force 2003: 102 games,
Force 2004: 146) and then the same as the Maxx software they share (Force 2005 / 2005.5: 173 / 180). The
2007-and-later keys have room for 300 games, and their numbering carries straight on from the Maxx one:
game 0 is still Solitaire and 4 is still Match 'Em Up, with retired games keeping their number (the ION
table calls it `g_match_removed`). Genuine keys enable 137 (Force 2009) to 200 (ION 2014) games; on the
2007 keys, which predate the on/off list, a game is on when it has a price. The only Force 2006 disk
image carries a stale copy of Force 2003's game table, so Force 2006 and ION 2006 keys are named from
Crown's.

---

## 10. The machine's settings memory (NVRAM)

Each machine keeps a settings file. On DOS it is `C:\NVRAM.DAT` or battery-backed memory on the I/O
board. On Linux it is `/var/config/nvram.dat`. It starts with a small header:
- a "valid" flag;
- a **copy of the key's part number**: a different key causes the "Dallas Key mismatch" reset;
- a **layout number**: a different software layout also causes a reset.

The rest holds coin settings copied from the key, the operator's choice for each of the 80 switches, and
the bookkeeping. The layout changes with almost every release. Releases with the same layout number
share it, for example MAXX 2K and XL Gold, or Emerald and Titanium.

What the decoder in this project can read:
- **DOS:** total, free and free-play credits (current and lifetime); coin books for six coin channels;
  security PIN; adult-content hours; volume; tournament counters; TouchTunes credits.
- **Per-game books on DOS:** for every game, its price, current and lifetime credits, shortest, average
  and longest play time, and number of 1-, 2-, 3- and 4-player games. Example, from a played Emerald 2:
  Eleven Ball 14,353 lifetime credits, Boxxi 12,225, Funky Monkey 5,385.
- **Linux:** about 30 named settings per release, including:
  - six-star and security PINs (Merit's factory six-star PIN is 4123);
  - value of a credit;
  - current credits;
  - volume and language;
  - Merit Money and promo schedules;
  - pay-per-time rates;
  - TouchTunes and TournaMAXX credits;
  - location number.
- **Linux credit books:** these live in a small disguised database, `/var/config/amusement.db`. It is
  an old SQLite version 2 file XOR-scrambled with a 4-byte pattern. Reading its rows is still to do.

**Force and ION.** Up to 2006 the Force machines keep the same `nvram.dat` as the Maxx software they
share. From 2007 the settings moved into XML files (`/merit/settings.xml`) and an SQLite database, and
`nvram.dat` shrank to 5,792 bytes; that layout has not been mapped yet.

---

## 11. Tools in this workspace

All in `scripts/`, run with Python:

| Tool | Does |
|---|---|
| **`mtkeytool.py`** | **the key editor: a window that opens any key from any year, shows every field, switch and game by name, lets you change them and save the result as a new key, re-encrypted for whatever button you choose. It can also generate a blank key for any of the 33 releases.** A ready-to-run copy lives in the `Run/` folder, including **`Megatouch Key Tool.exe`** - one Windows file, no Python needed |
| `mtkey.py decrypt <dump>` | identifies the key family and decodes a keyflasher dump (all families, including Crown) |
| `mtkey4.py decrypt <dump>` | the same for the 2007-and-later Force/ION keys |
| `keyinfo4.py <dump>` | readable report for a Force/ION key: fields, switches, games, checksum |
| `keyinfo.py <dump> --games <gamedata.dat>` | readable report: part number, territory, coins, prices, enabled games by name, all 80 switches |
| `nvram.py <nvram file> [--key <dump>]` | decodes a settings file: settings, books, switches. With a key, shows what the key overrides |
| `p6-craft.py <dump> <new part number> <out>` | changes only the part number (used for the SA999901 test) |
| `p17-reserial.py <dump> 82 <serial> <out dir>` | moves a Jade or Crown key onto a different serial, for emulators |
| `gamedata.py <file>` | lists a game table |

**Testing a key in MegaPPBox:**
- Boot it on the stock "New" image of its product, not a "Keyless" or "Patched" one.
- "Dallas Key mismatch, re-initing NVRAM" followed by a normal boot means the key was **accepted**.
  "Invalid Key", a key error or a shutdown means it was rejected.
- Expect the image's settings to be reset.

The detailed write-ups are in `Docs/`:

| Doc | Topic |
|---|---|
| 01 | key format |
| 02 | which keys each version accepts |
| 03 | the Crown cipher |
| 04 | territories and switches |
| 05 | serial ranges |
| 08 | settings memory |
| 18 | the Force / ION line: buttons, scrambling, passwords, signatures |
| 19 | the 2007-and-later key format, all 120 switch names, game numbering |
| 21 | what each switch does and who sets it, per-release game names, serial-range checks |

A version written for software agents is `keyinfo.md`.

---

## 12. Still unknown

- ~~Whether the second Crown signature (ending `87`) belongs to Force/ION keys.~~ **Settled: it does
  not.** With real Force dumps in hand, Force 2005 turns out to carry exactly the same signature as
  Maxx Jade, and the Force/Maxx difference shows up in the *first* byte instead - Force 2006 reads
  `86 24...` where Crown reads `87 23...`. The `87`-ending variant belongs to a different rule, about
  accented characters in the territory name.
- A **genuine ION 2014 key**. The only one available contradicts itself (it claims Canada while its
  territory text says USA, and its date decodes to 1977), so it is almost certainly hand-made.
- What the few serial-tied bytes at the end of a Force/ION key are for. Six otherwise identical ION
  2009 keys differ *only* in those bytes, and the game never reads them.
- ~~Names for a handful of game slots on the Force side.~~ **Settled:** the Force numbering agrees with
  the ION numbering on all 168 games that could be checked, so the ION names fill the Force gaps. Eight
  of ION's own ~300 slots are still unlabelled.
- The **Force 2007-2011 operator menus**, which were not among the recovered files. Those keys' switches
  are shown with the ION 2011 split between menu and key-only instead.
- The settings memory of the 2007-and-later machines, which moved to XML files and a database.
- The rows of the Linux credit-book database.
- Which of the 80 switches the DOS operator menus offer. The DOS keys carry the same switch table
  (checked against every DOS settings file), but the DOS menus reach most switches through a table
  that hasn't been traced, so only about 20 are confirmed as menu settings.
- XL 6000 and XL Gold: their settings layouts were worked out from the game code but haven't been
  checked against a real machine. No disk images of them, or of XL R1/Super 5000, were available.
- Exactly what the per-game values on older (pre-Titanium) keys mean.
- The online MegaNet server's own checks (out of scope).

<!-- p20: Force/ION + Gen 4 content merged -->

<!-- p21b: option meanings, per-release game names, per-family layouts -->

<!-- p21c: Force / ION woven through every topic -->
