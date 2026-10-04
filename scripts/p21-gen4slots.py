"""p21-gen4slots.py - classify the 120 Gen 4 option slots per build (the P10/P12 method, for Gen 4).

usage: p21-gen4slots.py <tag> <dis file> [<dis file> ...]   (objdump -d -C output, see p21-dis*.sh)
writes analysis/p21/<tag>.slots.json

For every call to an API that takes an xml_gameoptions::GameOptionIndex, the slot argument is
resolved from the pushes before the call (the index is the nearest immediate push in [0, 0x78),
skipping one non-immediate push for `this`), or from `mov $imm,%reg` feeding a pushed register.

  menu   = an operator-menu function writes it or builds a menu toggle for it
           (MenuSystem::SETUP_OPTION / SetOptionValue, STM_OP_Page1::SIX_STAR_OPTION, or
           NVRAMMap::SetGameOption from a UI handler: Toggle*/Set*/Update*/Save*/Enable*/Run)
  key    = read by the game or the menus, never written by a menu -> the key alone decides
  none   = no reference found in the scanned binaries
SIX_STAR_OPTION also passes the label text shown in the six-star menu; it is recorded.
"""
import sys, re, json, collections, os

READ = ('KeyManager::Option(', 'KeyManager::IsOptionSelectable(', 'NVRAMMap::IsOptionOn(',
        'NVRAMMap::GamesOpt(', 'NVRAMMap::GamesOptModified(', 'MenuSystem::IsOptionOn(',
        'MenuSystem::GetOptionValue(', 'MenuSystem::IsOptionInUse(', 'KeyMgr::GetOptionState(',
        'KeyMgr::IsOptionSelectable(', 'MenuSystem::IsSexBased(', 'MenuSystem::IsNudityBased(',
        'MenuSystem::IsSixStarBased(', 'MenuSystem::IsShowDeckBased(',
        'MenuSystem::IsTournaMAXXBased(', 'MenuSystem::GetRelatedGame(', 'MenuSystem::IsGameSpecific(')
WRITE_UI = ('MenuSystem::SETUP_OPTION(', 'MenuSystem::SetOptionValue(', 'STM_OP_Page1::SIX_STAR_OPTION(')
WRITE_ANY = ('NVRAMMap::SetGameOption(',)
UI_FN = re.compile(r'::(Toggle|Set|Update|Save|Enable|Run|Command|Process|Change|Select)')
NOT_UI = re.compile(r'Default|Init|Import|Reset|Reinit|EntryPoint|Load|Fudge|Restore|Clear')

tag, files = sys.argv[1], sys.argv[2:]
reads, writes, labels = collections.defaultdict(set), collections.defaultdict(set), {}
strings = {}

def load(path):
    out, fn = [], None
    for l in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'^([0-9a-f]+) <(.+)>:$', l)
        if m:
            fn = m.group(2); continue
        m = re.match(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$', l)
        if m:
            out.append((fn, m.group(2), m.group(3)))
    return out

def imm(lines, j, arg):
    if arg.startswith('$'):
        return int(arg[1:], 0)
    if arg.startswith('%'):
        for k in range(j - 1, max(0, j - 15), -1):
            _, mn, ops = lines[k]
            mm = re.match(r'\$(0x[0-9a-f]+|\d+),' + re.escape(arg) + r'$', ops)
            if mn == 'mov' and mm:
                return int(mm.group(1), 0)
            if arg in ops.split(',')[-1]:
                return None
    return None

for path in files:
    lines = load(path)
    for i, (f, mn, ops) in enumerate(lines):
        if mn != 'call':
            continue
        api = next((a for a in READ + WRITE_UI + WRITE_ANY if a in ops), None)
        if not api or (f and f.startswith(api.rstrip('('))):
            continue
        pushes = []
        for j in range(i - 1, max(0, i - 30), -1):
            _, mn2, ops2 = lines[j]
            if mn2 == 'call':
                break
            if mn2 == 'push':
                pushes.append((j, ops2.strip()))
        slot = None
        if api.startswith('STM_OP_Page1::SIX_STAR_OPTION'):
            # (this, char const* label, GameOptionIndex, char const* help): label/help are pointers
            vals = [imm(lines, j, a) for j, a in pushes[:4]]
            cand = [v for v in vals if v is not None and 0 <= v < 0x78]
            slot = cand[0] if cand else None
        else:
            for j, a in pushes[:2]:
                v = imm(lines, j, a)
                if v is not None and 0 <= v < 0x78:
                    slot = v
                    break
        if slot is None:
            continue
        where = (f or '?') + ' @' + os.path.basename(path).split('.')[1]
        if api in WRITE_UI or (api in WRITE_ANY and f and UI_FN.search(f) and not NOT_UI.search(f)):
            writes[slot].add(where)
        else:
            reads[slot].add(where)

res = {}
for s in range(0x78):
    c = 'menu' if writes[s] else ('key' if reads[s] else 'none')
    res[s] = {'class': c, 'writers': sorted(writes[s])[:6], 'readers': sorted(reads[s])[:6],
              'nwriters': len(writes[s]), 'nreaders': len(reads[s])}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'p21', tag + '.slots.json')
json.dump(res, open(out, 'w'), indent=1)
cnt = collections.Counter(v['class'] for v in res.values())
print(tag, dict(cnt))
