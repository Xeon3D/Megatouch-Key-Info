"""p21b-update-claude.py - record the P21b documentation pass in CLAUDE.md.

Asserted edits, sentinel-guarded (see the P20 lesson in CLAUDE.md).

    python scripts/p21b-update-claude.py [--check]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, 'CLAUDE.md')
SENTINEL = '<!-- p21b: handover docs and share pages carry P21 -->'

EDITS = [
    ('> **STATUS (2026-10-03): Phases 0–21 done (P21: key tool v2 + .exe; Gen 1/2 D2 = option table, '
     'Sapphire layout corrected — Docs/21).',
     '> **STATUS (2026-10-03): Phases 0–21 done (P21: key tool v2 + .exe; Gen 1/2 D2 = option table, '
     'Sapphire layout corrected — Docs/21; P21b folded all of it into `keyinfo.md`, `keyinfo-human.md` '
     'and both `share/` pages).'),

    ('| 6 — emulator falsification |',
     '| 21b — handover docs & share pages | `keyinfo.md`, `keyinfo-human.md`, `share/*.html`, '
     '`scripts/p21b-update-{docs,share,claude}.py` | P21 folded into both handover docs: Sapphire/Force 2004 '
     'layout, Ruby opt-out game list, Force builds that enforce the Maxx windows + Gen 4 container rule, '
     'option meanings (67/120 in Merit\'s words) and the per-release menu/key-only split, per-family game '
     'storage, per-release game names (26 tables, Force gaps filled from ION), renumbered open items. '
     'Research page: header now 1997–2014, new serial/option/game-table blocks, key-editor section moved '
     'to match the TOC; guide regenerated |\n'
     '| 6 — emulator falsification |'),
]


def main():
    s = open(TARGET, encoding='utf-8').read()
    if SENTINEL in s:
        print('CLAUDE.md already updated (sentinel present), nothing to do')
        return 0
    missing = [a for a, _ in EDITS if s.count(a) != 1]
    for m in missing:
        print('  !! no unique match: %r' % m[:70])
    if missing:
        print('refusing to write a partial update')
        return 1
    if '--check' in sys.argv:
        print('all %d edits would apply' % len(EDITS))
        return 0
    for a, b in EDITS:
        s = s.replace(a, b, 1)
    open(TARGET, 'w', encoding='utf-8').write(s.rstrip() + '\n\n' + SENTINEL + '\n')
    print('CLAUDE.md: %d edits applied' % len(EDITS))
    return 0


if __name__ == '__main__':
    sys.exit(main())
