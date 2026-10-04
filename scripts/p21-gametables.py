"""p21-gametables.py - build scripts/data/game_tables.json: game names per software version.

Game id = record order in that version's game table (DOS C:\\MERIT2\\DATA\\GAMEDATA.DAT, Linux
/usr/local/share/merit/config/gamedata.dat; Docs/08 P14/P16). Gen 4 ids are the xml_gameinfo::GameIds
enum (Docs/19, scripts/data/games.json). Ids are mostly stable across releases but Merit reused some
slots, so every key version gets the table of its own software, or the nearest one when none exists.

Inputs (extracted read-only): analysis/p16 (DOS), analysis/p14 (Sapphire..Crown), analysis/p19/bin
(Force 2004/2005), analysis/p21/gamedata (Ruby, Ruby 2, Force 2002/2003/2006, Sapphire 2, Jade 14.21).
"""
import json, os, re, sys, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path.insert(0, HERE)
import gamedata

A = lambda *p: os.path.join(ROOT, 'analysis', *p)
TABLES = [  # id, label, file
 ('M306', 'MAXX 3.06', A('p16', 'MAXX_V3.06_-_Played.GAMEDATA.DAT')),
 ('M2K', 'MAXX 2K V4.00/V4.01', A('p16', 'MAXX_2K_V4.00_-_Played.GAMEDATA.DAT')),
 ('M2KP', 'MAXX 2K Plus V5.00', A('p16', 'MAXX_2K_Plus_V5.00_-_Played.GAMEDATA.DAT')),
 ('XPLAT', 'XL Platinum / Double Platinum', A('p16', 'XL_Platinum_V1.02_-_Played.GAMEDATA.DAT')),
 ('MDIA', 'MAXX Diamond V6.03/V6.20', A('p16', 'MAXX_Diamond_V6.03_-_New.GAMEDATA.DAT')),
 ('MDD', 'MAXX Double Diamond V7.01/V7.20', A('p16', 'MAXX_Double_Diamond_V7.01_-_New.GAMEDATA.DAT')),
 ('XTIT', 'XL Titanium V3.00', A('p16', 'XL_Titanium_V3.00_-_Keyless_Played.GAMEDATA.DAT')),
 ('XTIT2', 'XL Titanium 2 V4.00', A('p16', 'XL_Titanium_2_V4.00_-_Played.GAMEDATA.DAT')),
 ('MEME', 'MAXX Emerald V8.04/V8.05/V8.20', A('p16', 'MAXX_Emerald_V8.04_-_Original.GAMEDATA.DAT')),
 ('MEME2', 'MAXX Emerald 2 V9.00/V9.01', A('p16', 'MAXX_Emerald_2_V9.00_-_Played.GAMEDATA.DAT')),
 ('F2002', 'Force 2002', A('p21', 'gamedata', 'F2002.GAMEDATA.DAT')),
 ('RUBY', 'MAXX Ruby', A('p21', 'gamedata', 'RUBY.gamedata.dat')),
 ('RUBY2', 'MAXX Ruby 2 V11.00', A('p21', 'gamedata', 'RUBY2.gamedata.dat')),
 ('F2003', 'Force 2003 v10.09', A('p21', 'gamedata', 'F2003.gamedata.dat')),
 ('F2003_5', 'Force 2003.5 v11.00', A('p21', 'gamedata', 'F2003_5.gamedata.dat')),
 ('SAPP', 'MAXX Sapphire V12.01', A('p14', 'MAXX_Sapphire_V12.01_-_Played.gamedata.dat')),
 ('SAPP2', 'MAXX Sapphire 2 V13.00', A('p14', 'MAXX_Sapphire_2_V13.00_-_Played_Keyless.gamedata.dat')),
 ('F2004', 'Force 2004 v12.00', A('p19', 'bin', 'F2004', 'gamedata.dat')),
 ('JADE', 'MAXX Jade V14.00', A('p14', 'MAXX_Jade_V14.00_-_New.gamedata.dat')),
 ('JADE1421', 'MAXX Jade V14.21', A('p14', 'MAXX_Jade_V14.21_-_Keyless_Played.gamedata.dat')),
 ('JADE2', 'MAXX Jade 2 V15.10', A('p14', 'MAXX_Jade_2_V15.10_-_New.gamedata.dat')),
 ('F2005', 'Force 2005 v14.00', A('p19', 'bin', 'F2005', 'gamedata.dat')),
 ('F2005_5', 'Force 2005.5 v15.10', A('p19', 'bin', 'F2005_5', 'gamedata.dat')),
 ('CROWN', 'MAXX Crown V16.10', A('p14', 'MAXX_Crown_V16.10_-_New.gamedata.dat')),
]
# key version (mtkeylib label) -> tables, own software first; 'nearest' marks a stand-in
VERSIONS = {
 'XL R1': (['M306'], 'nearest'), 'XL Super 5000': (['M306'], 'nearest'), 'XL 6000': (['M306'], 'nearest'),
 'MAXX 3.06': (['M306'], ''), 'XL Gold': (['M2K'], 'nearest'), 'MAXX 2K': (['M2K', 'M2KP'], ''),
 'XL Platinum': (['XPLAT'], ''), 'MAXX Diamond': (['MDIA', 'MDD'], ''),
 'XL Titanium': (['XTIT', 'XTIT2'], ''), 'MAXX Emerald': (['MEME', 'MEME2'], ''), 'Force 2002': (['F2002'], ''),
 'MAXX Ruby 2': (['RUBY2', 'RUBY'], ''), 'Force 2003': (['F2003_5', 'F2003'], ''),
 'MAXX Sapphire': (['SAPP', 'SAPP2'], ''), 'Force 2004': (['F2004'], ''),
 'MAXX Jade': (['JADE', 'JADE1421', 'JADE2'], ''), 'Force 2005': (['F2005', 'F2005_5'], ''),
 'MAXX Crown': (['CROWN'], ''),
 # Force 2006: the gamedata.dat on the only Force 2006 image is byte-identical in content to Force 2003's
 # (102 games) while the Force 2006 key prices Crown-era ids up to 0xC1, so that file is stale -> Crown.
 'Force 2006': (['CROWN', 'F2005_5'], 'nearest'), 'ION 2006': (['CROWN'], 'nearest'),
}
out = {'tables': {}, 'versions': {}}
seen = {}
for tid, label, path in TABLES:
    raw = open(path, 'rb').read()
    gs = gamedata.parse(path)
    out['tables'][tid] = {
        'label': label, 'source': os.path.relpath(path, ROOT).replace('\\', '/'),
        'sha256': hashlib.sha256(raw).hexdigest()[:16],
        'names': {str(g['id']): g.get('description', '').strip() for g in gs},
        'flags': {str(g['id']): g['flags'] for g in gs if g['flags']},
    }
for v, (ids, how) in VERSIONS.items():
    out['versions'][v] = {'tables': ids, 'nearest': how == 'nearest'}

# Gen 4: the recovered enum. Force ids agree with ION wherever both are pinned (168/168), so the Force
# table falls back to ION for ids the Force extractor could not pin (Docs/19 open item 3).
g4 = json.load(open(os.path.join(HERE, 'data', 'games.json')))
crown = out['tables']['CROWN']['names']
def pretty(tag):
    stem = re.sub(r'^g_|_removed$', '', tag)
    return stem.replace('_', ' ').title() + (' (retired)' if tag.endswith('_removed') else '')
def g4table(fam):
    names = {}
    for k, e in g4[fam].items():
        names[k] = e['desc'] or pretty(e['tag'])
    return names
ion = g4table('ION')
force = dict(ion)
force.update(g4table('FORCE'))
out['tables']['ION4'] = {'label': 'ION 2007-2014 (game-id enum)', 'source': 'scripts/data/games.json ION',
                         'names': ion, 'flags': {}}
out['tables']['FORCE4'] = {'label': 'Force 2007-2011 (game-id enum, gaps from ION)',
                           'source': 'scripts/data/games.json FORCE + ION', 'names': force, 'flags': {}}
for y in range(2007, 2015):
    out['versions']['ION %d' % y] = {'tables': ['ION4'], 'nearest': False}
for y in range(2007, 2012):
    out['versions']['Force %d' % y] = {'tables': ['FORCE4', 'ION4'], 'nearest': False}

dst = os.path.join(HERE, 'data', 'game_tables.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
for tid, t in out['tables'].items():
    print('%-9s %4d games  %s' % (tid, len(t['names']), t['label']))
