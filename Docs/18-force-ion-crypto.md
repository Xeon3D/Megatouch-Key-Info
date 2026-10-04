# 18 — Force / ION product line: containers, ciphers, passwords, signatures

Scope: the Merit **Force** (2002–2011) and **ION** (2006–2014) key families, plus the two
later ION-line products on the same code base (**Touch2Play 2013**, **Firefly 2010**).

Evidence: `scripts/mtkey4.py` (new Gen4 cipher), `scripts/mtpass.py` (new, all DS1991 password
sets), `scripts/p18-recover.py`, `scripts/p18-xorsolve.py`, keyflasher 20240222 source
(`parsing/decrypt`, `parsing/encrypt`, `parsing/validate`, `io/passwords`), the dumps in
`Key Info & Dumps/Force - ION`, and the raw results in `analysis/p18/raw/`.

## Answer in one paragraph

Force and ION are **the same software and the same key format as the Maxx line of the same
year** — the key selects the product. Force 2002–2006 and ION 2006 use DS1991 buttons with
*byte-identical ciphers* to their Maxx siblings (Force 2002 = Emerald, 2003 = Ruby, 2004 =
Sapphire, 2005 = Jade, 2006/ION 2006 = Crown); only the 8-byte signature and the password
init constants differ. From **Force 2007 / ION 2007** onward Merit abandoned the DS1991
MultiKey entirely and moved to a plain NVRAM iButton — **DS1995** (2 KB, family `0x0A`) for
ION 2007, **DS1996** (8 KB, family `0x0C`/`0x8C`) for everything after — holding a single
1024-byte block with no subkeys and no passwords, protected only by a weak keystream cipher.
That is generation **Gen 4** (`Docs/19`).

## Container generations

| Generation | Button | Family | Memory | Key payload | Protection |
|---|---|---|---|---|---|
| Gen 1–3 (`Docs/01`) | DS1991 MultiKey / DS1425 | `0x02`, `0x82` | 256 B | 3 × [ID 8][PW 8][DATA 48] + 64 B scratch | 3 passwords + per-version byte cipher |
| **Gen 4 (new)** | **DS1995** | **`0x0A`** | 2048 B | 1024 B at offset 0 | keystream cipher only |
| **Gen 4 (new)** | **DS1996** | **`0x0C` / `0x8C`** | 8192 B | 1024 B at a per-version offset | keystream cipher only |

`KeyManager::Init` picks the path from `USBIO::GetKeyFamilyCode()`: family `0x0C`, `0x8C` or
`0x0A` ⇒ `Is1995DallasKey() == 1` ⇒ Gen 4 layout; anything else ⇒ the legacy DS1991 layout.
Both layouts live in the same object, and every accessor branches on that flag — so every
Gen 4 build still reads DS1991 keys.

## Force / ION on the DS1991 era (Gen 1–3)

Cipher parameters are **identical** to the Maxx scheme named in the last column — verified by
decrypting each dump with the existing `scripts/mtkey.py` scheme and diffing against
Nicholas' own plaintext: **7 of 7 byte-exact, and all 7 encrypt round-trips exact**
(`analysis/p18/raw/scan_ds1991.txt`).

| Version | Part no. | Cipher scheme | laserMath | Signature | Where |
|---|---|---|---|---|---|
| Force 2002 | SA3050 | XTIT/MEMERALD (`733CAAE7`, inc 0x31, scr 64) | = Emerald | `DD62104321100293` | D0[0..7] (Gen 1/2) |
| Force 2003 | SA3059 | MRUBY (`61E35A13`, inc 0x17, scr 48) | = Ruby | `DE62104321100293` | D0[0..7] (Gen 2) |
| Force 2004 | SA3068 | MSAPPHIRE (`A7679AAA`, inc 0x53, scr 60) | = Sapphire | `1234567890ABCDEF` | D0[0x28..0x2F] (Gen 3) |
| Force 2005 | SA3083 | MJADE (`FF355A4B`, inc 0x16, scr 60) | = Jade | `8723879FE2432498` | D0[0x28..0x2F] |
| Force 2006 | SA3501 / SA3504 | MCROWN (`127837F3`, inc 0x16, scr 60) | = Crown | **`8624879FE2432498`** | D0[0x28..0x2F] |
| ION 2006 | SA3505 | MCROWN | = Crown | **`342190FA11880410`** | D0[0x28..0x2F] |

Force 2002 is a **DOS** build (its HDD image is FAT with a `MERIT2` tree and `MEGACDLL.EXE`),
which is why it shares the Emerald/Titanium cipher. Force 2003 onward are the i386 Linux
`start` builds.

*P21:* the Force builds also inherit the Maxx **serial windows** (`Docs/05`), proven by md5
identity of the packed `start` launchers rather than by re-reading the constants: Force 2003.5
v11.00 = Maxx Ruby 2 V11.00, Force 2005 v14.00 = Maxx Jade V14.00, Force 2005.5 v15.10 = Maxx
Jade 2 V15.10. Force 2003 v10.09, Force 2004, Force 2006 and ION 2006 have no matching binary in
the corpus and are taken to follow their nearest Maxx sibling [inferred]. The Gen 4 releases have
no window at all; their only container rule is DS1995/DS1996 and a button large enough for the
release's block offset (ION 2013 writes at 7 KB → DS1996). `mtkeylib.check_serial()` applies
both.

### Resolved: what the Crown gate's signature modifiers mean (`Docs/02` open item)

`Docs/02` recorded that Crown's gate accepts `8723879FE2432498` **or** `8723879FE2432487`
and asked whether `…2487` is the Force variant. It is not:

- The **Force variant changes byte 0, not byte 7**. The Force 2006 dump carries
  `86 24 879FE2432498` while the Maxx Crown dump carries `87 23 879FE2432498`: byte 0 is
  −1 and byte 1 is +1. That is exactly the platform-check modifier (`Docs/02`:
  "D2[0x1C] bit 3 must agree with a platform check, otherwise the expected signature's
  first byte is +1"), seen from the key side for the first time.
- The two Force 2005 dumps and the Maxx Jade dump carry the **same** `8723879FE2432498`, so
  that value is not Maxx-specific either.
- `…2487` (= `…2498` − 0x11) therefore belongs to the *other* modifier, the high-bit
  character in the territory name — not to Force.

Platform bit D2[0x1C] bit 3 across every DS1991 dump (`analysis/p18/raw/`):

| Key | D2[0x1C] | bit 3 | reading |
|---|---|---|---|
| Force 2004 / 2005 / 2006, ION 2006 | `7F` / `FF` | set | Force/ION hardware |
| Maxx Sapphire SA3059/SA3065 | `7F` | set | ~~— see note~~ *corrected P21:* on Sapphire D2[0x1C] is an option byte; its Bowling bit is D1[0x1A] bit 3 — clear on SA306501 (Maxx), set on SA305945 whose D1 equals the Force 2004 key's (`Docs/21` C3) |
| Maxx Jade SA307901 (`0900…`) | `FF` | set | — see note |
| Maxx Jade SA307901 (`4700…`) | `F7` | clear | Maxx hardware |
| Maxx Crown SA351133 | `F3` | clear | Maxx hardware |
| every Gen 1/2 Maxx/XL key | `52`–`56` | clear | Maxx/XL |

Note: the bit is game **0x44 (Bowling)** in the key's game bitmap and Bowling is flagged
Force-only (`Docs/08` P14), so "set" means the key enables a Force-only game. Two keys with
the same part number SA3079 differ in it, so the bit is a per-key programming choice rather
than a property of the SKU. **Open:** why a Sapphire/Jade-labelled key would carry it set.

## Force / ION passwords (all DS1991 schemes now reproducible)

`scripts/mtpass.py` ports every keyflasher `*PasswordGenerator` plus `MCROWN` (which
keyflasher lacks; recovered in P17). Shape for all of them: `magic = laserMath(ROM)`, a
3 × 8-byte init table (fixed constants or ROM-derived), then
`p[i] ^= magic[i%4]; p[i] += seed; seed += inc` with `seed = blkVCode[subkey]`.

**Verified against the passwords stored in the dumps: 48 of 49 reproduced byte-exact**
(`analysis/p18/raw/passwords.txt`).

| Password scheme | Init table | blkVCode / inc | Notes |
|---|---|---|---|
| M1 | fixed `CCE3AAF00F3CAECE` ×3 | 0 / 0 | no encryption step |
| XGOLD, M2K, XPLAT, MDIAMOND, XTIT, MEMERALD | per-version fixed 3×8 constants | per scheme | Merit used x86 instruction bytes as some constants |
| **F2002** | Emerald constants XOR `02`/`31`/`10` | `733CAAE7` / 0x31 | = Ruby's init with Emerald's cipher |
| MRUBY, **F2003** | Emerald constants XOR `02`/`31`/`10` | `61E35A13` / 0x17 | **F2003 passwords ≡ MRUBY passwords** |
| MSAPPHIRE | ROM-derived (`k7 % 7`, a shift chain, `k7 & 0x1F`) | `A7679AAA` / 0x53 | |
| **F2004** | ROM-derived (`k7 & 0xF`, two shift chains) | `A7679AAA` / 0x53 | differs from Sapphire |
| MJADE, MCROWN | `t = i + k[i] + 0x27/0x30/0x42`, `(t + t/255) ^ p` | `FF355A4B` / `127837F3` | |
| **F2005** | same shape, constants `0x03/0x11/0x99` | `FF355A4B` / 0x16 | |
| **FI2006** (Force + ION 2006) | `t = i + k[i] + 0x03/0x11/0x99`, `p ^= t % 255` | `127837F3` / 0x16 | mod, not the `t + t/255` form |

Consequence: Force 2003 keys and Maxx Ruby 2 keys are interchangeable at the crypto layer
(same cipher *and* same passwords) and differ only in the signature — consistent with the
P0 finding that Maxx Ruby 2 V11.00 and Force 2003.5 share one `start` binary.

The one unmatched dump is `SA002001_full_5B0000008E4C8A02` (the key the Emerald V8.05
"exefix" image last ran with). It decrypts with the Emerald cipher and carries a mangled
Emerald signature `DD62108621400293`, but its stored passwords match no generator — a fourth
Emerald-era init table, presumably an engineering/service key. **Open**, low value.

## Gen 4 cipher (Force 2007–2011, ION 2007–2014)

Two keystream variants over the 1024-byte block, both keyed by a 6-byte per-version magic
and the **inner six bytes of the ROM serial** (serial string = OneWire print order,
CRC first … family last, so `serial[1..6]`):

```
ADD:  kk[i] = magic[5-i] + serial[6-i]
      for i in 0 .. 32*nChunks-1:  plain[i] = cipher[i] - ((i/32) ^ kk[i%6]) + (i/32)
XOR:  kk[i] = magic[5-i] ^ serial[6-i]
      bytes 18..21 first (and, for 2009/2010, kk[0..3] are then REPLACED by the
      ciphertext bytes 18..21), then plain[i] = cipher[i] ^ kk[i%6] for every other byte
```

| Version | Part no. | Mode | Magic | Block offset | Notes |
|---|---|---|---|---|---|
| Force 2007 | SA3526 | ADD | `55AA72371221` | 0 | 31 chunks (992 B) |
| ION 2007 | SA3522 / SA3523 | ADD | `55AA72371221` | 0 | DS1995, 31 chunks |
| Force 2008 | SA3542 / SA3543 | ADD | `55AA72371221` | 0 | 32 chunks; "special" variant when the block already starts `SA` and byte 17 == 0x18 |
| ION 2008 | SA3547 / SA3548 | ADD | `55AA72371221` | 0 | as Force 2008 |
| Force 2009 | SA3570 / SA3572 | XOR | `36353759564E` | **1024** | key bytes 0..3 replaced from the data |
| ION 2009 | SA3559 / SA3560 | XOR | `36353759564E` | **1024** | as Force 2009 |
| Force 2010 | SA3579 | XOR | `3637374C4F42` | 0 | key bytes 0..3 replaced from the data |
| ION 2010 | SA3590 | XOR | `3637374C4F42` | 0 | as Force 2010 |
| Force 2011 | SA3603 / SA3604 | XOR | `393D3649564E` | 0 | |
| ION 2011 | SA3605 / SA3607 | XOR | `45414156594C` | **2048** | |
| ION 2012 | SA3614 / SA3617 | XOR | `726D5F6A634C` *or* `45414156594C` | **2048** | two magics in the wild |
| ION 2013 | SA3623 / SA3624 | XOR | `6D6B5C68624C` | **6144** | |
| ION 2014 | SA3628 / SA3630 | XOR | `756F726E6260` | **2048** | |

Force and ION share the magic wherever the year matches (2007, 2008, 2009, 2010); they
diverge from 2011, when the Force line stopped and ION continued.

**Verification: 22 of 22 Gen 4 dumps decrypt byte-exact against Nicholas' plaintexts, every
stored checksum validates, and all 22 encrypt round-trips are byte-exact**
(`analysis/p18/raw/verify_gen4.txt`, `roundtrip_gen4.txt`).

### The cipher leaks its own key

Because the XOR variant is a repeating 6-byte key and the plaintext starts with the ASCII
part number `SAnnnn`, the key falls out of the first six bytes; long runs of plaintext zeros
print it outright. From the key, `serial[6-i] = magic[5-i] ^ kk[i]` recovers the button's
inner serial bytes and identifies the version at the same time
(`scripts/p18-xorsolve.py`). Applied to the three unlabelled dumps:

| File | Recovered | Serial (inner 6) |
|---|---|---|
| `Force 2011/FORCE 2011.bin` | Force 2011, SA360301, checksum OK | `0040 0003994F` |
| `V40.02/data_32771_*KEY_DATA_CHUNK(1st..8th)` concatenated | **ION 2014**, SA362801, checksum OK | `0040 0001A819` |
| `ION 2014 (Tommy)/key_out` | ION/Force **2010** (SA3590), checksum FAILS | `0040 0002CAAA` (from `laser_out`) |

The V40.02 capture is a genuine USB read of an ION 2014 key in 8 × 128-byte chunks; unlike
the Crown-era board (`Docs/03`) the data arrives **unmasked**, so the chunks concatenate
straight into the encrypted block.

Tommy's `key_out` is the one inconsistent sample: byte 18 of the block is `0x59` where the
part-number prefix demands `0x58`, and the checksum does not validate either way. Since for
Force/ION 2010 key bytes 0..3 come from the block's *own* bytes 18..21, a one-bit error
there corrupts every sixth plaintext byte. Treated as a damaged or hand-made dump.
`laser_out` is the 8-byte ROM in ROM order (`1BAACA020040004D`), i.e. print-order
`4D00400002CAAA1B` — family `0x1B`, which is not a Dallas memory-iButton family, so that
button is probably emulated.

## Corpus

| Source | Contents |
|---|---|
| `Force - ION/Nicholas keys` | 29 encrypted dumps + matching plaintexts, F2002→F2011 and I2006→I2014 (several are *synthetic*: I2010/I2012/I2013/I2014 are re-encrypted onto the I2009 serial `0300400001ED838C`) |
| `Force - ION/Force 2011/FORCE 2011.bin` | real Force 2011 block, no serial in the file |
| `Force - ION/V40.02/` | USB capture of an ION 2014 key read (SERIAL, INIT, Confirmkey, 8 data chunks) |
| `Force - ION/ION 2014 (Tommy)/` | `key_out` + `laser_out`, damaged/emulated |
| `Force - ION/ION 2014 Web`, `Public ION 2014 Dump` | the same `start` binary (md5 `cbfcfab83a70e212438710ccf539104b`), identical to `/usr/local/bin/start` on the ION 2014 P5B image |

Only one ION 2014 key exists in the corpus and it is internally inconsistent — country code
1 (Canada) with territory `USA-STD`, and a programming date that decodes to 1977 while every
other genuine key decodes to the year before its product. **Open: a genuine ION 2014 dump.**

## Adversarial check (guardrail 7)

- *Boring explanation first:* the entire Force/ION DS1991 era was assumed to need new
  cipher work. It did not — the ciphers are the Maxx ones, and the cheap experiment
  (run the existing `mtkey.py` schemes over the new dumps) settled it in one command.
- *Live vs dead:* the Gen 4 cipher was confirmed from the binary, not only from keyflasher —
  `KeyManager::Check` in ION 2014 recomputes exactly keyflasher's checksum (sum of bytes
  0..0x3EF skipping 18..21 and 0x355/0x356, compared against the u16 at 0x355), and
  `KeyManager::Read` reads 0x3F0 bytes into the object. Two independent sources agree.
- *Not covered by the cheap scan:* the 8051 firmware on the USB I/O board (not needed —
  ION returns unmasked data); whether the DS1996's other 7 KB hold anything (every dump has
  the block only, rest zero); the `0x3F0..0x3FF` tokens, which the game never reads.
- *Integrity self-check found:* `KeyManager::Check` opens and reads **its own executable**
  (raw `open`/`read`/`close` syscalls, 0x400 bytes) before the signature comparison. New
  surface, not analysed — recorded in the `CLAUDE.md` surface table as **N**.
