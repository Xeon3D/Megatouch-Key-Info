"""keyinfo.py - human-readable dump of a Megatouch key (Gen 3: Sapphire/Jade/Crown fully; older: IDs + options).

usage: keyinfo.py <key dump (*_full_* or 256 B + serial)> [--games <gamedata.dat>]
Game names come from the matching version's /usr/local/share/merit/config/gamedata.dat
(see analysis/p14/*.gamedata.dat); without it, game IDs are printed.
"""
import sys, os, re, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey, gamedata

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
def slot_names():
    names, cls = {}, {}
    p = os.path.join(ROOT, 'Docs', '04-territory-options.md')
    for l in open(p, encoding='utf-8'):
        m = re.match(r'\| 0x([0-9A-F]{2}) \| (.+?) \| \d', l)
        if m and int(m.group(1), 16) not in names: names[int(m.group(1), 16)] = m.group(2)
    p = os.path.join(ROOT, 'analysis', 'p10', 'slot_classes_final.tsv')
    if os.path.exists(p):
        for l in open(p, encoding='utf-8').read().splitlines()[1:]:
            q = l.split('\t'); cls[int(q[0], 16)] = q[1]
    return names, cls

def main():
    path = sys.argv[1]; games = {}
    if '--games' in sys.argv:
        games = {g['id']: g for g in gamedata.parse(sys.argv[sys.argv.index('--games') + 1])}
    img, ser = mtkey.load_full(path)
    hits = mtkey.try_all(img, ser)
    if not hits: print('key does not decrypt with any known scheme'); return
    scheme, d = hits[0]; D0, D1, D2, SC = d[8:56], d[64:112], d[120:168], d[168:232]
    rom = bytes.fromhex(ser)[::-1]
    s48 = int.from_bytes(rom[1:7][::-1], 'big')
    print(f'Key {d[:8].decode("latin1")}  date {d[56:64].decode("latin1")}  rev {d[112:120].split(b"\0")[0].decode("latin1").strip()}  scheme {scheme}')
    print(f'Serial {ser}  family {rom[0]:#04x}  48-bit serial {s48:012X}')
    gen3 = D0[0x28:0x30] in (bytes.fromhex('8723879fe2432498'), bytes.fromhex('8723879fe2432487'), bytes.fromhex('1234567890abcdef'))
    jade = D0[0x28:0x30] != bytes.fromhex('1234567890abcdef')
    print(f'Signature {D0[0x28:0x30].hex() if gen3 else D0[0:8].hex()}  ({"Gen 3" if gen3 else "Gen 1/2"})')
    if gen3 and jade:
        terr = D1[0x20:0x2a].split(b'\0')[0].decode('latin1'); cc = D1[0x2e]
        print(f'Territory {terr!r}  country code {cc}')
        print(f'TournaMAXX game cost {D0[1] & 0x1f}, prize mode {D0[1] >> 5 & 3}, prize rate {(D0[2] & 0xf) * 2 | D0[1] >> 7}')
        print(f'Default language mask {struct.unpack_from("<I", D0, 3)[0]:#010x}  lockout {D0[0x27]}')
        print('Coin channels (a/b/c):', ' '.join(f'{D0[7+4*i]}/{D0[8+4*i]}/{D0[9+4*i]}' for i in range(6)))
        cur = [SC[8*i:8*i+8].split(b'\0')[0].decode('latin1') for i in range(6)]
        if any(cur): print('Currency names:', cur)
        # price list
        price = None; plist = []
        for x in D1[:0x1c]:
            if x == 0xFF: break
            if x >= 0xF0: price = x & 0xF; continue
            plist.append((x, price))
        print(f'Default price {D1[0x2a]}  (premium games {D1[0x1f]})')
        print('Game prices on key:', ', '.join(f'{games.get(g, {}).get("description", hex(g))}={p}' for g, p in plist))
        en = [g for g in range(0xE0) if D2[0x14 + g // 8] & (0x80 >> (g & 7))]
        print(f'Enabled games ({len(en)}):')
        for g in en:
            gi = games.get(g)
            print(f'   {g:#04x} {gi["description"] if gi else ""}' + (f'  [{",".join(gi["flags"])}]' if gi and gi['flags'] else ''))
    names, cls = slot_names()
    lab = {0: 'locked off', 1: 'locked ON', 2: 'selectable, default off', 3: 'selectable, default on'}
    print('Options:')
    for i in range(80):
        st = (D2[i // 4] >> (6 - 2 * (i % 4))) & 3
        print(f'   {i:#04x} {lab[st]:24} {names.get(i, "")[:44]:44} {cls.get(i, "")}')

if __name__ == '__main__':
    main()
