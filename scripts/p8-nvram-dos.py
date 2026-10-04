# p8-nvram-dos.py: per DOS version, locate _NVRAMDATA (exports), its size (memset in the
# default-init routine), the expected base version (cmp at NVRAM+9), and a reference map:
# every instruction whose absolute operand falls inside NVRAM -> offset, width, mnemonic, function.
# Writes analysis/p8/<ver>.nvmap.tsv and prints a summary table.
# Run in WSL (needs objdump):  python3 p8-nvram-dos.py
import glob, os, re, struct, subprocess, bisect, collections, json
FLAT = '/mnt/f/MTKeyWork/analysis/flat'; OUT = '/mnt/f/MTKeyWork/analysis/p8'; os.makedirs(OUT, exist_ok=True)
BASE = 0x10000
summary = []
for binf in sorted(glob.glob(f'{FLAT}/*.bin')):
    ver = os.path.basename(binf)[:-4]
    exf = f'{FLAT}/{ver}.exports.txt'
    if not os.path.exists(exf): continue
    exports = [(int(l.split()[0], 16), l.split()[1]) for l in open(exf)]
    nv = next((a for a, n in exports if n == '_NVRAMDATA'), None)
    if nv is None: summary.append((ver, None)); continue
    img = open(binf, 'rb').read()
    # size: "mov $imm32,%ebx ; mov $NV,%eax" (memset/memclr) within a few bytes
    sizes = collections.Counter()
    for m in re.finditer(rb'\xbb(....)(?:.{0,8})\xb8' + re.escape(struct.pack('<I', nv)), img, re.S):
        v = struct.unpack('<I', m.group(1))[0]
        if 0x100 <= v <= 0x10000: sizes[v] += 1
    size = sizes.most_common(1)[0][0] if sizes else 0x8000
    # base version: "mov NV+9,%al" (a0 addr) followed by cmp $imm,%eax (83 f8 imm)
    bv = collections.Counter(m.group(1)[0] for m in re.finditer(re.escape(b'\xa0' + struct.pack('<I', nv + 9)) + rb'.{0,4}?\x83\xf8(.)', img, re.S))
    basever = bv.most_common(1)[0][0] if bv else None
    # function starts: exports (named) + prologue scan (unnamed)
    starts = {a: n for a, n in exports if a < nv}
    for m in re.finditer(rb'(?<=[\xc3\x00\x90])[\x50-\x57]{0,6}\x55\x89\xe5', img[:nv - BASE]):
        starts.setdefault(BASE + m.start(), None)
    sk = sorted(starts)
    def func(a):
        i = bisect.bisect_right(sk, a) - 1
        if i < 0: return '?'
        s = sk[i]; return starts[s] or f'fn_{s:x}'
    # objdump linear sweep of the code object (first object)
    codeend = nv  # code precedes data in these images
    dis = subprocess.run(['objdump', '-D', '-b', 'binary', '-m', 'i386', '--adjust-vma=0x10000',
                          '--start-address=0x10000', f'--stop-address={codeend:#x}', binf],
                         capture_output=True, text=True).stdout
    refs = collections.defaultdict(list)
    rx = re.compile(r'^\s*([0-9a-f]+):\s+(?:[0-9a-f]{2} )+\s*(\S+)\s+(.*)$')
    # string table: printable NUL-terminated strings (>=3 chars) in the data part of the image
    strs = {}
    for m in re.finditer(rb'[\x20-\x7e]{3,60}\x00', img[nv - BASE - 0x80000 if nv - BASE > 0x80000 else 0:]):
        pass
    def string_at(va):
        o = va - BASE
        if not (0 <= o < len(img)) or (o and 0x20 <= img[o - 1] < 0x7f): return None
        e = img.find(b'\0', o, o + 80)
        s = img[o:e] if e > o else b''
        return s.decode('latin1') if len(s) >= 3 and all(0x20 <= c < 0x7f for c in s) else None
    lines = []
    for line in dis.splitlines():
        m = rx.match(line)
        if m: lines.append((int(m.group(1), 16), m.group(2), m.group(3)))
    ctx = collections.defaultdict(set)
    for i, (addr, mn, ops) in enumerate(lines):
        for h in re.findall(r'\$0x([0-9a-f]{5,6})', ops):
            s = string_at(int(h, 16))
            if s:
                for j in range(max(0, i - 12), min(len(lines), i + 12)):
                    ctx[lines[j][0]].add(s)
    for addr, mn, ops in lines:
        for h in re.findall(r'0x([0-9a-f]{5,6})', ops):
            v = int(h, 16)
            if nv <= v < nv + size:
                w = 'b' if mn.endswith('b') or re.search(r'%[abcd][lh]\b', ops) else ('w' if mn.endswith('w') or re.search(r'%[abcd]x\b|%[sd]i\b', ops) and not re.search(r'%e', ops) else 'd')
                refs[v - nv].append((addr, mn, w, func(addr)))
    with open(f'{OUT}/{ver}.nvmap.tsv', 'w') as f:
        f.write('offset\twidth\tnrefs\tstrings\tfunctions\n')
        for off in sorted(refs):
            r = refs[off]; fns = collections.Counter(x[3] for x in r)
            named = sorted({k for k in fns if not k.startswith('fn_')})
            sc = collections.Counter(s for x in r for s in ctx.get(x[0], ()))
            strs_ = ' | '.join(s for s, _ in sc.most_common(5)).replace('\t', ' ')
            f.write(f'{off:#06x}\t{collections.Counter(x[2] for x in r).most_common(1)[0][0]}\t{len(r)}\t{strs_}\t'
                    + ', '.join(named[:6] + [k for k, _ in fns.most_common(4) if k.startswith("fn_")]) + '\n')
    summary.append((ver, dict(nv=hex(nv), size=hex(size), basever=hex(basever) if basever is not None else None, offsets=len(refs))))
json.dump(summary, open(f'{OUT}/summary_dos.json', 'w'), indent=1)
for ver, d in summary: print(f'{ver:30} {d}')
