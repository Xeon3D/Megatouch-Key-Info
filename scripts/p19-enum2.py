"""p19-enum2.py - recover a generated enum table from libenums.so.

Shape of the generated `enum_<Enum>_tag(Enum, bool)` in these builds:

    call next ; pop REG ; add REG,N          -> PIC base = addr(next) + N
    cmp eax,<max> ; ja default
    mov eax,[REG+eax*4-D] ; add eax,REG ; jmp eax     (relative jump table at base-D)
  case_k:
    lea eax,[REG-A] ; test dl,dl ; jne ret   -> bool=true  returns string A (short tag)
    lea eax,[REG-B] ; ret                    -> bool=false returns string B (long label)

So each enum value yields a (tag, label) pair. Nothing about ordering is assumed: the
jump table indexes by the enum value directly.

usage: p19-enum2.py <lib.so> <enum_tag_symbol>
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


def foff(secs, va):
    for _, addr, o, size in secs:
        if addr and addr <= va < addr + size:
            return o + (va - addr)
    return None


def cstr(data, secs, va):
    o = foff(secs, va)
    if o is None:
        return None
    try:
        e = data.index(b'\0', o)
    except ValueError:
        return None
    try:
        s = data[o:e].decode('ascii')
    except UnicodeDecodeError:
        return None
    return s if 0 < len(s) <= 80 else None


def extract(path, sym):
    binw = wslpath(path)
    data = open(path, 'rb').read()
    secs = sections(binw)
    syms = sh("readelf -W --dyn-syms '%s'" % binw)
    cand = [(int(f[1], 16), int(f[2]), f[7]) for f in (l.split() for l in syms.splitlines())
            if len(f) >= 8 and f[3] == 'FUNC' and sym in f[7] and int(f[1], 16)]
    if not cand:
        return None, '%s not defined in %s' % (sym, os.path.basename(path))
    addr, size, _ = max(cand, key=lambda c: c[1])
    asm = sh("objdump -d --start-address=0x%x --stop-address=0x%x -M intel '%s'"
             % (addr, addr + size, binw))

    m = re.search(r'^\s*([0-9a-f]+):\s+5[89b]\s+pop\s+(e\w\w)\s*$', asm, re.M)
    if not m:
        return None, 'no pop REG'
    reg = m.group(2)
    m2 = re.search(r'add\s+%s,0x([0-9a-f]+)' % reg, asm)
    if not m2:
        return None, 'no add %s' % reg
    base = int(m.group(1), 16) + int(m2.group(1), 16)

    # all leas, by instruction address
    leas = {}
    for mm in re.finditer(
            r'^\s*([0-9a-f]+):(?:\s+[0-9a-f]{2})+\s+lea\s+eax,\[%s([+-]0x[0-9a-f]+)\]' % reg,
            asm, re.M):
        leas[int(mm.group(1), 16)] = base + int(mm.group(2), 16)
    order = sorted(leas)

    def pair_at(tgt):
        cases = [a for a in order if a >= tgt][:2]
        p = [cstr(data, secs, leas[a]) for a in cases]
        if not p or p[0] is None:
            return None
        return {'tag': p[0], 'label': p[1] if len(p) > 1 else None}

    table = {}
    mjt = re.search(r'mov\s+eax,DWORD PTR \[%s\+\w+\*4([+-]0x[0-9a-f]+)\]' % reg, asm)
    if mjt:
        jt = base + int(mjt.group(1), 16)
        mmax = re.search(r'cmp\s+eax,0x([0-9a-f]+)', asm)
        nmax = int(mmax.group(1), 16) + 1 if mmax else 256
        o = foff(secs, jt)
        for i in range(nmax):
            tgt = base + struct.unpack_from('<i', data, o + 4 * i)[0]
            if not (addr <= tgt < addr + size):
                continue
            p = pair_at(tgt)
            if p:
                table[i] = p
        return table, 'jump table 0x%x, %d of %d values defined' % (jt, len(table), nmax)

    # sparse enum: a comparison tree. A value's leaf is reached either by an exact
    # `cmp eax,V ; je LEAF`, or - at the end of a chain - by `cmp eax,V ; jne DEFAULT`
    # where the leaf is the fall-through. Both forms are read here.
    rows = []
    for l in asm.splitlines():
        ma = re.match(r'\s*([0-9a-f]+):(?:\s+[0-9a-f]{2})+\s+(\S.*)$', l)
        if ma:
            rows.append((int(ma.group(1), 16), ma.group(2)))

    # older generator (Force 2011): the string is loaded BEFORE the comparison and every
    # match jumps to one shared return -> `lea eax,[REG-X] ; cmp <reg>,V ; je EXIT`.
    pre, pending = {}, None
    for a, ins in rows:
        ml = re.match(r'lea\s+eax,\[%s([+-]0x[0-9a-f]+)\]' % reg, ins)
        if ml:
            pending = base + int(ml.group(1), 16)
            continue
        mc = re.match(r'cmp\s+(e\w\w),0x([0-9a-f]+)', ins)
        if mc and pending is not None:
            pre.setdefault(int(mc.group(2), 16), pending)
            continue
        mt = re.match(r'test\s+(e\w\w),(e\w\w)', ins)
        if mt and mt.group(1) == mt.group(2) and pending is not None:
            pre.setdefault(0, pending)
    if len(pre) > 32:
        t2 = {}
        for v, sa in pre.items():
            s = cstr(data, secs, sa)
            if s:
                t2[v] = {'tag': s, 'label': None}
        if len(t2) > 32:
            return t2, 'pre-load comparison tree, %d values recovered' % len(t2)

    last_cmp = None
    for i, (a, ins) in enumerate(rows):
        mc = re.search(r'^cmp\s+eax,0x([0-9a-f]+)', ins)
        if mc:
            last_cmp = int(mc.group(1), 16)
            continue
        if re.match(r'^test\s+eax,eax', ins):      # the value-0 leaf
            last_cmp = 0
            continue
        if last_cmp is None:
            continue
        mj = re.search(r'^je\s+([0-9a-f]+)\b', ins)
        mn = re.search(r'^jne\s+([0-9a-f]+)\b', ins)
        if mj:
            p = pair_at(int(mj.group(1), 16))
            if p and last_cmp not in table:
                table[last_cmp] = p
            last_cmp = None
        elif mn:
            # leaf is the fall-through: the next instruction address
            if i + 1 < len(rows):
                p = pair_at(rows[i + 1][0])
                if p and last_cmp not in table:
                    table[last_cmp] = p
            last_cmp = None
        elif re.match(r'^j(mp|l|le|g|ge|a|ae|b|be)\b', ins):
            last_cmp = None
    return table, 'comparison tree, %d values recovered' % len(table)


def main():
    path, sym = sys.argv[1], sys.argv[2]
    table, note = extract(path, sym)
    print('%s : %s' % (os.path.basename(path), note))
    if not table:
        return
    for i in sorted(table):
        print('  %3d 0x%02X  %-34s %s' % (i, i, table[i]['tag'], table[i]['label'] or ''))
    tag = os.path.basename(os.path.dirname(path))
    out = os.path.join('analysis', 'p19', 'json', '%s.%s.json' % (tag, sym))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(table, open(out, 'w'), indent=1)
    print('wrote %s (%d entries)' % (out, len(table)))


if __name__ == '__main__':
    main()
