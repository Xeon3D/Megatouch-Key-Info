"""p19-grid4.py - cross-key differential grid for Gen4 (Force 2007-2011 / ION 2007-2014).

Decrypts every Gen4 dump it is given, groups them by version, and reports for each byte
offset whether it is constant across the group or varies (with the values). Constant
bytes are structure/signature; varying bytes are the per-key fields. Printing the varying
offsets first is the cheapest way to locate fields without touching the binaries.

usage: p19-grid4.py <dir> [...]
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey4


def collect(paths):
    keys = {}
    for p in paths:
        try:
            if os.path.getsize(p) not in (1024, 1032, 2048, 2056, 8192, 8200):
                continue
        except OSError:
            continue
        mem, ser = mtkey4.load(p)
        if not ser:
            continue
        for v, dec in mtkey4.try_all(mem, ser):
            keys.setdefault(v, []).append((os.path.basename(p), ser, dec))
    return keys


def runs(offsets):
    """Collapse a sorted offset list into (start, end) runs."""
    out = []
    for o in offsets:
        if out and o == out[-1][1] + 1:
            out[-1][1] = o
        else:
            out.append([o, o])
    return out


def main():
    paths = []
    for a in sys.argv[1:]:
        if os.path.isdir(a):
            for dp, _, fs in os.walk(a):
                paths += [os.path.join(dp, f) for f in fs]
        else:
            paths.append(a)
    keys = collect(paths)

    print('=== Gen4 corpus ===')
    for v in sorted(keys):
        print('%-7s %d key(s): %s' % (v, len(keys[v]), ', '.join(s for _, s, _ in keys[v])))

    # per-version variation
    for v in sorted(keys):
        group = keys[v]
        if len(group) < 2:
            continue
        print('\n=== %s : %d keys, offsets that differ ===' % (v, len(group)))
        var = [o for o in range(1024) if len({d[o] for _, _, d in group}) > 1]
        print('varying bytes: %d / 1024' % len(var))
        for a, b in runs(var):
            vals = []
            for name, ser, d in group:
                vals.append('%s=%s' % (ser[-8:], d[a:b + 1].hex().upper()))
            print('  0x%03X..0x%03X (%2d)  %s' % (a, b, b - a + 1, '  '.join(vals)))

    # cross-version constants: what every Gen4 key shares at the same offset
    allk = [d for v in keys for _, _, d in keys[v]]
    if len(allk) > 1:
        same = [o for o in range(1024) if len({d[o] for d in allk}) == 1]
        print('\n=== identical across ALL %d Gen4 keys (%d bytes) ===' % (len(allk), len(same)))
        for a, b in runs(same):
            if b - a >= 1:
                print('  0x%03X..0x%03X (%2d) %s' % (a, b, b - a + 1, allk[0][a:b + 1].hex().upper()))


if __name__ == '__main__':
    main()
