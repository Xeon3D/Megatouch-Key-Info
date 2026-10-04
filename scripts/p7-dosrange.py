# Look for cmp-with-imm32 in the 0x400000..0x1000000 band in DOS flat images (possible laser-serial windows)
import glob, os, re, struct
for f in sorted(glob.glob('F:/MTKeyWork/analysis/flat/*.bin')):
    b = open(f, 'rb').read(); hits = []
    for m in re.finditer(rb'(\x81[\x78-\x7f].|\x3d|\x81[\xf8-\xff])(....)', b, re.S):
        v = struct.unpack('<I', m.group(2))[0]
        if 0x400000 <= v < 0x1000000 and v not in range(0x10000, 0x200000): hits.append(f'{0x10000+m.start():x}:{v:#x}')
    print(os.path.basename(f)[:-4].ljust(30), len(hits), ' '.join(hits[:12]))
