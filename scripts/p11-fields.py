# p11-fields.py <version> <nvrefs.tsv>... : derive an NVRAM field dictionary for a Linux build.
# For each offset: width (from decompiler casts), access kinds, and a label built from the most
# specific function names (UI setters/updaters preferred). Writes analysis/p11/<version>.fields.json
import sys, re, json, collections, os
ver = sys.argv[1]
W = collections.defaultdict(collections.Counter); F = collections.defaultdict(collections.Counter); K = collections.defaultdict(set)
for path in sys.argv[2:]:
    for line in open(path, encoding='utf-8', errors='replace').readlines()[1:]:
        p = line.rstrip('\n').split('\t')
        if len(p) < 4: continue
        off = int(p[0], 16); kind, fn, ctx = p[1], p[2], p[3]
        F[off][fn] += 1; K[off].add(kind)
        hexo = f'{off:#x}'
        m = re.search(r'\*\((\w+(?: \w+)?) \*\)\s*\(?PTR_NVRAMData_[0-9a-f]+\s*\+\s*' + re.escape(hexo) + r'\b', ctx)
        if m:
            t = m.group(1)
            W[off][4 if re.search(r'int|4|long|float|time_t', t) and 'short' not in t else 2 if 'short' in t or '2' in t else 8 if 'double' in t or '8' in t else 1] += 1
        elif re.search(r'NVRAMData_[0-9a-f]+\[' + re.escape(hexo) + r'\]', ctx): W[off][1] += 1
        elif re.search(re.escape(hexo) + r'\),\s*\d', ctx) or 'strcpy' in ctx or 'memcpy' in ctx or 'strncpy' in ctx: W[off]['buf'] += 1

def nice(n):
    m = re.match(r'(.+?)__(\d+)([A-Za-z_]\w*)', n)
    if m and len(m.group(3)) >= int(m.group(2)): return m.group(3)[:int(m.group(2))] + '::' + m.group(1)
    return n.split('__')[0]
GENERIC = {'GetNVRAM', 'PutNVRAM', 'InitVars', 'PreserveImportantVars', 'NVClear', 'NewSendAllData', 'SendAllData',
           'Process_Setup_Options_Request', 'Process_Cash_Settlement_Request', 'SystemClass::Continue', '_mangled_main', 'MG_ClearBooks'}
def score(n):
    base = n.split('::')[-1]
    s = 0
    if re.match(r'(Set|Toggle|Enter|Change)', base): s += 3
    if re.match(r'(Update|Get|Is|Check)', base): s += 1
    if '::' in n: s += 1
    if n.startswith('FUN_') or base in GENERIC or n in GENERIC: s -= 10
    return s
fields = {}
offs = sorted(F)
for i, off in enumerate(offs):
    names = [nice(n) for n, _ in F[off].most_common()]
    ranked = sorted(dict.fromkeys(names), key=lambda n: -score(n))
    label = ', '.join([n for n in ranked if score(n) > -5][:3]) or '(only generic/unnamed users)'
    w = W[off].most_common(1)[0][0] if W[off] else None
    fields[f'{off:#07x}'] = {'width': w, 'label': label, 'nfuncs': len(F[off]), 'kinds': sorted(K[off])}
os.makedirs('F:/MTKeyWork/analysis/p11', exist_ok=True)
json.dump(fields, open(f'F:/MTKeyWork/analysis/p11/{ver}.fields.json', 'w'), indent=1)
print(ver, len(fields), 'fields;', sum(1 for f in fields.values() if f['width']), 'with width')
