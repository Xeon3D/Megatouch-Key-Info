# p2-signatures.py: for every flat DOS image, find the key-gate function (the one referencing
# "Invalid Key"), locate "mov esi,imm32; movsd; movsd" (8-byte signature copy), then emulate the
# byte-obfuscation ops that follow (add/sub/inc/dec/shl1/unsigned >>1 />>2) up to the first call.
# A "cmp $imm,%eax; jne" before the ops means the transform is conditional (record raw AND transformed).
import glob, os, re, struct, json
BASE = 0x10000
def xrefs(img, s):
    out = []
    for m in re.finditer(re.escape(s), img):
        va = BASE + m.start(); p = struct.pack('<I', va); i = img.find(p)
        while i >= 0: out.append(i); i = img.find(p, i + 1)
    return out
def funcstart(img, off):
    best = None
    for m in re.finditer(rb'(?<=[\xc3\x00\x90])[\x50-\x57]{0,6}\x55\x89\xe5', img[max(0, off-0x3000):off]):
        best = max(0, off-0x3000) + m.start()
    return best
res = {}
for f in sorted(glob.glob('F:/MTKeyWork/analysis/flat/*.bin')):
    img = open(f, 'rb').read(); name = os.path.basename(f)[:-4]; found = []
    for x in xrefs(img, b'Invalid Key'):
        fs = funcstart(img, x)
        if fs is None: continue
        m = re.search(rb'\xbe(....)\xa5\xa5', img[fs:fs+0x80], re.S)
        if not m: continue
        src = struct.unpack('<I', m.group(1))[0]; raw = bytes(img[src-BASE: src-BASE+8])
        i = fs + m.end(); slot0 = None; v = bytearray(raw); cond = None; ops = []
        lea = re.search(rb'\x8d\x7d(.)', img[fs:fs+m.start()], re.S)
        slot0 = struct.unpack('b', lea.group(1))[0] if lea else None
        end = img.find(b'\xe8', i)  # first call
        code = img[i:end]
        cm = re.search(rb'\x83\xf8(.)\x75', code, re.S)
        if cm: cond = code[cm.start()-5:cm.start()].hex() + f' cmp {cm.group(1)[0]:#x}'
        for om in re.finditer(rb'\x80([\x6d\x45])(.)(.)|\xfe([\x45\x4d])(.)|\xd0\x65(.)|\x8a\x55(.).{4,10}?(\xd1\xf8|\xc1\xf8\x02).{0,4}?\x88\x55(.)|\x8a\x5d(.).{4,14}?(\xd1\xf8|\xc1\xf8\x02).{0,4}?\x88\x5d(.)', code, re.S):
            g = om.groups()
            if g[0]: d = struct.unpack('b', g[1])[0]-slot0; k = g[2][0]; v[d] = (v[d] + (k if g[0] == b'\x45' else -k)) & 0xff; ops.append(f'{"add" if g[0]==b"E" else "sub"}[{d}],{k:#x}')
            elif g[3]: d = struct.unpack('b', g[4])[0]-slot0; v[d] = (v[d] + (1 if g[3] == b'\x45' else -1)) & 0xff; ops.append(f'{"inc" if g[3]==b"E" else "dec"}[{d}]')
            elif g[5]: d = struct.unpack('b', g[5])[0]-slot0; v[d] = (v[d] << 1) & 0xff; ops.append(f'shl[{d}]')
            else:
                rd_, sh, wr = (g[6], g[7], g[8]) if g[6] else (g[9], g[10], g[11])
                d = struct.unpack('b', wr)[0]-slot0; n = 1 if sh == b'\xd1\xf8' else 2; v[d] >>= n; ops.append(f'shr[{d}],{n}')
        found.append(dict(gate=hex(BASE+fs), raw=raw.hex(), xformed=bytes(v).hex() if ops else None, cond=cond, ops=ops))
    uniq = {json.dumps(x, sort_keys=True): x for x in found}
    res[name] = list(uniq.values())
    for x in res[name]:
        print(f'{name:28} gate={x["gate"]} raw={x["raw"]} {bytes.fromhex(x["raw"])!r}' +
              (f' -> {x["xformed"]} cond={x["cond"]}' if x['xformed'] else ''))
json.dump(res, open('F:/MTKeyWork/analysis/p2/signatures.json', 'w'), indent=1)
