# Find 4 consecutive "movb $imm, [abs]" to consecutive addresses (blkVCode init) in each flat image.
import glob, os, re, struct
for f in sorted(glob.glob('F:/MTKeyWork/analysis/flat/*.bin')):
    img = open(f, 'rb').read(); hits = []
    for m in re.finditer(rb'(\xc6\x05(....)(.)){4}', img, re.S):
        seg = img[m.start():m.end()]
        addrs = [struct.unpack('<I', seg[i*7+2:i*7+6])[0] for i in range(4)]
        vals = bytes(seg[i*7+6] for i in range(4))
        if addrs == [addrs[0]+i for i in range(4)]:
            hits.append(f'{0x10000+m.start():#x}:{vals.hex()}@{addrs[0]:#x}')
    print(f'{os.path.basename(f)[:-4]:28}', ' '.join(hits[:6]))
