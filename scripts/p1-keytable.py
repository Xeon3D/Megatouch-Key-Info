# Tabulate all decrypted DS1991 Megatouch key dumps (232-byte layout).
import os, sys, hashlib, json
ROOT = sys.argv[1]
rows = {}
for dp, _, fs in os.walk(ROOT):
    for f in fs:
        p = os.path.join(dp, f)
        b = open(p, 'rb').read()
        if len(b) != 232: continue
        h = hashlib.sha256(b).hexdigest()[:12]
        r = rows.setdefault(h, dict(paths=[], hex=b.hex()))
        r['paths'].append(os.path.relpath(p, ROOT))
        r.update(id0=b[0:8].decode('latin1'), id1=b[0x38:0x40].decode('latin1'),
                 id2=b[0x70:0x78].decode('latin1'),
                 d0=b[8:0x38].hex(), d1=b[0x40:0x70].hex(), d2=b[0x78:0xa8].hex(), scr=b[0xa8:].hex())
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
for h, r in sorted(rows.items(), key=lambda kv: kv[1]['id0']):
    print(h, repr(r['id0']), repr(r['id1']), repr(r['id2']), os.path.basename(r['paths'][0]), len(r['paths']))
