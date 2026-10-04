# p8-align.py: carry Crown NVRAM labels to another version by matching the named functions that
# touch each offset (Jaccard similarity of normalised function-name sets).
# usage: p8-align.py <target-map> [<target-map> ...]
#   target map = Linux aggregated nvmap (offset \t n \t names) or DOS *.nvmap.tsv (offset \t w \t n \t - \t names)
import sys, re, bisect, collections
ROOT = 'F:/MTKeyWork/analysis/p8/'
def norm(n):
    n = n.strip()
    m = re.match(r'W\?([A-Z0-9_]+)\$:([A-Z0-9_]+)\$', n)          # Watcom C++: W?METHOD$:CLASS$...
    if m: return (m.group(2) + '::' + m.group(1)).upper()
    n = n.rstrip('_').upper()
    return n if not n.startswith(('FN_', 'FUN_', '(')) and n else None
def load(path):
    out = {}
    for line in open(path, encoding='utf-8', errors='replace'):
        p = line.rstrip('\n').split('\t')
        if not p[0].startswith('0x'): continue
        names = p[4] if len(p) >= 5 else (p[2] if len(p) >= 3 else '')
        s = {x for x in (norm(t) for t in names.split(',')) if x}
        if s: out[int(p[0], 16)] = s
    return out
ref = load(ROOT + 'crown.nvmap.tsv')
labels = []
for line in open(ROOT + 'crown_labels.tsv'):
    p = line.rstrip('\n').split('\t')
    if p[0].startswith('0x'): labels.append((int(p[0], 16), int(p[1]), p[2]))
labels.sort(); lstarts = [l[0] for l in labels]
def label_of(off):
    i = bisect.bisect_right(lstarts, off) - 1
    if i >= 0 and off < labels[i][0] + labels[i][1]: return labels[i][2] + (f' +{off - labels[i][0]:#x}' if off != labels[i][0] else '')
    return None
for tgt in sys.argv[1:]:
    t = load(tgt); rows = []
    for off, s in sorted(t.items()):
        best, bj = None, 0.0
        for roff, rs in ref.items():
            j = len(s & rs) / len(s | rs)
            if j > bj: best, bj = roff, j
        lab = label_of(best) if best is not None else None
        rows.append((off, best, bj, lab, sorted(s)[:4]))
    outp = tgt.replace('.tsv', '').replace('.nvmap', '') + '.aligned.tsv'
    with open(outp, 'w', encoding='utf-8') as f:
        f.write('offset\tcrown_offset\tscore\tlabel\tfunctions\n')
        for off, best, bj, lab, s in rows:
            f.write(f'{off:#07x}\t{best:#07x}\t{bj:.2f}\t{lab or ""}\t{", ".join(s)}\n' if best is not None else f'{off:#07x}\t\t0\t\t{", ".join(s)}\n')
    good = sum(1 for r in rows if r[2] >= 0.3 and r[3])
    print(f'{tgt.split("/")[-1]}: {len(rows)} named offsets, {good} labelled (score>=0.3) -> {outp.split("/")[-1]}')
