# Locate laser-serial range checks: "cmp dword [ebp+d], imm32" (81 7d d imm32) and
# "cmp byte [reg], 0x82/0x02" family checks, near each other. Report imm32 clusters.
import glob, os, re, struct
files = sorted(glob.glob('F:/MTKeyWork/Executables/*/start.elf') + glob.glob('F:/MTKeyWork/Executables/*/start') + glob.glob('F:/MTKeyWork/analysis/flat/*.bin'))
for f in files:
    b = open(f, 'rb').read()
    if b[:4] == b'\x7fELF' and os.path.basename(f) == 'start' and os.path.exists(os.path.join(os.path.dirname(f), 'start.elf')): continue
    hits = []
    for m in re.finditer(rb'\x80\x38\x82|\x80\x3a\x82|\x80\x39\x82|\x80\x7d.\x82|\x3c\x82', b, re.S):  # cmp byte [..],0x82 / cmp al,0x82
        win = b[m.start(): m.start() + 0x90]
        imms = [struct.unpack('<I', mm.group(1))[0] for mm in re.finditer(rb'\x81\x7d.(....)', win, re.S)]
        imms += [struct.unpack('<I', mm.group(1))[0] for mm in re.finditer(rb'\x3d(....)', win, re.S)]
        imms = [i for i in imms if 0x100 <= i < 0x1000000]
        if len(imms) >= 2: hits.append((m.start(), [hex(i) for i in imms]))
    print(os.path.relpath(f, 'F:/MTKeyWork')[:50].ljust(50), hits[:4])
