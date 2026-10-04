# Decode the 80 two-bit option states (Gen3 D2[0..0x13]) for Jade/Crown keys and show differences.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
names = {}
for l in open('F:/MTKeyWork/analysis/p4_options_table.txt'):
    p = l.split(None, 2); names[int(p[0])] = p[2].strip()[:60] if len(p) > 2 else ''
keys = [('JADE 0900', 'F:/MTKeyWork/Key Info & Dumps/New Keys/MAXX Jade/MJADE_full_0900400002B65782'),
        ('JADE 4700', 'F:/MTKeyWork/Key Info & Dumps/New Keys/MAXX Jade/MJADE_full_4700400002501B82'),
        ('CROWN USA', 'F:/TouchPPBox Folder/keys/MCROWN_full_FF004000036F1F82'),
        ('CROWN CAN', 'F:/MTKeyWork/Key Info & Dumps/New Keys/MAXX Crown/Crown CAN-VER2/MCROWN_full_6D000000CB053702')]
st = {}
for n, p in keys:
    img, ser = mtkey.load_full(p); (s, d), = mtkey.try_all(img, ser); D2 = d[120:168]
    st[n] = [(D2[i // 4] >> (6 - 2 * (i % 4))) & 3 for i in range(80)]
print('idx  ' + ' '.join(n[:9].ljust(9) for n in st))
for i in range(80):
    row = [st[n][i] for n in st]
    mark = '  <== differs' if len(set(row)) > 1 else ''
    print(f'0x{i:02x} ' + ' '.join(str(v).ljust(9) for v in row) + f' {names.get(i, "")}{mark}')
