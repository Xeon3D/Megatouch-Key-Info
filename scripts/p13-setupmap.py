# p13-setupmap.py <SETUP.DLL> <MEGACDLL exports.txt (with ordinals)> <out.tsv>
# Map DOS operator-setup NVRAM accesses: every import fixup to _NVRAMDATA (by ordinal) gives an NVRAM
# offset (fixup additive); label it with the menu strings referenced near the access (+-0x60 bytes).
import sys, struct, re, collections, subprocess, os, tempfile
dll, exf, outp = sys.argv[1:4]
ordn = next(int(l.split()[2]) for l in open(exf) if l.split()[1] == '_NVRAMDATA')
tmp = os.path.join(tempfile.gettempdir(), 'setup_flat.bin')
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'le_flatten.py'), dll, tmp], capture_output=True)
img = open(tmp, 'rb').read(); BASE = 0x10000
def string_at(va):
    o = va - BASE
    if not (0 < o < len(img)) or 0x20 <= img[o - 1] < 0x7f: return None
    e = img.find(b'\0', o, o + 90)
    s = img[o:e] if e > o else b''
    return s.decode('latin1') if len(s) >= 3 and all(0x20 <= c < 0x7f for c in s) else None
refs = collections.defaultdict(list)
for l in open(tmp + '.imports.txt'):
    va, mo, t, add = l.split()
    if mo.endswith(f':{ordn}'):
        refs[int(add[1:], 16)].append(int(va, 16))
starts = sorted(BASE + m.start() for m in re.finditer(rb'(?<=[\xc3\x00\x90])[\x50-\x57]{0,6}\x55\x89\xe5', img))
import bisect
with open(outp, 'w', encoding='utf-8') as f:
    f.write('offset\tnrefs\tfunctions\tstrings\n')
    for off in sorted(refs):
        sc = collections.Counter(); fns = set()
        for va in refs[off]:
            i = bisect.bisect_right(starts, va) - 1; fns.add(f'fn_{starts[i]:x}' if i >= 0 else '?')
            o = va - BASE
            for k in range(max(0, o - 0x60), min(len(img) - 4, o + 0x60)):
                s = string_at(struct.unpack_from('<I', img, k)[0])
                if s: sc[s] += 1
        f.write(f'{off:#06x}\t{len(refs[off])}\t{",".join(sorted(fns))[:80]}\t' + ' | '.join(s for s, _ in sc.most_common(6)) + '\n')
print(os.path.basename(dll), 'ordinal', ordn, len(refs), 'NVRAM offsets')
