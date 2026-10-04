# xref.py flat.bin base 'substring' -> string VAs and code locations that embed the VA as imm32
import sys, struct, re
img = open(sys.argv[1], 'rb').read(); base = int(sys.argv[2], 0); pat = sys.argv[3].encode()
for m in re.finditer(re.escape(pat), img):
    s = m.start()
    while s > 0 and 0x20 <= img[s-1] < 0x7f: s -= 1
    va = base + s; e = img.find(b'\0', s)
    refs = [base + i for i in range(len(img) - 4) if struct.unpack_from('<I', img, i)[0] == va]
    print(f'{va:#x} {img[s:e][:60]!r} refs: {" ".join(hex(r) for r in refs[:12])}')
