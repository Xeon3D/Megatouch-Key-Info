"""p21-optcatalog.py - build scripts/data/option_catalog.json: a readable label, a description and the
menu/key classification for every option slot, per software build.

Sources (all on disk):
  scripts/data/options.json            slot -> Merit's enum name (libenums.so, Docs/19)
  analysis/p21/helptext.json           Merit's own operator-menu help text (p21-help.py)
  analysis/p12/slot_classes_all.json   Gen 3 classes per build (P12: ruby2 .. crown)
  analysis/p21/<build>.slots.json      Gen 4 classes per build (p21-gen4slots.py)
Labels/descriptions marked 'merit' quote the help text; 'code' ones are written from the enum name and
the functions that read or write the slot (see the readers/writers in the per-build json).
"""
import json, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
A = os.path.join(ROOT, 'analysis')
enum = json.load(open(os.path.join(ROOT, 'scripts', 'data', 'options.json')))
helps = json.load(open(os.path.join(A, 'p21', 'helptext.json')))
HELP = {}
for b in ('I2014', 'FIREFLY', 'CROWN', 'SAPPHIRE', 'RUBY2'):
    for lab, txt in helps.get(b, []):
        HELP.setdefault(re.sub(r'\s+', ' ', lab).strip().rstrip(':').lower(), re.sub(r'\s+', ' ', txt).strip())

def h(label):
    t = HELP.get(label.lower())
    assert t, 'help text not found: %r' % label
    return t

U = 'Spare slot reserved by Merit; no code in the scanned builds reads it.'
# slot: (label, description or ('help', <Merit help label>))
CAT = {
 0x00: ('Free game in Solitaire', ('help', 'Enable free game in Solitaire')),
 0x01: ('Allow game continue', ('help', 'Allow game continue')),
 0x02: ('Rental mode', ('help', 'Enable Rental Mode')),
 0x03: ('Psychographic profiles', 'Lets the machine build player-preference ("psychographic") profiles. A toggle on '
        'System Options page 4; what it collects was not traced.'),
 0x04: ('Allow bonus replay', ('help', 'Allow bonus replay')),
 0x05: ('Price display: credits or money', ('help', 'Price Display')),
 0x06: ('Sort price descriptions', 'Sorts the price descriptions shown to players. No code in the scanned builds reads it.'),
 0x07: ('Split-column move in Power Solitaire', ('help', 'Split column move in Power Solitaire')),
 0x08: ('Erotic games (master switch)', ('help', 'Enable erotic games')),
 0x09: ('Show correct answer in trivia games', ('help', 'Show correct answer in Trivia, Power Trivia, TicTacTrivia and Snap Shot')),
 0x0A: ('Trivia rounds / bonus', ('help', 'Trivia rounds / bonus')),
 0x0B: ('TournaMAXX allowed in free play', 'Lets TournaMAXX games run while the machine is in free-play mode '
        '(checked by the game menu when a game is chosen).'),
 0x0C: ('TournaMAXX price differs from regular price', 'Charges a different price for the TournaMAXX version of a game '
        'than for normal play (read by the books\' game-cost calculation).'),
 0x0D: ('Six Stars operator shortcut', ('help', 'Enable 6 Stars')),
 0x0E: ('Free game in Power Solitaire', ('help', 'Enable free game in Power Solitaire')),
 0x0F: ('Rental mode: 5-row price table', 'Allows five rows in the coinless/rental (CCO) price table instead of the '
        'shorter default table.'),
 0x10: ('Touch2Play mode', 'Runs the machine as a Touch2Play product (changes the game menu and high-score screens).'),
 0x11: ('Women golfers in Golf', ('help', 'Golf has women')),
 0x12: ('Photo Hunt hints', ('help', 'Photo Hunt hints')),
 0x13: ('Merit Money', ('help', 'Enable Merit Money')),
 0x14: ('TournaMAXX', 'Enables TournaMAXX network tournaments (the "On-Line" choice of Select Tournament Mode). On '
        'Crown keys this is locked off, which is why TournaMAXX had to be enabled in the key.'),
 0x15: ('Music timer from Six Stars', ('help', 'Access Music Timer from 6 stars')),
 0x16: ('Player-selectable language', ('help', 'Player selectable language')),
 0x17: ('Auto-clear high scores', ('help', 'Auto Clear Hi Scores')),
 0x18: ('Allow clearing credits', 'Allows the operator to clear the credits on the machine. No code in the scanned '
        'builds reads it.'),
 0x19: ('Moan sounds in Strip Club', ('help', 'Allow moan sounds in Strip Club')),
 0x1A: ('High scores from Six Stars', ('help', 'Access Hi Score from 6 stars')),
 0x1B: ('Video billboard from Six Stars', ('help', 'Access VBB from 6 stars')),
 0x1C: ('Volume control from Six Stars', ('help', 'Access Volume Control from 6 stars')),
 0x1D: ('Disable free credits', 'Removes the free-credits function (the coin menus hide it).'),
 0x1E: ('Allow nudity', ('help', 'Allow nudity')),
 0x1F: ('Nudity level', 'Chooses how explicit the erotic games\' pictures are.'),
 0x20: ('Show deck cards', ('help', 'Show deck cards')),
 0x21: ('Checkerz rules', ('help', 'Checkerz Rules')),
 0x22: ('Fan time', ('help', 'Fan Time')),
 0x23: ('Language buttons have flags', ('help', 'Language buttons have flags')),
 0x24: ('Tournament support (internal)', 'Internal tournament switch written together with TournaMAXX by "Select '
        'Tournament Mode". On Crown it gated the Merit-thon / tournament bookkeeping screens.'),
 0x25: ('Calibration from Six Stars', ('help', 'Access Calibration from 6 stars')),
 0x26: ('Face-up cards in Tri-Towers', ('help', 'Face up cards, player selectable in Tri Towers')),
 0x27: ('Strip Club rewinds on loss', ('help', 'Strip Club rewinds on loss')),
 0x28: ('Kids category', ('help', 'Enable kids category')),
 0x29: ('Free play', ('help', 'Freeplay Enabled')),
 0x2A: ('Easy mode', ('help', 'Enable easy mode')),
 0x2B: ('Same category for all in Power Trivia', ('help', 'Category same for all in Power Trivia')),
 0x2C: ('Consolation question in Power Trivia', ('help', 'Enable consolation question in Power Trivia')),
 0x2D: ('My Merit', ('help', 'Enable My Merit')),
 0x2E: ('Continuous bonus round', ('help', 'Continuous bonus round')),
 0x2F: ('Senior mode', 'Turns on Senior Mode: games that support it play more slowly, and the books and menus treat '
        'the machine as a senior venue.'),
 0x30: ('Theft deterrent', ('help', 'Enable theft deterrent')),
 0x31: ('Lease mode (time bomb)', 'Puts the machine on a lease: it stops working after a set period unless the lease '
        'is renewed.'),
 0x32: ('TournaMAXX update from Six Stars', ('help', 'Access TournaMAXX update from 6 stars')),
 0x33: ('Promo credits', ('help', 'Enable Promo Credits')),
 0x34: ('Linked games (Mega-Link)', ('help', 'Linked games enabled')),
 0x35: ('No names in high scores', ('help', 'No Names in Hi Scores')),
 0x36: ('Web filter', ('help', 'Enable Web Filter')),
 0x37: ('High-resolution mode', ('help', 'Enable Hi Resolution Mode')),
 0x38: ('MegaWeb browser', ('help', 'Enable MegaWeb')),
 0x39: ('Prize Zone', ('help', 'Enable Prize Zone')),
 0x3A: ('Premium erotic (Penthouse)', ('help', 'Enable Premium Erotic')),
 0x3B: ('Entertainment Channel', ('help', 'Enable Entertainment Channel')),
 0x3C: ('Educational attract mode', ('help', 'Enable Educational Attract Mode')),
 0x3D: ('Coinless coin-op', ('help', 'Enable Coinless Coin Op')),
 0x3E: ('Hot Topics (downloadable content)', ('help', 'Enable Hot Topics')),
 0x3F: ('Quick pricing', 'Offers the Quick Price Setup screens in the coin menu (set the credit value, credits per '
        'game and display style in four steps).'),
 0x40: ('Premium erotic ads in idle', ('help', 'Enable Premium Erotic Ad Screens In Idle')),
 0x41: ('Attract mode sounds', ('help', 'Enable Attract Mode Sounds')),
 0x42: ('Operator website', 'Turns on the operator\'s own website feature in the network menu.'),
 0x43: ('MindSpark mode', 'Runs the machine as a MindSpark-branded product (the platform check reads it).'),
 0x44: ('ShowTenders (old switch)', ('help', 'Enable ShowTenders Cocktail College')),
 0x45: ('Auto-continue', ('help', 'Enable Auto-Continue')),
 0x46: ('Card back advertising', ('help', 'Enable Card Back Advertising')),
 0x47: ('Premiere tournament terminal', 'Makes the machine a Premiere tournament terminal (changes the menu layout '
        'and the AMI link).'),
 0x48: ('Sticker Book timer', ('help', 'Sticker Book Timer settings')),
 0x49: ('Player key (Megatouch Nation)', ('help', 'Enable Megatouch Nation')),
 0x4A: ('Bowling Poker', 'Enables the Bowling Poker game. No code in the scanned builds reads it.'),
 0x4B: ('Force slow senior game play', ('help', 'Force Slow Senior Game Play')),
 0x4C: ('High resolution for TouchTunes', 'Switches to high resolution for TouchTunes remote setup.'),
 0x4D: ('Erotic games in attract mode', 'Shows erotic games in the attract mode. No code in the scanned builds reads it.'),
 0x4E: ('Erotic games in New Games', 'Lists erotic games in the New Games category. No code in the scanned builds reads it.'),
 0x4F: ('Erotic games into New Games automatically', 'Places new erotic games in the New Games category '
        'automatically. No code in the scanned builds reads it.'),
 0x50: ('Network options from Six Stars', 'Allows the network options through Six Stars. No code in the scanned '
        'builds reads it (slot 0x76 is the one the menus use).'),
 0x51: ('Alternate language selection', 'Uses the alternate language-selection screen.'),
 0x52: ('Operator setup from Six Stars', ('help', 'Access Operator Setup from 6 stars')),
 0x53: ('Unlock Firefly from Six Stars', ('help', 'Access Unlock Firefly from 6 stars')),
 0x54: ('Players can unlock Firefly', 'Lets players unlock a Firefly machine themselves.'),
 0x55: ('Prize pools on main menu', ('help', 'Show Prize Pools on Main Menu')),
 0x56: ('Location card setup from Six Stars', 'Allows the location card setup through Six Stars (Firefly).'),
 0x57: ('Spare slot (default yes)', U),
 0x58: ('TouchTunes', 'Enables the TouchTunes jukebox integration.'),
 0x59: ('KidZpace mode', 'Runs the machine in KidZpace (children\'s venue) mode; the books and coin menus change.'),
 0x5A: ('Free credits from Six Stars', ('help', 'Access Free Credits Menu from 6 stars')),
 0x5B: ('Bypass wireless security', 'Skips the wireless-network security setup (Firefly).'),
 0x5C: ('Allow coin-in table changes', 'Lets the operator edit the coin-in table.'),
 0x5D: ('UAE prize mode', 'Prize mode for the United Arab Emirates market; the books menus change.'),
 0x5E: ('Spare slot (default no)', U),
 0x5F: ('Spare slot (default no)', U),
 0x60: ('Disable questionable content', ('help', 'Disable Questionable Content')),
 0x61: ('Turn off automatic reconnect', 'Stops the machine reconnecting to the network automatically. No code in '
        'the scanned builds reads it.'),
 0x62: ('Disable exit from AMI during playback', ('help', 'Disable Exit From AMI During Music Playback')),
 0x63: ('AMI jukebox', ('help', 'Enable AMI')),
 0x64: ('Credit cards', 'Accepts credit-card payments.'),
 0x65: ('Credit cards pulse the hard meter', 'Counts credit-card payments on the hardware coin meter.'),
 0x66: ('Spare slot (default no)', U),
 0x67: ('Firefly mode', 'Runs the machine as a Firefly.'),
 0x68: ('Spare slot (always on)', U), 0x69: ('Spare slot (always on)', U), 0x6A: ('Spare slot (always on)', U),
 0x6B: ('Spare slot (always on)', U), 0x6C: ('Spare slot (always on)', U),
 0x6D: ('MegaNet without TournaMAXX', 'Allows the MegaNet services even when TournaMAXX is off.'),
 0x6E: ('Spare slot (never on)', U), 0x6F: ('Spare slot (never on)', U), 0x70: ('Spare slot (never on)', U),
 0x71: ('Spare slot (never on)', U),
 0x72: ('Download selector', 'Shows the download selector for new games and content.'),
 0x73: ('Credit card demo mode', 'Demonstration mode for credit-card payments. No code in the scanned builds reads it.'),
 0x74: ('ShowTenders / Cocktail College', ('help', 'Enable Cocktail College')),
 0x75: ('Revenue share', 'Revenue-sharing accounting. No code in the scanned builds reads it.'),
 0x76: ('Network menu from Six Stars', ('help', 'Access Network Menu from 6 stars')),
 0x77: ('Spare slot (never on)', U),
}
# Where the Crown-era analysis (Docs/04, P8-P12) read a slot differently from Merit's later enum name.
CROWN_NOTE = {   # slot: (label as read on Jade/Crown, what the Jade/Crown code does with it)
 0x0C: ('Local tournament in progress', 'Jade/Crown: runtime "local tournament in progress" flag.'),
 0x0F: ('Pay-per-time (CCO)', 'Jade/Crown: turns on pay-per-time (coinless coin-op) pricing.'),
 0x2F: ('Special screen / demo mode', 'Jade/Crown: read only by a special screen/demo mode that forces game bits.'),
 0x43: ('Scrolling marquee text', 'Jade/Crown: scrolling marquee text.'),
 0x47: ('Hide TournaMAXX ranking screens', 'Jade 2/Crown: hides the TournaMAXX ranking/events screens.'),
}

out = {'slots': {}, 'builds': {}}
for s in range(0x78):
    lab, d = CAT[s]
    src = 'merit' if isinstance(d, tuple) else 'code'
    text = h(d[1]) if isinstance(d, tuple) else d
    text = text.replace('&#162;', '¢')
    cl, cn = CROWN_NOTE.get(s, ('', ''))
    out['slots'][str(s)] = {'label': lab, 'desc': text, 'source': src, 'enum': enum.get(str(s), ''),
                            'crown_label': cl, 'crown_note': cn}

# Classes: unify to menu / key / runtime / remote / unused
G3 = json.load(open(os.path.join(A, 'p12', 'slot_classes_all.json')))
MAP3 = {'operator': 'menu', 'key': 'key', 'runtime': 'runtime', 'remote': 'remote', 'unused': 'unused'}
for b, v in G3.items():
    out['builds'][b] = {k: MAP3[c] for k, c in v['classes'].items()}
for b in ('I2011', 'I2014', 'T2P2013', 'FIREFLY'):
    v = json.load(open(os.path.join(A, 'p21', b + '.slots.json')))
    out['builds'][b] = {k: {'menu': 'menu', 'key': 'key', 'none': 'unused'}[x['class']] for k, x in v.items()}

# DOS: SETUP.DLL reaches NVRAM through import fixups whose additive is the offset (P13), so every
# option slot it addresses directly is known. Most menu toggles go through an index table instead,
# so only "menu" is asserted; everything else stays "untraced" (never "key").
OPT_BASE_DOS = {0x4D: 0x108, 0x50: 0x138, 0x53: 0x138, 0x59: 0x445, 0x5A: 0x445, 0x5D: 0x445,
                0x65: 0x3CF, 0x66: 0x3CF}
DOS_REP = {'DOS_306': 'MAXX_V3.06_-_Played', 'DOS_2K': 'MAXX_2K_V4.00_-_Played',
           'DOS_2KP': 'MAXX_2K_Plus_V5.00_-_Played', 'DOS_PLAT': 'XL_Platinum_V1.02_-_Played',
           'DOS_DIA': 'MAXX_Diamond_V6.03_-_New', 'DOS_DD': 'MAXX_Double_Diamond_V7.01_-_New',
           'DOS_TIT': 'XL_Titanium_V3.00_-_Keyless_Played', 'DOS_EME': 'MAXX_Emerald_V8.04_-_Original'}
for b, img in DOS_REP.items():
    nv = open(os.path.join(A, 'p9', 'nvram', img + '.NVRAM.DAT'), 'rb').read()
    base = OPT_BASE_DOS[nv[9]]
    offs = {int(l.split('	')[0], 16) for l in open(os.path.join(A, 'p13', img + '.setup.nvmap.tsv'))
            .readlines()[1:]}
    out['builds'][b] = {str(i): ('menu' if base + i in offs else 'untraced') for i in range(80)}

dst = os.path.join(ROOT, 'scripts', 'data', 'option_catalog.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('wrote', dst, len(out['slots']), 'slots,', len(out['builds']), 'builds',
      sum(1 for x in out['slots'].values() if x['source'] == 'merit'), 'with Merit help text')
