# For each flat DOS image: find "mov esi,imm32; movsd; movsd" + byte add/sub/inc/dec on [ebp+disp8]
# (the obfuscated 8-byte key signature) and print the de-obfuscated value.
import glob, os, re, struct
for f in sorted(glob.glob('F:/MTKeyWork/analysis/flat/*.bin')):
    img = open(f, 'rb').read(); base = 0x10000; out = []
    for m in re.finditer(rb'\xbe(....)\xa5\xa5', img, re.S):
        src = struct.unpack('<I', m.group(1))[0]
        if not base <= src < base + len(img): continue
        # destination frame slot from the preceding lea edi,[ebp+disp8] (8d 7d xx)
        pre = img[m.start()-3:m.start()]
        if pre[:2] != b'\x8d\x7d': continue
        dst = struct.unpack('b', pre[2:3])[0]
        val = bytearray(img[src-base: src-base+8]); i = m.end(); ops = 0
        while True:
            op = img[i:i+2]
            if op == b'\xc6\x45': i += 4; continue                     # movb $x,[ebp+d] (terminator write) skip
            if op in (b'\x80\x6d', b'\x80\x45'):
                d = struct.unpack('b', img[i+2:i+3])[0] - dst; k = img[i+3]
                if 0 <= d < 8: val[d] = (val[d] + (k if op == b'\x80\x45' else -k)) & 0xff; ops += 1
                i += 4; continue
            if op in (b'\xfe\x45', b'\xfe\x4d'):
                d = struct.unpack('b', img[i+2:i+3])[0] - dst
                if 0 <= d < 8: val[d] = (val[d] + (1 if op == b'\xfe\x45' else -1)) & 0xff; ops += 1
                i += 3; continue
            break
        if ops >= 4: out.append(f'{base+m.start():#x}:{bytes(val).hex()}({bytes(val)!r})')
    print(f'{os.path.basename(f)[:-4]:30} ' + ' '.join(out))
