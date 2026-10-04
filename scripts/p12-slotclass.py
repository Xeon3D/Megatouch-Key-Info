# p12-slotclass.py: classify the 80 option slots per Linux build.
#   operator = an operator-menu handler writes it (SetOptionValue call in opsetup, or direct write by Set*/Toggle*)
#   key      = read (menus/game) but never written by a menu  -> value comes from the key alone
#   runtime  = written by game code;  remote = written only by a MegaNet packet handler;  unused = no reader
# inputs: analysis/p10/slotcalls_<build>.tsv (p10-slotcalls.py on opsetup) + analysis/p8/<build>_*.nvrefs.tsv
import re, sys, collections, json
A = 'F:/MTKeyWork/analysis/'
BUILDS = {'ruby2': ('ruby2_1100', 0x3DA), 'sapphire': ('sapph_1201', 0x3DA), 'sapphire2': ('sapph2_1300', 0x3DA),
          'jade': ('jade_1400', 0x8E), 'jade2': ('jade2_1510', 0x8E), 'jade1421': ('jade_1421', 0x8E), 'crown': ('crown', 0x8E)}
API_FUNCS = ('SetOptionValue', 'GetOptionValue', 'IsOptionOn', 'SetupOption', 'IsOptionInUse', 'ReinitNVRAM', 'SetupOptionDefaults')
res = {}
for b, (pref, base) in BUILDS.items():
    try: calls = [l.rstrip('\n').split('\t') for l in open(A + f'p10/slotcalls_{b}.tsv')]
    except FileNotFoundError: continue
    sets = collections.defaultdict(set); reads = collections.defaultdict(set)
    for s, api, where, f in calls:
        (sets if api == 'set' else reads)[int(s, 16)].add(f)
    dw = collections.defaultdict(set); dr = collections.defaultdict(set); have = False
    for part in ('start', 'opsetup'):
        try: lines = open(A + f'p8/{pref}_{part}.nvrefs.tsv', encoding='utf-8', errors='replace').readlines()[1:]
        except FileNotFoundError: continue
        have = True
        for l in lines:
            p = l.rstrip('\n').split('\t')
            if len(p) < 4: continue
            off = int(p[0], 16)
            if not base <= off < base + 80: continue
            slot = off - base; f = p[2].split('__')[0]
            if f in API_FUNCS: continue
            (dw if re.search(r'(\[%#x\]|\+ %#x\)?)\s*=[^=]' % (off, off), p[3]) else dr)[slot].add(f + '|' + part)
    cls = {}
    for i in range(80):
        ui = {x for x in dw[i] if re.match(r'(Set|Toggle|Change)', x)}
        if sets[i] or ui: c = 'operator'
        elif dw[i] and all('Process_' in x for x in dw[i]): c = 'remote'
        elif dw[i]: c = 'runtime'
        elif reads[i] or dr[i]: c = 'key'
        else: c = 'unused'
        cls[i] = c
    res[b] = {'classes': cls, 'nvrefs': have}
json.dump(res, open(A + 'p12/slot_classes_all.json', 'w'), indent=1)
names = {}
for l in open('F:/MTKeyWork/Docs/04-territory-options.md', encoding='utf-8'):
    m = re.match(r'\| 0x([0-9A-F]{2}) \| (.+?) \| \d', l)
    if m and int(m.group(1), 16) not in names: names[int(m.group(1), 16)] = m.group(2)
bs = list(res)
print('slot  ' + ''.join(b[:9].ljust(10) for b in bs) + 'name (from Crown)')
for i in range(80):
    row = [res[b]['classes'][i] for b in bs]
    flag = '  <==' if len(set(row)) > 1 else ''
    print(f'0x{i:02X}  ' + ''.join(r.ljust(10) for r in row) + names.get(i, '')[:46] + flag)
