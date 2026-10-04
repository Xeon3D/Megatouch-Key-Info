"""p19-games4.py - build the Gen4 game-id table (id -> name) for Force/ION.

Gen4 moved the game table to /usr/local/gamedata/config/gamedata.xml, which carries a
symbolic GameId (G_FOO) and a Description per game. The key indexes games by the numeric
xml_gameinfo::GameIds enum value; the binary holds the G_* identifier strings in enum
order, so the enum value is the position of that string in the binary's string table.
This cross-checks the XML order against the binary order and writes a JSON table.

usage: p19-games4.py <tag> [...]      e.g. p19-games4.py F2011 I2014
"""
import sys, os, re, json

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'analysis', 'p19')
GAME_RE = re.compile(r'<game>(.*?)</game>', re.S)
TAG_RE = re.compile(r'<(\w+)>(.*?)</\1>', re.S)


def from_xml(tag):
    p = os.path.join(ROOT, 'xml', tag, 'gamedata.xml')
    if not os.path.exists(p):
        return []
    txt = open(p, encoding='latin1').read()
    out = []
    for m in GAME_RE.finditer(txt):
        d = {k: v.strip() for k, v in TAG_RE.findall(m.group(1))}
        out.append((d.get('GameId', '?'), d.get('Description', ''), d.get('ShortGameDesc', '')))
    return out


def from_binary(tag):
    """G_* identifiers in the order they appear in the binary's string data."""
    p = os.path.join(ROOT, 'bin', tag, 'start')
    if not os.path.exists(p):
        return []
    data = open(p, 'rb').read()
    seen, order = set(), []
    for m in re.finditer(rb'\x00(G_[A-Z0-9_]{2,60})\x00', data):
        n = m.group(1).decode()
        if n not in seen:
            seen.add(n)
            order.append(n)
    return order


def main():
    for tag in sys.argv[1:]:
        xml = from_xml(tag)
        binorder = from_binary(tag)
        print('=== %s : gamedata.xml %d games, binary G_* strings %d'
              % (tag, len(xml), len(binorder)))
        if not xml:
            continue
        xmlnames = [g[0] for g in xml]
        same = xmlnames[:len(binorder)] == binorder[:len(xmlnames)]
        print('    xml order == binary string order : %s' % same)
        tbl = {}
        for i, (gid, desc, short) in enumerate(xml):
            tbl[i] = {'name': gid, 'desc': desc, 'short': short}
        out = os.path.join(ROOT, 'json')
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, '%s.games.json' % tag), 'w') as f:
            json.dump(tbl, f, indent=1)
        for i in list(range(6)) + [0x44, 0x12A, 0x12B]:
            if i in tbl:
                print('      %3X  %-32s %s' % (i, tbl[i]['name'], tbl[i]['desc']))
        print('    wrote %s.games.json (%d entries)' % (tag, len(tbl)))


if __name__ == '__main__':
    main()
