# Decode u_m_m_s obfuscated strings in Crown start.elf: out[i] = s[i] if s[i]==key[i%len] else s[i]^key[i%len]
import sys, struct, subprocess
f = sys.argv[1]; b = open(f, 'rb').read()
phoff, = struct.unpack_from('<I', b, 0x1c); n, = struct.unpack_from('<H', b, 0x2c)
segs = [struct.unpack_from('<8I', b, phoff + 32*i) for i in range(n)]
def v2o(va):
    for t, o, v, _, fs, *_ in segs:
        if t == 1 and v <= va < v + fs: return va - v + o
def cstr(va):
    o = v2o(va); return b[o: b.index(b'\0', o)]
sym = {l.split()[7]: int(l.split()[1], 16) for l in subprocess.run(['readelf', '-Ws', '--dyn-syms', f], capture_output=True, text=True).stdout.splitlines() if len(l.split()) >= 8 and l.split()[0].rstrip(':').isdigit() and l.split()[1] != '00000000'}
key = cstr(struct.unpack_from('<I', b, v2o(sym['m_m_k']))[0])
print('key =', key)
def dec(s): return bytes(c if c == key[i % len(key)] else c ^ key[i % len(key)] for i, c in enumerate(s))
for a in sys.argv[2:]:
    va = int(a, 16); print(hex(va), dec(cstr(va)))
