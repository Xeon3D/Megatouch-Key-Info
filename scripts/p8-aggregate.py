# Aggregate Ghidra nvrefs TSVs: offset -> demangled-ish function names (shortest informative first).
import sys, collections, re
agg = collections.defaultdict(collections.Counter)
for fn in sys.argv[2:]:
    for line in open(fn, encoding='utf-8', errors='replace').readlines()[1:]:
        p = line.rstrip('\n').split('\t')
        if len(p) < 3: continue
        agg[int(p[0], 16)][p[2]] += 1
def nice(n):  # Foo__10ClassName -> ClassName::Foo
    m = re.match(r'(.+?)__(\d+)([A-Za-z_]\w*)', n)
    if m and len(m.group(3)) >= int(m.group(2)): return m.group(3)[:int(m.group(2))] + '::' + m.group(1)
    return n.split('__')[0]
with open(sys.argv[1], 'w') as f:
    for off in sorted(agg):
        names = [nice(n) for n, _ in agg[off].most_common()]
        named = [n for n in names if not n.startswith('FUN_')]
        f.write(f'{off:#07x}\t{sum(agg[off].values())}\t' + ', '.join(dict.fromkeys(named))[:220] + '\n')
print(len(agg), 'offsets')
