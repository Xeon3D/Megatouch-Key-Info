"""p19-enum3.py - complete a sparse generated enum table by using the .rodata layout.

`enum_GameIds_tag` is compiled as a binary comparison tree, so only the leaves reached by
an exact `je` can be read off directly (p19-enum2.py gets those). The generator, however,
emits the two string literals of each enum value (lowercase tag, uppercase label)
consecutively in declaration order, so the literals in address order enumerate the whole
enum. This script:

  1. reads every (value -> tag string address) pair the `je` leaves give,
  2. checks those addresses increase with the enum value (the layout assumption),
  3. collects all tag literals the function references, in address order,
  4. assigns the gaps, and verifies every directly-known value still lands on its own tag.

Only a table that passes step 4 for every known value is written out.

usage: p19-enum3.py <lib.so> <enum_tag_symbol>
"""
import sys, os, re, json, subprocess


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
        s = data[o:e].decode('ascii')
    except (ValueError, UnicodeDecodeError):
        return None
    return s if 0 < len(s) <= 80 else None


def main():
    path, sym = sys.argv[1], sys.argv[2]
    binw = wslpath(path)
    data = open(path, 'rb').read()
    secs = sections(binw)
    syms = sh("readelf -W --dyn-syms '%s'" % binw)
    cand = [(int(f[1], 16), int(f[2]), f[7]) for f in (l.split() for l in syms.splitlines())
            if len(f) >= 8 and f[3] == 'FUNC' and sym in f[7] and int(f[1], 16)]
    addr, size, _ = max(cand, key=lambda c: c[1])
    asm = sh("objdump -d --start-address=0x%x --stop-address=0x%x -M intel '%s'"
             % (addr, addr + size, binw))
    m = re.search(r'^\s*([0-9a-f]+):\s+5[89b]\s+pop\s+(e\w\w)\s*$', asm, re.M)
    reg = m.group(2)
    base = int(m.group(1), 16) + int(re.search(r'add\s+%s,0x([0-9a-f]+)' % reg, asm).group(1), 16)

    leas = {}
    for mm in re.finditer(
            r'^\s*([0-9a-f]+):(?:\s+[0-9a-f]{2})+\s+lea\s+eax,\[%s([+-]0x[0-9a-f]+)\]' % reg,
            asm, re.M):
        leas[int(mm.group(1), 16)] = base + int(mm.group(2), 16)
    order = sorted(leas)

    # (1) values reached by an exact je
    known = {}
    last = None
    for l in asm.splitlines():
        mc = re.search(r'cmp\s+eax,0x([0-9a-f]+)', l)
        if mc:
            last = int(mc.group(1), 16)
            continue
        mj = re.search(r'\bje\s+([0-9a-f]+)\b', l)
        if mj and last is not None:
            tgt = int(mj.group(1), 16)
            nxt = min((a for a in order if a >= tgt), default=None)
            if nxt is not None and last not in known:
                known[last] = leas[nxt]
            last = None

    # (2) do the string addresses increase with the enum value?
    kv = sorted(known)
    addrs = [known[v] for v in kv]
    mono = all(addrs[i] < addrs[i + 1] for i in range(len(addrs) - 1))
    print('%s: %d values via je; tag addresses increase with value: %s'
          % (os.path.basename(path), len(known), mono))
    if not mono:
        bad = [(kv[i], hex(addrs[i]), kv[i + 1], hex(addrs[i + 1]))
               for i in range(len(addrs) - 1) if addrs[i] >= addrs[i + 1]]
        print('  %d inversions, e.g. %s' % (len(bad), bad[:3]))
        print('  layout assumption fails - not writing a table')
        return

    # (3) all referenced literals, in address order, keeping only lowercase tags
    lits = []
    for a in sorted(set(leas.values())):
        s = cstr(data, secs, a)
        if s and s == s.lower() and re.fullmatch(r'[a-z0-9_]+', s):
            lits.append((a, s))

    # (4) walk the value range, consuming literals in address order
    lo, hi = kv[0], kv[-1]
    table, li, fails = {}, 0, []
    # restrict to literals from the first known address onward
    li = next(i for i, (a, _) in enumerate(lits) if a == addrs[0])
    v = lo
    while v <= hi and li < len(lits):
        a, s = lits[li]
        if v in known:
            if known[v] != a:
                fails.append((v, s, cstr(data, secs, known[v])))
        table[v] = s
        li += 1
        v += 1
        # jump the sparse gap between the dense game block and the 0x2718+ block
        while v not in known and v < hi and (v - lo) > 0 and \
                li < len(lits) and any(k > v for k in known) and \
                min(k for k in known if k >= v) - v > 64:
            v = min(k for k in known if k >= v)
    print('  assigned %d values, %d disagree with the je leaves' % (len(table), len(fails)))
    if fails:
        for f in fails[:8]:
            print('    value 0x%X: layout says %r, je leaf says %r' % f)
        print('  not writing a table')
        return
    for v in sorted(table):
        print('  %5d 0x%04X  %s' % (v, v, table[v]))
    tag = os.path.basename(os.path.dirname(path))
    out = os.path.join('analysis', 'p19', 'json', '%s.%s.full.json' % (tag, sym))
    json.dump(table, open(out, 'w'), indent=1)
    print('wrote %s (%d entries)' % (out, len(table)))


if __name__ == '__main__':
    main()
