# Print LE header + object table of a CauseWay/Watcom LE executable.
import struct, sys
b = open(sys.argv[1], 'rb').read()
# find LE header: follow MZ chain (CauseWay stub) via e_lfanew at 0x3c
off = struct.unpack_from('<I', b, 0x3c)[0]
if b[off:off+2] != b'LE':
    off = b.find(b'LE\x00\x00')
print('LE at', hex(off))
h = lambda o, f='<I': struct.unpack_from(f, b, off + o)[0]
npages, eip_obj, eip, esp_obj, esp, pgsz, lastpg = h(0x14), h(0x18), h(0x1c), h(0x20), h(0x24), h(0x28), h(0x2c)
objtab, nobj, pgtab, fixpg, fixrec, datapg = h(0x40), h(0x44), h(0x48), h(0x68), h(0x6c), h(0x80)
print(f'pages={npages} pgsz={pgsz:#x} lastpg={lastpg:#x} eip={eip_obj}:{eip:#x} objs={nobj} datapages@{datapg:#x}')
for i in range(nobj):
    vs, base, fl, pidx, pcnt, _ = struct.unpack_from('<6I', b, off + objtab + i * 24)
    print(f' obj{i+1}: vsize={vs:#x} base={base:#x} flags={fl:#x} pages {pidx}..{pidx+pcnt-1}')
