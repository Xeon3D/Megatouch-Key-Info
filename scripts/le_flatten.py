# Flatten a Watcom/CauseWay LE executable into a raw image at the objects' preferred bases,
# applying internal fixups. Output: <out>.bin (raw, starts at lowest object base) + prints base.
# Usage: le_flatten.py in.exe out.bin   (prints input + output SHA256)
import struct, sys, hashlib
src, dst = sys.argv[1], sys.argv[2]
b = open(src, 'rb').read()
off = struct.unpack_from('<I', b, 0x3c)[0]
if b[off:off+2] != b'LE': off = b.find(b'LE\x00\x00')
h = lambda o: struct.unpack_from('<I', b, off + o)[0]
npages, pgsz, lastpg = h(0x14), h(0x28), h(0x2c)
objtab, nobj, pgtab, fixpg, fixrec, datapg = h(0x40), h(0x44), h(0x48), h(0x68), h(0x6c), h(0x80)
objs = [struct.unpack_from('<6I', b, off + objtab + i*24) for i in range(nobj)]
lo = min(o[1] for o in objs); hi = max(o[1] + ((o[0] + pgsz - 1)//pgsz)*pgsz for o in objs)
img = bytearray(hi - lo)
page_va = {}
for oi, (vs, base, fl, pidx, pcnt, _) in enumerate(objs):
    for k in range(pcnt):
        p = pidx + k  # 1-based
        e = b[off+pgtab+(p-1)*4: off+pgtab+(p-1)*4+4]
        n = (e[0] << 16) | (e[1] << 8) | e[2]   # LE: 3-byte page number (big-endian-ish), 1 byte flags
        fo = datapg + (n-1)*pgsz
        sz = lastpg if p == npages else pgsz
        va = base + k*pgsz
        img[va-lo: va-lo+sz] = b[fo: fo+sz]
        page_va[p] = va
nfix = 0; unk = 0; imports = []; code_tgts = set()
for p in range(1, npages+1):
    a = struct.unpack_from('<I', b, off+fixpg+(p-1)*4)[0]; z = struct.unpack_from('<I', b, off+fixpg+p*4)[0]
    r = off + fixrec + a; end = off + fixrec + z
    while r < end:
        st, fl = b[r], b[r+1]; r += 2
        if st & 0x20:
            cnt = b[r]; r += 1
        else:
            soffs = [struct.unpack_from('<h', b, r)[0]]; r += 2
        if fl & 3 == 1:  # import by ordinal: record and skip (left unresolved in image)
            mod = struct.unpack_from('<H', b, r)[0] if fl & 0x40 else b[r]; r += 2 if fl & 0x40 else 1
            if fl & 0x80: ordn = b[r]; r += 1
            elif fl & 0x10: ordn = struct.unpack_from('<I', b, r)[0]; r += 4
            else: ordn = struct.unpack_from('<H', b, r)[0]; r += 2
            add = 0
            if fl & 4:
                add = struct.unpack_from('<i' if fl & 0x20 else '<h', b, r)[0]; r += 4 if fl & 0x20 else 2
            if st & 0x20: soffs = list(struct.unpack_from('<%dh' % cnt, b, r)); r += 2*cnt
            for so in soffs: imports.append((page_va[p] + so, mod, ordn, st & 0xf, add))
            continue
        if fl & 3 != 0:
            print(f'non-internal fixup page {p} st={st:#x} fl={fl:#x} rec@{r-2:#x}'); unk += 1; break
        if fl & 0x40: tobj = struct.unpack_from('<H', b, r)[0]; r += 2
        else: tobj = b[r]; r += 1
        t = st & 0xf
        if t == 2: toff = 0
        elif fl & 0x10: toff = struct.unpack_from('<I', b, r)[0]; r += 4
        else: toff = struct.unpack_from('<H', b, r)[0]; r += 2
        if st & 0x20:
            soffs = list(struct.unpack_from('<%dh' % cnt, b, r)); r += 2*cnt
        tgt = objs[tobj-1][1] + toff
        if t == 7 and objs[tobj-1][2] & 4: code_tgts.add(tgt)
        for so in soffs:
            va = page_va[p] + so
            if va < lo or va + 4 > hi: continue
            if t == 7: struct.pack_into('<I', img, va-lo, tgt)
            elif t == 8: struct.pack_into('<i', img, va-lo, tgt - (va + 4))
            elif t == 5: struct.pack_into('<H', img, va-lo, toff & 0xffff)
            elif t == 2: struct.pack_into('<H', img, va-lo, tobj)  # selector: object number
            elif t in (3, 6): struct.pack_into('<I', img, va-lo, toff); struct.pack_into('<H', img, va-lo+4, tobj) if t == 6 else None
            else: print(f'unhandled src type {t} at {va:#x}'); unk += 1
            nfix += 1
open(dst, 'wb').write(img)
eobj, eip = h(0x18), h(0x1c)
print(f'base={lo:#x} size={len(img):#x} entry={objs[eobj-1][1]+eip:#x} fixups={nfix} imports={len(imports)} unhandled={unk}')
impmod = h(0x70); nmod = h(0x74); r = off + impmod; mods = []
for _ in range(nmod): n = b[r]; mods.append(b[r+1:r+1+n].decode('latin1')); r += 1 + n
with open(dst + '.imports.txt', 'w') as f:
    for va, m, o, t, a in imports: f.write(f'{va:08x} {mods[m-1] if 0 < m <= len(mods) else m}:{o} type{t} +{a:#x}\n')
print(' import modules:', mods)
import re  # Watcom prologue scan: run of push-reg bytes ending in "push ebp; mov ebp,esp", after ret/pad
for (vs, base, fl, *_ ) in objs:
    if not fl & 4: continue
    seg = img[base-lo: base-lo+vs]
    for m in re.finditer(rb'(?<=[\xc3\x00\x90])[\x50-\x57]{0,6}\x55\x89\xe5', seg):
        code_tgts.add(base + m.start())
open(dst + '.seeds.txt', 'w').write(''.join(f'{a:x}\n' for a in sorted(code_tgts)))
print(' code-pointer seeds:', len(code_tgts))
for i,o in enumerate(objs): print(f' obj{i+1} {o[1]:#x}+{o[0]:#x} flags={o[2]:#x}')
print('in ', hashlib.sha256(b).hexdigest()); print('out', hashlib.sha256(img).hexdigest())
