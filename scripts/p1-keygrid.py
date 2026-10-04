# Print every unique decrypted key as aligned subkey rows for cross-version field comparison.
import sys, os, glob, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
seen = {}
for root in sys.argv[1:]:
    for p in glob.glob(os.path.join(root, '**', '*'), recursive=True):
        if not os.path.isfile(p) or os.path.getsize(p) not in (256, 264): continue
        img, ser = mtkey.load_full(p)
        for s, d in mtkey.try_all(img, ser):
            seen.setdefault(d, (s, ser, os.path.basename(p)))
def row(b): return ' '.join(b[i:i+4].hex() for i in range(0, len(b), 4))
for d, (s, ser, n) in sorted(seen.items(), key=lambda kv: kv[0][:8]):
    print(f'### {d[:8].decode("latin1")} {d[56:64].decode("latin1")} {d[112:115].decode("latin1")!r}  {s}  {ser}  {n}')
    print('  D0', row(d[8:56])); print('  D1', row(d[64:112])); print('  D2', row(d[120:168])); print('  SC', row(d[168:232]))
