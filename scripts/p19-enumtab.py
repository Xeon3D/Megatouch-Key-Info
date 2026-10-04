"""p19-enumtab.py - recover a generated enum<->string table out of a Gen4 binary.

The Force/ION builds carry generated accessors `xml_<ns>::enum_<Enum>_tag(Enum, bool)`
and `enum_<Enum>_value(const char*)`. The _tag function indexes an array of string
pointers by the enum value, so reading that array in order yields the full id -> name
table (game ids, game-option indices, ...).

Strategy: find the _tag symbol, disassemble it to locate the pointer array it indexes
(a `lea`/`mov` off the GOT base plus `*4` scaling), then walk the array in the ELF's
data section following each pointer to its string.

usage: p19-enumtab.py <binary> <symbol-substring> [max_entries]
   e.g. p19-enumtab.py analysis/p19/bin/I2014/start enum_GameIds_tag 320
"""
import sys, os, re, subprocess, struct, json

WSL = ['wsl', 'bash', '-c']


def sh(cmd):
    return subprocess.run(WSL + [cmd], capture_output=True, text=True).stdout


def wslpath(p):
    p = os.path.abspath(p).replace('\\', '/')
    return '/mnt/' + p[0].lower() + p[2:]


def elf_sections(binw):
    out = sh("readelf -W -S '%s'" % binw)
    secs = []
    for m in re.finditer(r'\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', out):
        secs.append((m.group(1), int(m.group(3), 16), int(m.group(4), 16), int(m.group(5), 16)))
    return secs  # name, addr, offset, size


def vaddr_to_off(secs, va):
    for name, addr, off, size in secs:
        if addr and addr <= va < addr + size:
            return off + (va - addr)
    return None


def main():
    path, sym = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    binw = wslpath(path)
    data = open(path, 'rb').read()
    secs = elf_sections(binw)

    # locate the symbol: parse readelf's own columns, matching the MANGLED name
    syms = sh("readelf -W --dyn-syms '%s'" % binw)
    cand = []
    for l in syms.splitlines():
        f = l.split()
        if len(f) >= 8 and f[3] == 'FUNC' and sym in f[7]:
            cand.append((int(f[1], 16), int(f[2]), f[7]))
    if not cand:
        print('symbol %s not found' % sym)
        return
    addr, size, mangled = max(cand, key=lambda c: c[1])
    print('%s (%s) @ 0x%x size %d' % (sym, mangled, addr, size))

    asm = sh("objdump -d --start-address=0x%x --stop-address=0x%x -M intel '%s'"
             % (addr, addr + size, binw))
    print(asm[:1800])

    # candidate table addresses: any 32-bit displacement used with *4 scaling or lea
    cands = set()
    for m in re.finditer(r'(?:lea|mov)\s+\w+,(?:DWORD PTR )?\[\w+(?:\+\w+\*4)?([+-]0x[0-9a-f]+)\]', asm):
        cands.add(int(m.group(1), 16))
    gotbase = None
    m = re.search(r'add\s+ebx,0x([0-9a-f]+)', asm)
    pcrel = None
    m2 = re.search(r'^\s*([0-9a-f]+):\s+5b\s+pop\s+ebx', asm, re.M)
    if m and m2:
        pcrel = int(m2.group(1), 16) + int(m.group(1), 16)
        print('GOT/PIC base = 0x%x' % pcrel)
    print('displacements seen:', ' '.join(hex(c) for c in sorted(cands)))

    # try each candidate as a string-pointer array at pic_base + disp
    best = None
    for disp in sorted(cands):
        for base in filter(None, [pcrel]):
            tbl = base + disp
            off = vaddr_to_off(secs, tbl)
            if off is None:
                continue
            names, bad = [], 0
            for i in range(limit):
                if off + 4 * i + 4 > len(data):
                    break
                ptr = struct.unpack_from('<I', data, off + 4 * i)[0]
                so = vaddr_to_off(secs, ptr)
                if so is None:
                    bad += 1
                    break
                end = data.index(b'\0', so)
                s = data[so:end].decode('latin1')
                if not s or len(s) > 64 or not re.fullmatch(r'[A-Za-z0-9_]+', s):
                    bad += 1
                    break
                names.append(s)
            if len(names) > (len(best[1]) if best else 3):
                best = (tbl, names)
    if not best:
        print('no plausible string table found')
        return
    tbl, names = best
    print('\ntable at 0x%x : %d entries' % (tbl, len(names)))
    for i, n in enumerate(names):
        print('  %3d 0x%03X  %s' % (i, i, n))
    out = os.path.join('analysis', 'p19', 'json',
                       '%s.%s.json' % (os.path.basename(os.path.dirname(path)), sym))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({i: n for i, n in enumerate(names)}, open(out, 'w'), indent=1)
    print('wrote', out)


if __name__ == '__main__':
    main()
