# Find the game descriptor table in Crown start.elf: locate module-name strings, then pointers to them,
# and infer a fixed stride -> (index, name) list.
import struct, re, sys
f = sys.argv[1]; b = open(f, 'rb').read()
phoff, = struct.unpack_from('<I', b, 0x1c); n, = struct.unpack_from('<H', b, 0x2c)
segs = [struct.unpack_from('<8I', b, phoff + 32*i) for i in range(n)]
def o2v(o):
    for t, off, v, _, fs, *_ in segs:
        if t == 1 and off <= o < off + fs: return v + o - off
def v2o(v):
    for t, off, va, _, fs, *_ in segs:
        if t == 1 and va <= v < va + fs: return off + v - va
names = ['airhockey', 'psolitaire', 'powertrivia', 'chess', 'checkerz', 'golf', 'euchre', 'hearts']
for nm in names:
    for m in re.finditer(rb'(?<=\x00)' + nm.encode() + rb'(?=\x00)', b):
        va = o2v(m.start()); p = struct.pack('<I', va)
        refs = [o2v(i) for i in range(len(b) - 4) if b[i:i+4] == p]
        print(nm, hex(va), [hex(r) for r in refs[:4]])
