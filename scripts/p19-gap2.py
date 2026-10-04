"""p19-gap2.py - list the generated-enum string literals a comparison-tree enum_*_tag
references but that p19-enum2.py could not attach to a value, and show the code around
each so the guarding comparison can be read.

usage: p19-gap2.py <lib.so> <enum_tag_symbol> <table.json>
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
    for _, a, o, s in secs:
        if a and a <= va < a + s:
            return o + (va - a)
    return None


def cstr(data, secs, va):
    o = foff(secs, va)
    if o is None:
        return None
    try:
        return data[o:data.index(b'\0', o)].decode('ascii')
    except (ValueError, UnicodeDecodeError):
        return None


def main():
    path, sym, tbl = sys.argv[1], sys.argv[2], sys.argv[3]
    binw = wslpath(path)
    data = open(path, 'rb').read()
    secs = sections(binw)
    known = {v['tag'] for v in json.load(open(tbl)).values()}
    syms = sh("readelf -W --dyn-syms '%s'" % binw)
    cand = [(int(f[1], 16), int(f[2])) for f in (l.split() for l in syms.splitlines())
            if len(f) >= 8 and f[3] == 'FUNC' and sym in f[7] and int(f[1], 16)]
    addr, size = max(cand, key=lambda c: c[1])
    asm = sh("objdump -d --start-address=0x%x --stop-address=0x%x -M intel '%s'"
             % (addr, addr + size, binw))
    m = re.search(r'^\s*([0-9a-f]+):\s+5[89b]\s+pop\s+(e\w\w)\s*$', asm, re.M)
    reg = m.group(2)
    base = int(m.group(1), 16) + int(re.search(r'add\s+%s,0x([0-9a-f]+)' % reg, asm).group(1), 16)

    rows = []
    for l in asm.splitlines():
        ma = re.match(r'\s*([0-9a-f]+):(?:\s+[0-9a-f]{2})+\s+(\S.*)$', l)
        if ma:
            rows.append((int(ma.group(1), 16), ma.group(2).strip()))
    idx = {a: i for i, (a, _) in enumerate(rows)}

    unclaimed = []
    for i, (a, ins) in enumerate(rows):
        mm = re.match(r'lea\s+eax,\[%s([+-]0x[0-9a-f]+)\]' % reg, ins)
        if not mm:
            continue
        s = cstr(data, secs, base + int(mm.group(1), 16))
        if s and s == s.lower() and re.fullmatch(r'[a-z0-9_]+', s) and s not in known:
            unclaimed.append((a, s, i))

    print('%d literals referenced but unattached:' % len(unclaimed))
    for a, s, i in unclaimed:
        ctx = ' | '.join(ins for _, ins in rows[max(0, i - 4):i + 1])
        print('  0x%06x  %-30s  %s' % (a, s, ctx[-150:]))


if __name__ == '__main__':
    main()
