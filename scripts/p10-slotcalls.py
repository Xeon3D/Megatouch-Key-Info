# p10-slotcalls.py <objdump -d output> <label> : for every call to the option API, resolve the slot
# argument (cdecl: the LAST push before the call is the first argument) through simple constant tracking
# (push $imm, or push %reg after mov $imm,%reg in the same window). Emits TSV: slot fn api caller
import sys, re, collections
API = {'SetOptionValue__Fii': 'set', 'GetOptionValue__Fi': 'get', 'IsOptionOn__Fib': 'on', 'IsOptionOn__Fi': 'on',
       'IsOptionInUse__Fib': 'inuse', 'IsOptionInUse__Fi': 'inuse', 'IsOptionSelectable__6KeyMgrib': 'selectable',
       'IsOptionSelectable__6KeyMgri': 'selectable', 'GetOptionState__6KeyMgri': 'state'}
lines = []; fn = None
for l in open(sys.argv[1], encoding='utf-8', errors='replace'):
    m = re.match(r'^([0-9a-f]+) <(.+?)(?:@@Base|@plt)?>:$', l)
    if m: fn = m.group(2); continue
    m = re.match(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$', l)
    if m: lines.append((fn, m.group(2), m.group(3)))
out = collections.defaultdict(set)
for i, (f, mn, ops) in enumerate(lines):
    if mn != 'call': continue
    m = re.search(r'<([^@>+]+)', ops)
    if not m or m.group(1) not in API: continue
    api = API[m.group(1)]
    if f and f.startswith(m.group(1)): continue           # skip the API's own implementation
    # arguments: walk back collecting pushes (nearest first); for KeyMgr methods arg0 is 'this'
    pushes = []; regs = {}
    for j in range(i - 1, max(0, i - 25), -1):
        _, mn2, ops2 = lines[j]
        if mn2 == 'call': break
        if mn2 == 'push': pushes.append((j, ops2.strip()))
    want = 1 if api in ('selectable', 'state') else 0
    if len(pushes) <= want: continue
    j, arg = pushes[want]
    slot = None
    if arg.startswith('$0x') or arg.startswith('$'): slot = int(arg[1:], 0)
    elif arg.startswith('%'):
        for k in range(j - 1, max(0, j - 15), -1):
            _, mn3, ops3 = lines[k]
            mm = re.match(r'\$(0x[0-9a-f]+|\d+),' + re.escape(arg) + r'$', ops3)
            if mn3 == 'mov' and mm: slot = int(mm.group(1), 0); break
            if arg in ops3.split(',')[-1]: break
    if slot is not None and 0 <= slot < 0x50:
        out[slot].add((api, f or '?'))
for slot in sorted(out):
    for api, f in sorted(out[slot]):
        print(f'{slot:#04x}\t{api}\t{sys.argv[2]}\t{f}')
