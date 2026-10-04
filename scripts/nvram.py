"""nvram.py - decode Megatouch NVRAM images (DOS C:\\NVRAM.DAT / SRAM dumps, Linux /var/config/nvram.dat).

usage: nvram.py <file> [<file> ...]            human-readable report
       nvram.py --json <file>                  machine-readable
       --key <key dump>    effective option values;  --games <GAMEDATA.DAT>   game names for DOS books
                           (default: analysis/p16/dos_games_by_base.json for the NVRAM's base version)

Layouts are identified by the base-version byte at offset 9 (plus file size for DOS vs Linux).
Field offsets come from Docs/08-nvram.md (code references in each build). 'tentative' layouts
have only one anchor and should be cross-checked.
"""
import sys, json, re, os

# option slot names (Docs/04 complete table)
SLOTS = {}
_doc = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Docs', '04-territory-options.md')
try:
    for l in open(_doc, encoding='utf-8'):
        m = re.match(r'\| 0x([0-9A-F]{2}) \| (.+?) \|', l)
        if m: SLOTS[int(m.group(1), 16)] = m.group(2)
except OSError:
    pass

# layout table: key = (platform, base version) -> fields
DOS_LAYOUTS = {
    # base: (name, options, coins, rev, status)
    0x45: ('XL 6000 R02', 0x108, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x49: ('XL 6000 R04', 0x108, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x4A: ('XL 6000 R07', 0x108, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x4D: ('MAXX 3.06', 0x108, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x50: ('XL Gold R00 / MAXX 2K V4.00-4.01', 0x138, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x53: ('XL Gold R01 / MAXX 2K Plus', 0x138, 0x29, None, 'anchored (default pattern matches later builds)'),
    0x59: ('MAXX Diamond', 0x445, 0x3F5, None, 'anchored'),
    0x5A: ('XL Platinum / Double Platinum', 0x445, 0x3F5, None, 'anchored'),
    0x5D: ('MAXX Double Diamond', 0x445, 0x3F5, None, 'anchored'),
    0x65: ('MAXX Emerald / XL Titanium', 0x3CF, 0x38D, 0x385, 'anchored'),
    0x66: ('MAXX Emerald 2 / XL Titanium 2', 0x3CF, 0x38D, 0x385, 'anchored'),
}
LINUX_LAYOUTS = {
    'ruby': ('Ruby 2 / Sapphire / Sapphire 2', 0x3DA, 0x3C8, 0x384, None, 'anchored (Ruby 2 + Sapphire symbols)'),
    'crown': ('Jade / Jade 2 / Crown', 0x8E, 0x7C, 0x38, 0x40, 'anchored (Crown symbols)'),
}
def linux_layout(b):
    """Base version 0x0A = Ruby 2; 0x10 is shared by Sapphire 2 (Ruby-style) and Jade/Crown.
    Disambiguate by where the key-revision copy ('R..') sits."""
    if b[0x38:0x39] == b'R': return 'crown'
    if b[0x384:0x385] == b'R' or b[9] == 0x0A: return 'ruby'
    return None

def u16(b, o): return b[o] | b[o + 1] << 8

def decode(path, games=None):
    b = open(path, 'rb').read()
    r = {'file': os.path.basename(path), 'size': len(b)}
    if not any(b[:16]):
        r['status'] = 'blank (never initialised)'; return r
    r['valid'] = b[0] == 1
    r['key_part_number'] = b[1:9].decode('latin1')
    r['territory'] = r['key_part_number'][6:8]
    base = b[9]; r['base_version'] = hex(base)
    linux = len(b) >= 0x10000
    if linux and linux_layout(b):
        name, opt, coin, rev, cur, st = LINUX_LAYOUTS[linux_layout(b)]
    elif not linux and base in DOS_LAYOUTS:
        name, opt, coin, rev, st = DOS_LAYOUTS[base]; cur = None
    else:
        r['status'] = f'unknown layout (base {base:#x})'; return r
    r['layout'] = name; r['layout_status'] = st
    if rev: r['key_revision'] = b[rev:rev + 4].split(b'\0')[0].decode('latin1').strip()
    r['coin_channels'] = [{'coins': b[coin + i], 'credits': b[coin + 6 + i], 'pulses': b[coin + 12 + i]} for i in range(6)]
    if cur:
        r['currencies'] = [b[cur + 8 * i: cur + 8 * i + 8].split(b'\0')[0].decode('latin1') for i in range(6)]
    r['options'] = {f'0x{i:02X}': {'value': b[opt + i], 'name': SLOTS.get(i, '')} for i in range(80)}
    if linux:
        build = linux_build(r['key_part_number'], linux_layout(b))
        if build: r['build'] = build; r['settings'] = named_fields(b, build)
    elif hex(base) in DOS_FIELDS:
        # DOS: offsets from the operator-setup DLL's own NVRAM accesses + menu strings (analysis/p13)
        r['build'] = 'DOS SETUP.DLL map'
        r['settings'] = typed_fields(b, DOS_FIELDS[hex(base)])
    if not linux and base in DOS_BOOKS:
        r['books'] = dos_books(b, base, games)
    return r

_DF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'p13', 'dos_fields_by_base.json')
DOS_FIELDS = json.load(open(_DF)) if os.path.exists(_DF) else {}
def typed_fields(b, table):
    import struct
    out = {}
    for k, v in sorted(table.items()):
        o, t = v['offset'], v['type']
        if o + 8 > len(b): continue
        if t == 'u8': x = b[o]
        elif t == 'u16': x = struct.unpack_from('<H', b, o)[0]
        elif t == 'u32': x = struct.unpack_from('<I', b, o)[0]
        elif t == 'f32': x = round(struct.unpack_from('<f', b, o)[0], 4)
        elif t == 'f32x6': x = [round(v, 2) for v in struct.unpack_from('<6f', b, o)]
        else: x = b[o:o + int(t[3:])].split(b'\0')[0].decode('latin1')
        out[k] = x
    return out

# DOS per-game books (P16): array indexed by game ID (= GAMEDATA.DAT record order), located from the
# SETUP.DLL imul-stride accesses and the 'Clearing current/lifetime books' loops (Docs/08).
#   36-byte record (Diamond..Emerald 2): +0 u8 menu flags, +1 u16 = price (low 4 bits) |
#     current books << 4 (12 bits), +3 u32 lifetime books, +7 u8 loader skips (GAMEDATA default 20),
#     +8 u32 current play time packed (bits 0-9 shortest, 10-19 average, 20-31 longest, seconds),
#     +0xE 4 x u16 current games by player count, +0x16 / +0x1C the same two for lifetime.
#   42-byte record (MAXX 3.06, 2K, 2K Plus): +1 u32 = price (low byte) | current books << 8, +5 u32
#     lifetime books, +9 u8 loader skips, +0xA/+0xC/+0xE u16 shortest/longest/average current,
#     +0x12 4 x u16 current games by player count, +0x1A / +0x22 the same for lifetime.
# base: (array offset, record size, capacity). Capacity = records that fit before the next NVRAM array
# (64 for the 42-byte layouts, Diamond and Platinum; 72 Double Diamond; 84 Emerald). The 42-byte
# MEGACDLL update loops are bounded at 64 too.
# XL 6000 (0x45/0x49/0x4A) shares the MAXX 3.06 array and XL Gold (0x50/0x53) the 2K one (same MEGACDLL
# accesses); no XL 6000 GAMEDATA.DAT sample, so its books print without names.
DOS_BOOKS = {0x45: (0x168, 42, 64), 0x49: (0x168, 42, 64), 0x4A: (0x168, 42, 64), 0x4D: (0x168, 42, 64),
             0x50: (0x198, 42, 64), 0x53: (0x198, 42, 64), 0x59: (0x4A5, 36, 64), 0x5A: (0x4A5, 36, 64),
             0x5D: (0x4A5, 36, 72), 0x65: (0x42F, 36, 84), 0x66: (0x42F, 36, 84)}
_DG = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'p16', 'dos_games_by_base.json')
DOS_GAMES = json.load(open(_DG)) if os.path.exists(_DG) else {}
def dos_books(b, base, games=None):
    import struct
    o0, size, cap = DOS_BOOKS[base]
    names = games or DOS_GAMES.get(hex(base), {}).get('names') or []
    out = []
    for g in range(min(len(names), cap) if names else cap):
        r = b[o0 + size * g: o0 + size * (g + 1)]
        if len(r) < size: break
        if size == 36:
            w = struct.unpack_from('<H', r, 1)[0]; price, cur = w & 0xF, w >> 4
            life = struct.unpack_from('<I', r, 3)[0]; skips = r[7]
            t, lt = struct.unpack_from('<I', r, 8)[0], struct.unpack_from('<I', r, 0x16)[0]
            tc = (t & 0x3FF, t >> 10 & 0x3FF, t >> 20); tl = (lt & 0x3FF, lt >> 10 & 0x3FF, lt >> 20)
            pc, pl = struct.unpack_from('<4H', r, 0xE), struct.unpack_from('<4H', r, 0x1C)
        else:
            w = struct.unpack_from('<I', r, 1)[0]; price, cur = w & 0xFF, w >> 8
            life = struct.unpack_from('<I', r, 5)[0]; skips = r[9]
            s, l, a = struct.unpack_from('<3H', r, 0xA); tc = (s, a, l)
            s, l, a = struct.unpack_from('<3H', r, 0x1A); tl = (s, a, l)
            pc, pl = struct.unpack_from('<4H', r, 0x12), struct.unpack_from('<4H', r, 0x22)
        out.append({'id': g, 'name': names[g] if g < len(names) else '', 'flags': r[0], 'price': price,
                    'current': cur, 'lifetime': life, 'loader_skips': skips,
                    'time_current_s': tc, 'time_lifetime_s': tl,
                    'games_by_players_current': pc, 'games_by_players_lifetime': pl})
    return out

# Named settings per Linux build (analysis/p11/linux_fields.json, resolved from the setter functions)
_LF = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'p11', 'linux_fields.json')
LINUX_FIELDS = json.load(open(_LF)) if os.path.exists(_LF) else {}
def linux_build(part, layout):
    """Pick the build-specific field table from the key part number kept in NVRAM."""
    if part.startswith('SA35'): return 'crown'
    if part.startswith('SA3079'): return 'jade'          # Jade and Jade 2 share offsets for these fields
    if part.startswith(('SA3059', 'SA3065')): return 'sapphire'
    if part.startswith(('SA3056', 'SA3061')): return 'ruby2'
    return {'crown': 'crown', 'ruby': 'sapphire'}.get(layout)
def named_fields(b, build):
    import struct
    out = {}
    for k, v in sorted(LINUX_FIELDS.get(build, {}).items()):
        o, t = v['offset'], v['type']
        if o + 16 > len(b): continue
        if t == 'u8': x = b[o]
        elif t == 'u16': x = struct.unpack_from('<H', b, o)[0]
        elif t == 'u32': x = struct.unpack_from('<I', b, o)[0]
        elif t == 'f32': x = round(struct.unpack_from('<f', b, o)[0], 4)
        else: x = b[o:o + int(t[3:])].split(b'\0')[0].decode('latin1')
        out[k] = x
    return out

def apply_key(r, keypath):
    """Combine stored option values with the key's 2-bit lock states (Gen 3 keys: D2[0..0x13])."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
    img, ser = mtkey.load_full(keypath)
    hits = mtkey.try_all(img, ser)
    if not hits: r['key_note'] = 'key did not decrypt'; return r
    scheme, d = hits[0]; D2 = d[120:168]
    r['key_file'] = os.path.basename(keypath); r['key_id'] = d[:8].decode('latin1')
    if r.get('key_part_number') and r['key_id'] != r['key_part_number']:
        r['key_note'] = f"NVRAM belongs to {r['key_part_number']}, key is {r['key_id']} (game would re-init NVRAM)"
    for i in range(80):
        s = (D2[i // 4] >> (6 - 2 * (i % 4))) & 3
        o = r['options'][f'0x{i:02X}']
        o['key_state'] = s
        o['effective'] = 0 if s == 0 else 1 if s == 1 else o['value']
    return r

def report(r):
    print(f"== {r['file']}  ({r['size']} bytes)")
    if 'status' in r: print('  ', r['status']); return
    print(f"   valid={r['valid']}  key={r['key_part_number']} (territory {r['territory']})  base={r['base_version']}  layout={r['layout']} [{r['layout_status']}]"
          + (f"  rev={r['key_revision']}" if 'key_revision' in r else ''))
    print('   coin channels (coins/credits/pulses):', ' '.join(f"{c['coins']}/{c['credits']}/{c['pulses']}" for c in r['coin_channels']))
    if 'currencies' in r: print('   currencies:', [c for c in r['currencies'] if c])
    if r.get('settings'):
        print(f"   settings ({r['build']} offsets):")
        items = [f'{k}={v!r}' for k, v in r['settings'].items()]
        for i in range(0, len(items), 4): print('     ', '  '.join(items[i:i + 4]))
    if r.get('books'):
        played = [g for g in r['books'] if g['lifetime'] or g['current'] or any(g['games_by_players_lifetime'])]
        print(f"   per-game books ({len(played)} of {len(r['books'])} games played; current/lifetime credits, "
              "lifetime shortest/avg/longest s, lifetime games 1-4P):")
        for g in sorted(played, key=lambda g: (-g['lifetime'], -sum(g['games_by_players_lifetime']))):
            print(f"      {g['id']:#04x} {g['name'][:22]:22} price {g['price']}  {g['current']:6}/{g['lifetime']:<7}"
                  f" t {'/'.join(map(str, g['time_lifetime_s']))}  players {'/'.join(map(str, g['games_by_players_lifetime']))}")
    if 'key_id' in r:
        print(f"   key file {r['key_file']} ({r['key_id']})" + (f"  NOTE: {r['key_note']}" if 'key_note' in r else ''))
        lab = {0: 'locked off', 1: 'locked on', 2: 'selectable', 3: 'selectable'}
        on = [f"{k} {v['name'][:34]:34} [{lab[v['key_state']]}, stored {v['value']}]" for k, v in r['options'].items() if v['effective'] == 1]
        dif = [f"{k} {v['name'][:34]:34} stored {v['value']} but key {lab[v['key_state']]}" for k, v in r['options'].items() if v['effective'] != v['value']]
        print(f'   options effectively ON ({len(on)}):'); [print('     ', x) for x in on]
        if dif: print(f'   stored value overridden by key ({len(dif)}):'); [print('     ', x) for x in dif]
    else:
        on = [f"{k} {v['name'][:34]}" for k, v in r['options'].items() if v['value'] == 1]
        print(f'   options stored ON ({len(on)}; pass --key to get effective values):'); [print('     ', x) for x in on]

if __name__ == '__main__':
    args = sys.argv[1:]; key = None; js = False
    if '--json' in args: js = True; args.remove('--json')
    if '--key' in args:
        i = args.index('--key'); key = args[i + 1]; del args[i:i + 2]
    games = None
    if '--games' in args:
        i = args.index('--games'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import gamedata
        games = [g.get('description', '') for g in gamedata.parse(args[i + 1])]; del args[i:i + 2]
    res = [decode(p, games) for p in args]
    if key: res = [apply_key(r, key) if 'options' in r else r for r in res]
    if js: print(json.dumps(res, indent=1))
    else:
        for r in res: report(r)
