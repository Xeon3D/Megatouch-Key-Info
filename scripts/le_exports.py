# le_exports.py in.exe out.txt : list exported names of a Watcom/CauseWay LE image as "VA name"
# (resident + non-resident name tables resolved through the entry table).
import struct, sys
b = open(sys.argv[1], 'rb').read()
off = struct.unpack_from('<I', b, 0x3c)[0]
if b[off:off+2] != b'LE': off = b.find(b'LE\x00\x00')
h = lambda o: struct.unpack_from('<I', b, off + o)[0]
objtab, nobj = h(0x40), h(0x44)
objs = [struct.unpack_from('<6I', b, off + objtab + i*24) for i in range(nobj)]

# entry table: bundles of (count, type, [object], entries)
entries = {}; r = off + h(0x5c); ordinal = 1
while True:
    cnt = b[r]; r += 1
    if cnt == 0: break
    typ = b[r]; r += 1
    if typ == 0: ordinal += cnt; continue
    obj = struct.unpack_from('<H', b, r)[0]; r += 2
    size = {1: 3, 2: 5, 3: 5, 4: 7}[typ & 0x7f]
    for _ in range(cnt):
        flags = b[r]
        if typ & 0x7f == 3: o = struct.unpack_from('<I', b, r + 1)[0]
        elif typ & 0x7f in (1, 2): o = struct.unpack_from('<H', b, r + 1)[0]
        else: o = None
        if o is not None and 0 < obj <= len(objs): entries[ordinal] = objs[obj-1][1] + o
        r += size; ordinal += 1

def names(start, end=None):
    r = start; out = []
    while True:
        n = b[r]
        if n == 0 or (end and r >= end): break
        nm = b[r+1:r+1+n].decode('latin1'); o = struct.unpack_from('<H', b, r+1+n)[0]
        out.append((o, nm)); r += 3 + n
    return out

allnames = names(off + h(0x58))
if h(0x88): allnames += names(h(0x88), h(0x88) + h(0x8c))
rows = sorted((entries[o], nm, o) for o, nm in allnames if o in entries)
with open(sys.argv[2], 'w') as f:
    for va, nm, o in rows: f.write(f'{va:06x} {nm} {o}\n')
print(len(rows), 'exports')
