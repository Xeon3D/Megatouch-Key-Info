# p16-dosgames.py: per-DOS-layout game name lists -> analysis/p16/dos_games_by_base.json
# Game ID = record order in C:\MERIT2\DATA\GAMEDATA.DAT (same rule as Linux). The NVRAM base version
# of each image comes from that image's own NVRAM.DAT (analysis/p9/nvram, byte 9), so names are tied
# to the layout they index. MAXX images win over XL images for a shared base (XL lists can differ).
import glob, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedata
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis')
out = {}
for f in sorted(glob.glob(os.path.join(A, 'p16', '*.GAMEDATA.DAT')), key=lambda p: ('XL_' in p, p)):
    n = os.path.basename(f).replace('.GAMEDATA.DAT', '')
    nv = os.path.join(A, 'p9', 'nvram', n + '.NVRAM.DAT')
    if not os.path.exists(nv): continue
    b = open(nv, 'rb').read()
    if not any(b[:16]): continue
    base = hex(b[9]); gs = gamedata.parse(f)
    names = [g.get('description', '') for g in gs]
    if base in out:
        if out[base]['names'] != names: out[base].setdefault('variants', {})[n] = names
        continue
    out[base] = {'source': n, 'count': len(names), 'names': names}
json.dump(out, open(os.path.join(A, 'p16', 'dos_games_by_base.json'), 'w'), indent=1)
for k, v in sorted(out.items()):
    print(k, v['count'], v['source'], 'variants:', list(v.get('variants', {})))
