# p16-dosarrays.py <SETUP.DLL> <MEGACDLL exports.txt> : list NVRAM arrays indexed in DOS SETUP.DLL.
# For every _NVRAMDATA import fixup, look back up to 12 bytes for an `imul reg,reg,imm` (6B /r ib or
# 69 /r id); the immediate is the record stride, the fixup additive the record base + field offset.
# Prints: stride, additive, field offset relative to the lowest additive of that stride, ref count.
import sys, os, subprocess, tempfile, collections, struct
dll, exf = sys.argv[1:3]
ordn = next(int(l.split()[2]) for l in open(exf) if l.split()[1] == '_NVRAMDATA')
tmp = os.path.join(tempfile.gettempdir(), 'p16_setup_flat.bin')
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), 'le_flatten.py'), dll, tmp], capture_output=True)
img = open(tmp, 'rb').read(); BASE = 0x10000
hits = collections.defaultdict(collections.Counter)
for l in open(tmp + '.imports.txt'):
    va, mo, t, add = l.split()
    if not mo.endswith(f':{ordn}'): continue
    o = int(va, 16) - BASE; a = int(add[1:], 16)
    for k in range(o - 12, o - 2):
        if img[k] == 0x6B and img[k + 1] >> 6 == 3:
            hits[img[k + 2]][a] += 1; break
        if img[k] == 0x69 and img[k + 1] >> 6 == 3:
            hits[struct.unpack_from('<I', img, k + 2)[0]][a] += 1; break
for stride in sorted(hits):
    adds = sorted(hits[stride]); lo = adds[0]
    print(f'stride {stride:#06x}: ' + ' '.join(f'{a:#06x}(+{a - lo:#x})x{hits[stride][a]}' for a in adds))
