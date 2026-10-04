"""keyinfo4.py - decode a Gen4 Megatouch key (Force 2007-2011 / ION 2007-2014).

Field map recovered from KeyManager::{Init,Read,ParseOptionData,Check} and every accessor
in the Gen4 binaries (ION 2014 start, analysis/p19/raw/I2014.keymgr.asm). The game reads
0x3F0 bytes of the decrypted block straight into the KeyManager object at offset 0, so
every object offset below 0x3F0 in those functions IS the key offset.

usage: keyinfo4.py <key file> [...]        full report per key
       keyinfo4.py --map                   print the field map only
"""
import sys, os, struct, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey4

# offset, size, name  (sizes: 'b' u8, 'w' u16, 'd' u32, 'q' u64, 'f' f32, n = n-byte string)
MAP = [
    (0x000, 8,   'part number (ASCII SAnnnnTT)'),
    (0x008, 1,   'unused / high byte of date'),
    (0x009, 'd', 'programming date (time_t, LE)'),
    (0x00D, 4,   'revision (ASCII, e.g. R00)'),
    (0x011, 1,   'unused'),
    (0x012, 4,   'serial-bound token (excluded from checksum)'),
    (0x016, 10,  'territory / country description (ASCII)'),
    (0x020, 10,  'territory field tail'),
    (0x02A, 200, 'MegaNet server URL (ASCII)'),
    (0x0F2, 'b', 'country code'),
    (0x0F3, 'b', 'NJ exception number'),
    (0x0F4, 'b', 'lockout value'),
    (0x0F5, 8,   'signature (8 bytes)'),
    (0x0FE, 'w', 'ChampEdition game cost'),
    (0x100, 'w', 'ChampEdition prize mode (bits 5..6)'),
    (0x102, 'w', 'ChampEdition prize pool rate (x5)'),
    (0x104, 'q', 'language mask (64 bit)'),
    (0x10C, 'd', 'default language mask'),
    (0x114, 92,  'currency names: 4 x 23 bytes'),
    (0x170, 'b', 'default pricing scheme'),
    (0x171, 'b', 'default currency'),
    (0x172, 36,  'coin channel values: 9 x f32'),
    (0x192, 6,   'credits per channel: 6 x u8'),
    (0x198, 24,  'channel values: 6 x f32'),
    (0x1B0, 300, 'per-game price: low nibble = price, high nibble = continue cost'),
    (0x2DC, 'b', 'price for game 0x2718'),
    (0x2DD, 120, 'option slots: 120 x u8 (0 off, 1 on, 2/3 operator-selectable)'),
    (0x355, 'w', 'checksum (u16)'),
    (0x357, 'w', 'unit time, game 0x2718 (s)'),
    (0x359, 'w', 'unit time, game 0x271B (s)'),
    (0x35B, 100, 'web portal URL (ASCII)'),
    (0x3BF, 48,  'game enable bitmap: 300 bits, MSB first'),
    (0x3EF, 'b', 'region'),
    (0x3F0, 16,  'serial-bound tokens x3 (not read by the game; outside the checksum)'),
]

# the 8-byte signatures Check() compares against (ION 2014)
GEN4_SIGS = {
    '93e41c6e20911b9b': 'Gen4 sig A',
    'cfb4a9611bb72003': 'Gen4 sig B',
    '00000000c7723cef': 'Gen4 sig C',
}


def s(d, o, n):
    raw = d[o:o + n]
    return raw.split(b'\0')[0].decode('latin1', 'replace')


def options(d):
    return list(d[0x2DD:0x2DD + 120])


def game_prices(d):
    return [(d[0x1B0 + i] & 0xF, d[0x1B0 + i] >> 4) for i in range(300)]


def game_bitmap(d):
    """Returns the list of enabled game ids, decoded exactly as KeyManager::Init does."""
    out = []
    for gid in range(0x12C):
        byte = d[0x3BF + gid // 8]
        if byte & (0x80 >> (gid % 8)):
            out.append(gid)
    return out


def date(d):
    t = struct.unpack_from('<I', d, 0x009)[0]
    try:
        tm = time.gmtime(t)
        return '%02d/%02d/%02d (%s, time_t %u)' % (
            tm.tm_mon, tm.tm_mday, tm.tm_year % 100,
            time.strftime('%Y-%m-%d', tm), t)
    except (ValueError, OSError, OverflowError):
        return 'invalid (time_t %u)' % t


def report(path):
    mem, ser = mtkey4.load(path)
    if not ser:
        print('%s: no serial in file or name' % path)
        return
    hits = mtkey4.try_all(mem, ser)
    if not hits:
        print('%s: no Gen4 scheme decrypts this' % os.path.basename(path))
        return
    for v, d in hits:
        print('=' * 78)
        print('%s   version %s   serial %s' % (os.path.basename(path), v, ser))
        ck, st = mtkey4.checksum(d, v), mtkey4.stored_checksum(d, v)
        print('  part number      %s' % s(d, 0, 8))
        print('  revision         %s' % s(d, 0x0D, 4))
        print('  programming date %s' % date(d))
        print('  territory        %r' % s(d, 0x16, 10))
        print('  country code     %d   NJ exception %d   lockout %d   region %d'
              % (d[0xF2], d[0xF3], d[0xF4], d[0x3EF]))
        sig = d[0xF5:0xFD]
        print('  signature        %s  %s' % (sig.hex().upper(),
                                             GEN4_SIGS.get(sig.hex(), 'unrecognised')))
        print('  checksum         stored %04X  computed %04X  %s'
              % (st, ck, 'OK' if st == ck else 'MISMATCH'))
        print('  server URL       %s' % s(d, 0x2A, 200))
        print('  web portal       %s' % s(d, 0x35B, 100))
        print('  language mask    %016X   default %08X'
              % (struct.unpack_from('<Q', d, 0x104)[0],
                 struct.unpack_from('<I', d, 0x10C)[0]))
        print('  pricing scheme   %d   default currency %d' % (d[0x170], d[0x171]))
        cur = [s(d, 0x114 + 23 * i, 23) for i in range(4)]
        print('  currency names   %s' % ', '.join('%d=%r' % (i, c) for i, c in enumerate(cur) if c))
        chv = struct.unpack_from('<9f', d, 0x172)
        print('  coin channels    %s' % ', '.join('%g' % x for x in chv))
        print('  credits/channel  %s' % list(d[0x192:0x198]))
        print('  channel values   %s' % ', '.join('%g' % x for x in struct.unpack_from('<6f', d, 0x198)))
        print('  ChampEdition     cost %d  prize mode %d  pool rate %d'
              % (struct.unpack_from('<H', d, 0xFE)[0],
                 (struct.unpack_from('<H', d, 0x100)[0] >> 5) & 3,
                 struct.unpack_from('<H', d, 0x102)[0] * 5))
        print('  unit time        %ds / %ds' % (struct.unpack_from('<H', d, 0x357)[0],
                                                struct.unpack_from('<H', d, 0x359)[0]))
        op = options(d)
        byst = {k: [i for i, x in enumerate(op) if x == k] for k in (0, 1, 2, 3)}
        print('  options (120)    on=%d locked-off=%d selectable=%d'
              % (len(byst[1]), len(byst[0]), len(byst[2]) + len(byst[3])))
        for k, lab in ((1, 'forced ON  '), (2, 'selectable '), (3, 'selectable*')):
            if byst[k]:
                print('      %s %s' % (lab, ' '.join('%02X' % i for i in byst[k])))
        gb = game_bitmap(d)
        pr = game_prices(d)
        priced = [i for i, (p, c) in enumerate(pr) if p]
        print('  games in bitmap  %d   with a price  %d' % (len(gb), len(priced)))
        print('      bitmap ids   %s%s' % (' '.join('%X' % g for g in gb[:48]),
                                           ' ...' if len(gb) > 48 else ''))
        print('      priced ids   %s%s' % (' '.join('%X:%d' % (i, pr[i][0]) for i in priced[:30]),
                                           ' ...' if len(priced) > 30 else ''))
        print('  tokens @0x3F0    %s' % ' '.join(d[0x3F0 + 6 * i:0x3F0 + 6 * i + 4].hex().upper()
                                                 for i in range(2)))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--map':
        for o, sz, name in MAP:
            n = sz if isinstance(sz, int) else {'b': 1, 'w': 2, 'd': 4, 'q': 8, 'f': 4}[sz]
            print('0x%03X..0x%03X  %-4s %s' % (o, o + n - 1, sz if isinstance(sz, str) else '%dB' % sz, name))
        sys.exit()
    for p in sys.argv[1:]:
        report(p)
