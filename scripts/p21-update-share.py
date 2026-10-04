"""p21-update-share.py - bring share/megatouch-security-keys.html up to date with P21 (Docs/21), then
regenerate the plain-language guide from keyinfo-human.md (via p20-update-share.py's renderer).

Patches in place, every anchor asserted (a missed anchor is an error, not a silent no-op); a sentinel
makes a second run skip the research page.

    python scripts/p21-update-share.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'share', 'megatouch-security-keys.html')
SENTINEL = '<!-- p21: option table on every DS1991 key, per-family layouts, key editor -->'

LAYOUTS = """
    <h3>Where each key family keeps its options and games</h3>
    <p>Every key up to 2006 carries the option table, the XL and DOS MAXX keys included: their
    <code>DATA2[0..0x13]</code> matches the operator-option bytes of every DOS settings file (locked
    slots 100%). Games are stored differently in each family:</p>
    <div class="tbl"><table>
      <thead><tr><th>Family</th><th>Options</th><th>Games</th><th>Prices</th></tr></thead>
      <tbody>
        <tr><td>XL, DOS MAXX, Force 2002</td><td class="mono">DATA2[0..0x13], 80</td><td>one nibble per game 0x00–0x3F in <code>DATA1</code>, 0 = off</td><td>the nibble (Diamond era); a class code on Emerald/Titanium</td></tr>
        <tr><td>Ruby 2, Force 2003</td><td class="mono">DATA2[0..0x13], 80</td><td>all on, except bytes with bit 7 set in the <code>DATA1</code> list</td><td><code>(game, price)</code> pairs; default <code>DATA2[0x22]</code></td></tr>
        <tr><td>Sapphire, Force 2004</td><td class="mono">DATA2[0x16..0x2B], 88</td><td>bitmap <code>DATA1[0x12..]</code></td><td>price list <code>DATA1[0..0x11]</code>; default <code>DATA2[2]</code></td></tr>
        <tr><td>Jade, Crown, Force 2005/2006, ION 2006</td><td class="mono">DATA2[0..0x13], 80</td><td>bitmap <code>DATA2[0x14..]</code></td><td>price list <code>DATA1[0..0x1B]</code>; default <code>DATA1[0x2A]</code></td></tr>
        <tr><td>Force / ION 2007+</td><td class="mono">0x2DD, 120 × 1 byte</td><td>bitmap at <code>0x3BF</code> (2007: priced = on)</td><td>one byte per game at <code>0x1B0</code></td></tr>
      </tbody>
    </table></div>
"""

EDITOR = """
  <section id="editor">
    <div class="sec-head"><h2>The key editor</h2><span class="tag">Megatouch Key Tool</span></div>
    <p>Everything on this page is built into one program that opens, edits and generates keys for all
    33 releases from XL R1 to ION 2014 (a single Windows <code>.exe</code>, or Python source). It shows
    every option with a plain name and a description, in Merit's own operator help text for 67 of the
    120 slots, grouped by who sets it: the operator menus, or the key alone. Games carry the names from
    that release's own game table. When the button serial is changed it checks the 1-Wire checksum, the
    button family and the serial window the release enforces, and can suggest a serial the release
    accepts. Every save is re-decrypted to verify it.</p>
  </section>
"""


def patch(s):
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, 'anchor not found exactly once: %r' % a[:80]
        s = s.replace(a, b)
    rep('<span class="pill ok">Confirmed</span> 80 two-bit option slots.</div>',
        '<span class="pill ok">Confirmed</span> 80 two-bit option slots on every key up to 2006, 120 from 2007.</div>')
    rep('A per-game enable bitmap and price list sit next to it.</p>',
        'The XL and DOS MAXX keys carry the same table; Sapphire keys have 88 slots.</p>')
    rep('<div class="sec-head"><h2>Option locks</h2><span class="tag">DATA2, 80 slots × 2 bits</span></div>',
        '<div class="sec-head"><h2>Option locks</h2><span class="tag">DATA2, 80 slots × 2 bits, every DS1991-era key</span></div>')
    i = s.index('<h2>Option locks</h2>')
    j = s.index('</table></div>', i) + len('</table></div>')
    s = s[:j] + '\n' + LAYOUTS + s[j:]
    rep('<li>TournaMAXX (slot 0x14) is a key-only switch in every build from Ruby 2 to Crown.</li>',
        '<li>TournaMAXX (slot 0x14) is a key-only switch in every build from Ruby 2 to Crown. On ION it '
        'became a menu toggle ("Select Tournament Mode"), still usable only when the key leaves it '
        'selectable.</li>')
    rep("""      <li><strong>Game names</strong> for 8 ION slots and most of the Force-line slots. A limitation of
      the table extractor, not a gap in the format: the key data decodes either way.</li>""",
        """      <li><strong>Game names</strong> for 8 ION slots. The Force-line gaps are filled from ION, which
      agrees on all 168 Force ids that could be pinned.</li>""")
    rep("""      <li><strong>Option names on the DOS machines</strong>, and the credit-book rows in the Linux
      <code>amusement.db</code> (an obsolete SQLite&nbsp;2 file).</li>""",
        """      <li><strong>Which options the DOS operator menus offer.</strong> The DOS keys carry the same
      80-slot table, but the DOS menus reach most slots through an index table that has not been
      traced, so about 20 are confirmed as menu settings. Also the credit-book rows in the Linux
      <code>amusement.db</code> (an obsolete SQLite&nbsp;2 file).</li>""")
    rep("""      <li><strong>Why a Jade-labelled key carries the Force platform bit.</strong>""",
        """      <li><strong>The Force 2007–2011 operator menus</strong>, not among the extracted files; those keys'
      options are classified from ION 2011's menus.</li>
      <li><strong>Why a Jade-labelled key carries the Force platform bit.</strong>""")
    k = s.index('<section id="open">') if '<section id="open">' in s else s.index('<h2>Open items</h2>')
    k = s.rfind('<section', 0, k + 1)
    s = s[:k] + EDITOR.lstrip('\n') + '\n  ' + s[k:]
    rep('<a href="#open">', '<a href="#editor">Key editor</a><a href="#open">')
    return s.rstrip('\n') + '\n' + SENTINEL + '\n'   # after </html>, like the P20 sentinel


def main():
    s = open(PAGE, encoding='utf-8').read()
    if SENTINEL in s:
        print('megatouch-security-keys.html already has the P21 changes, skipped')
    else:
        open(PAGE, 'w', encoding='utf-8').write(patch(s))
        print('megatouch-security-keys.html patched (P21)')
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'p20-update-share.py')],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(r.stderr)


if __name__ == '__main__':
    main()
