# immref.py flat.bin base hexval [hexval...] : list code offsets where imm32/disp32 == value
import sys, struct
img = open(sys.argv[1], 'rb').read(); base = int(sys.argv[2], 0)
for v in sys.argv[3:]:
    v = int(v, 16); pat = struct.pack('<I', v); i = img.find(pat); out = []
    while i >= 0:
        out.append(f'{base+i:x}:{img[max(0,i-2):i].hex()}'); i = img.find(pat, i+1)
    print(hex(v), len(out), ' '.join(out[:60]))
