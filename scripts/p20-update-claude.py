"""p20-update-claude.py - finish the CLAUDE.md maintenance for P18-P20.

An earlier pass used str.replace() without checking, so some rows were silently dropped.
This script asserts every edit, refuses to write a partial update, and carries a sentinel so
a second run is a no-op.

    python scripts/p20-update-claude.py
    python scripts/p20-update-claude.py --check
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'CLAUDE.md')
SENTINEL = '<!-- p20: ledger and buckets complete -->'

EDITS = [

# --- artifact buckets ------------------------------------------------------
("""| Key dumps | `Key Info & Dumps/New Keys` (superset of `Keys`) | keyflasher `*_full_*` (256 B + 8 B serial) and `*_decrypted_*` (232 B) | yes |""",
 """| Key dumps | `Key Info & Dumps/New Keys` (superset of `Keys`) | keyflasher `*_full_*` (256 B + 8 B serial) and `*_decrypted_*` (232 B) | yes |
| Force/ION dumps | `Key Info & Dumps/Force - ION` | F2002→F2011, I2006→I2014 (Nicholas), Force 2011 block, ION 2014 USB capture (V40.02), ION 2014 `start` | yes |
| Force/ION/T2P/Firefly images | `H:/Megatouch/Hard Disk Images/<product>/*.img` | use the extracted `.img` only, never the archives; ignore `ION 2014 Lost Classics` | yes |
| Gen 4 binaries + configs | `analysis/p19/bin/<tag>/`, `analysis/p19/xml/<tag>/` | `start`, `opsetup.so`, `libenums.so`, `gamedata.xml`, `settings.xml`, extracted read-only | regenerable |
| Runnable key editor | `Run/` | self-contained copy of the tool + launcher + README, no workspace dependencies | regenerable |
| Shareable pages | `share/*.html` | standalone HTML: the research page and the plain-language guide | regenerable |"""),

# --- surface table ---------------------------------------------------------
("""| L | HDD model check `HDIsOk` (XOR 0x11 string) | Sapphire V12.01 | bool-gate? | boot | found, not analysed (new surface, P2) |""",
 """| L | HDD model check `HDIsOk` (XOR 0x11 string) | Sapphire V12.01 | bool-gate? | boot | found, not analysed (new surface, P2) |
| N | Executable self-read integrity check | Gen 4 `KeyManager::Check` (raw open/read/close of its own file, 0x400 B) | integrity | every boot | **found, not analysed** (new surface, P19) |"""),

# --- phase ledger ----------------------------------------------------------
("""| 7 — open-item sweep | Docs/02, 04, 05 updated | dual-platform DOS builds explained; TournaMAXX = option 0x14; Ruby 2/Sapphire 12.01 ranges; Maxx vs Force via ForceChk1 + key bit; board whitelist |""",
 """| 7 — open-item sweep | Docs/02, 04, 05 updated | dual-platform DOS builds explained; TournaMAXX = option 0x14; Ruby 2/Sapphire 12.01 ranges; Maxx vs Force via ForceChk1 + key bit; board whitelist |
| 18 — Force/ION corpus & crypto | `Docs/18-force-ion-crypto.md`, `scripts/mtkey4.py`, `mtpass.py`, `p18-*.py`, `analysis/p18/` | Gen 4 container (DS1995/DS1996) + both keystream ciphers for 13 versions, **22/22 dumps byte-exact + round-trip**; every DS1991 password set incl. Force/ION, **48/49 reproduced**; Force 2002 = DOS build; Force ciphers ≡ Maxx ciphers; `…2487` open item resolved; 3 unlabelled dumps identified by key recovery |
| 19 — Gen 4 field map | `Docs/19-gen4-format.md`, `scripts/keyinfo4.py`, `p19-*`, `analysis/p19/` | full field map from `KeyManager` in the ION 2014 binary (the key block is read into the object at offset 0); checksum confirmed from code; **all 120 option slots named**, identical across 4 builds; game-id enum recovered (293/301 ION); Gen 4 dropped the serial window; new surface N |
| 20 — key editor | `scripts/mtkeytool.py` (GUI), `mtkeylib.py` (model), `test-mtkeytool.py`, `scripts/data/*.json`, `Run/` | read/show/edit/save/generate keys for **all 33 releases**; suite green: 107 dumps load + round-trip, 19 edit cycles, 33 generated releases, retarget, serial recovery, GUI checks |
| 20b — docs & shareable pages | `keyinfo.md`, `keyinfo-human.md`, `share/*.html`, `Run/` | Force/ION + Gen 4 folded into both handover docs (idempotent `p20-update-docs.py`, `p20-update-guide.py`); research page gained "The Force / ION line" and "The 2007 key format" plus rewritten open items, guide regenerated (`p20-update-share.py`); `Run/` built and self-tested by `p20-make-run.py` |"""),

# --- anti-pattern note, earned twice this session ---------------------------
("""## Tooling baseline""",
 """## Lesson added P20

`str.replace()` without checking the result is a silent no-op. Two edits in this session
"succeeded" while changing nothing — a CLAUDE.md ledger update, and a GUI smoke test that
reported OK while the file it claimed to open did not exist. **Every scripted edit asserts
that its anchor matched, and every test asserts on a return value rather than on the absence
of an exception.** The `p20-*.py` scripts and `scripts/test-mtkeytool.py` follow this.

## Tooling baseline"""),
]


def main():
    check = '--check' in sys.argv
    s = open(TARGET, encoding='utf-8').read()
    if SENTINEL in s:
        print('CLAUDE.md already updated (sentinel present), nothing to do')
        return 0
    missing = [old for old, _ in EDITS if old not in s]
    if missing:
        for m in missing:
            print('  !! no match: %r' % m.split('\n')[0][:72])
        print('refusing to write a partial update')
        return 1
    if check:
        print('all %d edits would apply' % len(EDITS))
        return 0
    for old, new in EDITS:
        s = s.replace(old, new, 1)
    open(TARGET, 'w', encoding='utf-8').write(s.rstrip() + '\n\n' + SENTINEL + '\n')
    print('CLAUDE.md: %d edits applied' % len(EDITS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
