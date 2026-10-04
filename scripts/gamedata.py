"""gamedata.py - parse Megatouch /usr/local/share/merit/config/gamedata.dat (game ID = record order).

usage: gamedata.py <gamedata.dat> [--json]
Fields per record (from the file's own header): support-file base name, DLL name, description,
graphics directory, tournament rounds, max players, linkable units, idle name, language mask (hex),
replay score, (unused), high-colour, sex flag, other flags (bit 0 H2H, 1 pro sports, 2 differs on
Force/Maxx, 3 Merit-thon event, 4 Prize Zone II, 5 card-back ads, 6 Force only, 7 continuable).
"""
import sys, json
FIELDS = ['support', 'dll', 'description', 'directory', 'tournament', 'max_players', 'linkable', 'idle_name',
          'langs', 'replay_score', 'unused', 'high_color', 'sex_flag', 'other_flags']
FLAGS = ['h2h', 'pro_sports', 'force_maxx_variant', 'meritthon', 'prize_zone2', 'card_back_ads', 'force_only', 'continuable']

def parse(path):
    games = []; cur = None
    for raw in open(path, encoding='latin1'):
        line = raw.rstrip('\r\n')
        if line.startswith('*'):
            cur = []; games.append(cur); continue
        if cur is None or line.startswith('//') or line.startswith('/ ') or not line.strip(): continue
        if len(cur) < len(FIELDS): cur.append(line.split('//')[0].strip())
    out = []
    for gid, vals in enumerate(games):
        g = dict(zip(FIELDS, vals)); g['id'] = gid
        try:
            of = int(g.get('other_flags', '0'), 16); g['flags'] = [FLAGS[i] for i in range(8) if of >> i & 1]
        except ValueError:
            g['flags'] = []
        out.append(g)
    return out

if __name__ == '__main__':
    gs = parse(sys.argv[1])
    if '--json' in sys.argv: print(json.dumps(gs, indent=1))
    else:
        for g in gs:
            print(f"{g['id']:#04x} {g.get('dll', ''):16} {g.get('description', ''):32} {','.join(g['flags'])}")
