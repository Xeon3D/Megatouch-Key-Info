# Territory table: part-number suffix vs territory name (generation-specific offset) vs Gen3 country code.
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
rows = {}
for root in sys.argv[1:]:
    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if not os.path.isfile(p) or os.path.getsize(p) not in (256, 264): continue
        img, ser = mtkey.load_full(p)
        for s, d in mtkey.try_all(img, ser):
            D0, D1, D2 = d[8:56], d[64:112], d[120:168]
            if D0[0x28:0x30] in (bytes.fromhex('8723879fe2432498'),):       gen, name, cc = 'G3-Jade/Crown', D1[0x20:0x2a], D1[0x2e]
            elif D0[0x28:0x30] == bytes.fromhex('1234567890abcdef'):        gen, name, cc = 'G3-Sapphire', D2[0x04:0x0e], None
            else:                                                           gen, name, cc = 'G1/G2', D2[0x18:0x22], None
            name = name.split(b'\0')[0].decode('latin1')
            rows[(d[:8], ser)] = (d[:8].decode(), d[6:8].decode(), name, cc, gen, s, ser)
for r in sorted(rows.values(), key=lambda r: (r[1], r[0])):
    print(f'{r[0]}  terr={r[1]}  name={r[2]!r:12} cc={r[3]}  {r[4]:14} {r[5]:15} {r[6]}')
