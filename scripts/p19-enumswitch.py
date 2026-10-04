"""p19-enumswitch.py - recover a generated enum<->string table from a switch-style
`enum_<Enum>_tag` function in libenums.so.

These functions are compiled as a jump table: the enum value indexes a table of code
offsets, and each case does `lea eax,[ebx - disp]; jmp end`, where ebx is the PIC base.
So:
  * parse the PIC base (`call next; pop ebx; add ebx,N`),
  * parse the jump table that `jmp DWORD PTR [ebx+eax*4-D]` indexes,
  * for each entry follow the case code to its `lea` and read the string.
That yields value -> name exactly as the enum declares it, with no ordering assumption.

usage: p19-enumswitch.py <lib> <enum_tag_symbol> [count]
"""
import sys, os, re, struct, json, subprocess


def sh(c):
    return subprocess.run(['wsl', 'bash', '-c', c], capture_output=True, text=True).stdout


def wslpath(p):
    p = os.path.abspath(p).replace('\\', '/')
    return '/mnt/' + p[0].lower() + p[2:]


def sections(binw):
    out = sh("readelf -W -S '%s'" % binw)
    return [(m.group(1), int(m.group(3), 16), int(m.group(4), 16), int(m.group(5), 16))
            for m in re.finditer(
                r'\[\s*\d+\]\s+(\S+)\s+(\S+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)', out)]


def off(secs, va):
    for _, addr, o, size in secs:
        if addr and addr <= va < addr + size:
            return o + (va - addr)
    return None


def cstr(data, secs, va):
    o = off(secs, va)
    if o is None:
        return None
    e = data.index(b'\0', o)
    s = data[o:e]
    try:
        s = s.decode('ascii')
    except UnicodeDecodeError:
        return None
    return s if 0 < len(s) <= 64 else None


def main():
    path, sym = sys.argv[1], sys.argv[2]
    binw = wslpath(path)
    data = open(path, 'rb').read()
    secs = sections(binw)

    syms = sh("readelf -W --dyn-syms '%s'" % binw)
    cand = [(int(f[1], 16), int(f[2]), f[7]) for f in (l.split() for l in syms.splitlines())
            if len(f) >= 8 and f[3] == 'FUNC' and sym in f[7] and int(f[1], 16)]
    if not cand:
        print('%s: %s not defined here' % (os.path.basename(path), sym))
        return
    addr, size, mangled = max(cand, key=lambda c: c[1])
    asm = sh("objdump -d --start-address=0x%x --stop-address=0x%x -M intel '%s'"
             % (addr, addr + size, binw))

    # PIC base: the instruction after the `call` plus the `add ebx,N`
    mpop = re.search(r'^\s*([0-9a-f]+):\s+5b\s+pop\s+ebx', asm, re.M)
    madd = re.search(r'add\s+ebx,0x([0-9a-f]+)', asm)
    if not (mpop and madd):
        print('no PIC base found')
        return
    base = int(mpop.group(1), 16) + int(madd.group(1), 16)

    # every `lea reg,[ebx-0xNNN]` paired with the instruction address
    leas = {}
    for m in re.finditer(r'^\s*([0-9a-f]+):(?:\s+[0-9a-f]{2})+\s+lea\s+\w+,\[ebx([+-]0x[0-9a-f]+)\]',
                         asm, re.M):
        leas[int(m.group(1), 16)] = base + int(m.group(2), 16)

    # jump table: `jmp DWORD PTR [ebx+eax*4-0xNNN]`
    mjt = re.search(r'jmp\s+DWORD PTR \[ebx\+\w+\*4([+-]0x[0-9a-f]+)\]', asm)
    table = {}
    if mjt:
        jt = base + int(mjt.group(1), 16)
        o = off(secs, jt)
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 400
        for i in range(n):
            if o is None or o + 4 * (i + 1) > len(data):
                break
            tgt = struct.unpack_from('<I', data, o + 4 * i)[0]
            if not (addr <= tgt < addr + size):
                break
            # the first lea at or after the case target holds this case's string
            nxt = min((a for a in leas if a >= tgt), default=None)
            s = cstr(data, secs, leas[nxt]) if nxt is not None else None
            if s is None:
                break
            table[i] = s
        print('jump table at 0x%x : %d cases' % (jt, len(table)))

    if not table:
        # fall back to address order of the string literals
        strs = []
        for a in sorted(leas):
            s = cstr(data, secs, leas[a])
            if s and s not in strs:
                strs.append(s)
        table = dict(enumerate(strs))
        print('no usable jump table; using %d literals in code order' % len(table))

    for i in sorted(table):
        print('  %3d 0x%03X  %s' % (i, i, table[i]))
    tag = os.path.basename(os.path.dirname(path))
    out = os.path.join('analysis', 'p19', 'json', '%s.%s.json' % (tag, sym))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(table, open(out, 'w'), indent=1)
    print('wrote %s (%d entries)' % (out, len(table)))


if __name__ == '__main__':
    main()
