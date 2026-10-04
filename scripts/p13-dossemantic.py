# p13-dossemantic.py: resolve named DOS NVRAM settings per layout from SETUP.DLL string anchors.
import glob, os, json, re
D = 'F:/MTKeyWork/analysis/p13/'
# field: (type, regex on the strings column, pick: 'first'|'last'|'max')
ANCH = {
 'free_credits':          ('u32', r'^FREE CREDITS', 'first'),
 'freeplay_credits':      ('u32', r'(^| \| )FREEPLAY CREDITS', 'first'),
 'b2_coins':              ('f32', r'B2 COINS', 'first'),
 'tournament_play':       ('u16', r'TOURNAMENT PLAY', 'first'),
 'tourn_paid_without_pin':('u16', r'PAID WITHOUT PIN', 'first'),
 'tourn_claimed_prize':   ('u16', r'CLAIMED PRIZE', 'first'),
 'security_pin':          ('str4', r'PIN MIS-MATCH', 'first'),
 'volume':                ('u32', r'volloop', 'last'),
 'touchtunes_credits':    ('u16', r'TOUCH TUNES', 'first'),
 'play_time_shortest':    ('u16', r'SHORTEST PLAY', 'first'),
}
out = {}
for f in sorted(glob.glob(D + '*.setup.nvmap.tsv')):
    n = os.path.basename(f).replace('.setup.nvmap.tsv', '')
    rows = [l.rstrip('\n').split('\t') for l in open(f, encoding='utf-8').readlines()[1:]]
    res = {}
    for k, (t, rx, pick) in ANCH.items():
        hits = [int(r[0], 16) for r in rows if len(r) > 3 and re.search(rx, r[3])]
        if hits: res[k] = {'offset': hits[0] if pick == 'first' else hits[-1], 'type': t, 'all': [hex(h) for h in hits[:4]]}
    out[n] = res
json.dump(out, open(D + 'dos_fields.json', 'w'), indent=1)
keys = list(ANCH)
print('image'.ljust(34) + ''.join(k[:11].ljust(12) for k in keys))
for n, r in out.items():
    print(n[:33].ljust(34) + ''.join((hex(r[k]['offset']) if k in r else '-').ljust(12) for k in keys))

# ---- P16: derived fields + per-base table (consumed by scripts/nvram.py) ----
# Every DOS credit counter is a current/lifetime u32 pair (the label sits on the current one; the
# lifetime copy is the next unlabelled '%ld' offset, +4). Total credits sit 8 bytes before free credits
# (2K: labelled 'TOTAL CREDITS'; Diamond+: unlabelled 0x27/0x2B). B2 coins are 6 f32 channels,
# lifetime copy +0x18. Values checked on played NVRAMs (current <= lifetime everywhere).
PAIRS = {'free_credits': 4, 'freeplay_credits': 4}
def derive(r):
    d = {}
    for k, v in r.items():
        if k == 'play_time_shortest': continue          # superseded by the per-game books decoder
        d[k] = {'offset': v['offset'], 'type': v['type']}
        if k in PAIRS: d[k + '_lifetime'] = {'offset': v['offset'] + 4, 'type': 'u32'}
    if 'free_credits' in r:
        fc = r['free_credits']['offset']
        d['total_credits'] = {'offset': fc - 8, 'type': 'u32'}
        d['total_credits_lifetime'] = {'offset': fc - 4, 'type': 'u32'}
    if 'b2_coins' in r:
        o = r['b2_coins']['offset']
        d['b2_coins'] = {'offset': o, 'type': 'f32x6'}
        d['b2_coins_lifetime'] = {'offset': o + 0x18, 'type': 'f32x6'}
    return d
# MAXX 3.06 (base 0x4D): SETUP.DLL uses button-graphic names, not the 2K text labels, so the anchors
# miss. Its layout is 2K minus 0x30 below 0xE00 (options 0x108 vs 0x138, books 0x168 vs 0x198, PIN
# 0xD33 'secpin' vs 0xD63, adult-hours bytes 22/6/2 at 0xD2C vs 0xD5C in both played images).
# Tournament counters: code order in fn_35438 ('Tournament Play' -> 0x177C/0x1780, 'Paid Without
# Pin' -> 0x1784/0x1788, 'Claimed Prize' -> 0x178C/0x1790), record 0 of the 0xE4-stride array at 0x174A.
MANUAL = {'0x4d': {
    'total_credits': (0x3C, 'u32'), 'total_credits_lifetime': (0x40, 'u32'),
    'free_credits': (0x44, 'u32'), 'free_credits_lifetime': (0x48, 'u32'),
    'b2_coins': (0xBC, 'f32x6'), 'b2_coins_lifetime': (0xD4, 'f32x6'),
    'security_pin': (0xD33, 'str4'), 'adult_off_hour': (0xD2C, 'u8'), 'adult_on_hour': (0xD2D, 'u8'),
    'tournament_play': (0x177C, 'u32'), 'tourn_paid_without_pin': (0x1784, 'u32'),
    'tourn_claimed_prize': (0x178C, 'u32'), 'volume': (0x6764, 'u32')},
  '2k_extra': {'adult_off_hour': (0xD5C, 'u8'), 'adult_on_hour': (0xD5D, 'u8')}}
NV = 'F:/MTKeyWork/analysis/p9/nvram/'
by_base = {}
for n, r in out.items():
    p = NV + n + '.NVRAM.DAT'
    if not os.path.exists(p): continue
    b = open(p, 'rb').read()
    if not any(b[:16]): continue
    base = hex(b[9])
    if base in by_base or not r: continue
    by_base[base] = derive(r)
    if base in ('0x50', '0x53'):
        by_base[base].update({k: {'offset': o, 'type': t} for k, (o, t) in MANUAL['2k_extra'].items()})
by_base['0x4d'] = {k: {'offset': o, 'type': t} for k, (o, t) in MANUAL['0x4d'].items()}
# XL 6000 R02/R04/R07 (no HDD image): MEGACDLL references the 3.06 credit/B2 offsets with identical
# per-offset reference counts (4,5,2,3,4,5) and has no security PIN / adult-hours accesses.
for xb in ('0x45', '0x49', '0x4a'):
    by_base[xb] = {k: v for k, v in by_base['0x4d'].items() if 'credits' in k or 'b2_coins' in k}
json.dump(by_base, open(D + 'dos_fields_by_base.json', 'w'), indent=1)
print('\nper-base fields:')
for k, v in sorted(by_base.items()): print(k, ' '.join(f'{n}={x["offset"]:#x}' for n, x in v.items()))
