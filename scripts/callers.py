# callers.py flat.bin target_hex... : list E8 rel32 call sites to target(s)
import sys, struct
img = open(sys.argv[1], 'rb').read(); base = 0x10000
for t in sys.argv[2:]:
    t = int(t, 16); out = []
    for i in range(len(img) - 5):
        if img[i] == 0xe8 and base + i + 5 + struct.unpack_from('<i', img, i + 1)[0] == t: out.append(hex(base + i))
    print(hex(t), out[:30])
