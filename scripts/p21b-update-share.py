"""p21b-update-share.py - finish the share pages for P21 (Docs/21).

p21-update-share.py added the per-family layout table and the key-editor section. This adds what
was still missing from the research page - option meanings and the per-release menu/key-only split,
the Force serial-window identity, the Gen 4 container rule, per-release game names - fixes the page
header (it still said "1997-2005 ... to MAXX Crown"), puts the key-editor section where the table of
contents points, and regenerates the plain-language guide from the updated keyinfo-human.md.

Every anchor is asserted; a sentinel makes a second run skip the research page.

    python scripts/p21b-update-share.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, 'share', 'megatouch-security-keys.html')
SENTINEL = '<!-- p21b: option meanings, menu/key split per release, Force windows, game tables -->'

SERIAL = """    <h3>The Force cabinets enforce the Maxx windows</h3>
    <p>Force ran the same software as the Maxx of the same year, so it enforces the same ranges. That
    was settled by comparing the packed <code>start</code> launchers byte for byte: Force 2003.5 v11.00
    is identical to Maxx Ruby&nbsp;2 V11.00, Force 2005 v14.00 to Maxx Jade V14.00, and Force 2005.5
    v15.10 to Maxx Jade&nbsp;2 V15.10. The other Force builds (2003 v10.09, 2004, 2006 and ION 2006)
    have no matching binary in the collection, so they are taken to follow their nearest Maxx sibling.</p>
    <p>The 2007-and-later keys have no window at all — the cipher is keyed from the button's serial,
    so a key simply decrypts to garbage on the wrong button and fails its own checksum. What those
    releases do constrain is the button type: it must be a DS1995 or DS1996, and large enough for the
    release's block offset. ION 2013 writes its block at 7&nbsp;KB, so only a DS1996 will do.</p>
"""

OPTMEAN = """    <h3>What each slot does, and which releases offer it</h3>
    <p>Merit's own operator help text survives inside the later programs as
    <code>&lt;b&gt;Label&lt;/b&gt;|text</code> strings. It covers <strong>67 of the 120</strong> slots,
    so for those the description is Merit's wording rather than an inference; the other 53 are described
    from the code that reads them. Five slots (0x0C, 0x0F, 0x2F, 0x43, 0x47) meant something different
    in the Crown era than the name Merit later gave them, so both readings are recorded and the
    Crown-era one is shown for Crown-era keys.</p>
    <p>Who may write a slot was then read out of each release's own operator menus. That split is what
    makes a slot a licence rather than a preference, and it moves release by release:</p>
    <div class="tbl"><table>
      <thead><tr><th>Release</th><th>Operator menu</th><th>Key only</th><th>Other</th></tr></thead>
      <tbody>
        <tr><td>Ruby 2</td><td>38</td><td>5</td><td>37 unused</td></tr>
        <tr><td>Sapphire</td><td>51</td><td>5</td><td>1 runtime, 23 unused</td></tr>
        <tr><td>Sapphire 2</td><td>52</td><td>7</td><td>1 runtime, 20 unused</td></tr>
        <tr><td>Jade</td><td>52</td><td>9</td><td>1 runtime, 1 remote, 17 unused</td></tr>
        <tr><td>Jade 2, Crown</td><td>53</td><td>10</td><td>1 runtime, 1 remote, 15 unused</td></tr>
        <tr><td>ION 2011 / 2014, Touch2Play 2013</td><td>69</td><td>18</td><td>33 unused</td></tr>
        <tr><td>Firefly 2010</td><td>74</td><td>13</td><td>33 unused</td></tr>
        <tr><td>DOS builds</td><td>16–20 traced</td><td class="dim">—</td><td>the rest go through an index table that has not been traced</td></tr>
      </tbody>
    </table></div>
    <p>Force 2007–2011 drives its options through an older <code>KeyManager::Option(int)</code> API and
    its operator menus are not among the recovered files, so those keys are read with the ION 2011
    split.</p>
"""

GAMETABLES = """    <h3>A game number only means something next to its release</h3>
    <p>A key stores games by number, and the number is nothing more than a position in that release's
    game table — <code>GAMEDATA.DAT</code> on DOS, <code>gamedata.dat</code> on Linux, a compiled enum
    from 2007 on. The same number is therefore a different game on a different release, so naming a
    key's games means using its own software's table. Twenty-four release tables were recovered, plus
    the two compiled into the Force and ION programs.</p>
    <ul class="plain">
      <li>Ruby, Ruby 2 and Force 2003 keep <code>/usr/local/share/merit</code> on partition 7, so their
      table lives at <code>/config/gamedata.dat</code> there.</li>
      <li>Force 2006 ships a <em>stale</em> table: the only image's file is entry-for-entry Force 2003's
      102 games, while the Force 2006 key prices Crown-era numbers up to 0xC1. Force 2006 and ION 2006
      are read with Crown's 195-entry table instead.</li>
      <li>The Force numbering agrees with the ION enum on all 168 numbers that could be pinned, so the
      ION names fill the Force gaps.</li>
    </ul>
"""


def patch(s):
    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, 'anchor not found exactly once: %r' % a[:90]
        s = s.replace(a, b)

    # --- header: the page covers 1997-2014 now, and the corpus grew
    rep('<div class="eyebrow">Reverse-engineering notes · Merit Megatouch, 1997–2005</div>',
        '<div class="eyebrow">Reverse-engineering notes · Merit Megatouch, 1997–2014</div>')
    rep('How the Dallas iButton keys work across every Megatouch version from XL R1 to MAXX Crown:'
        ' what the software checks, what the key contains, and why a given key does or doesn\'t boot.',
        'How the Dallas iButton keys work across every Megatouch version from XL R1 to ION 2014 — the'
        ' Maxx/XL line and the Force / ION line: what the software checks, what the key contains, and'
        ' why a given key does or doesn\'t boot.')
    rep('<span>60 key dumps decrypted, every one byte-exact</span>',
        '<span>107 key dumps decrypted and re-encrypted, every one byte-exact</span>')

    # --- serial windows: the Force builds, and the Gen 4 container rule
    rep('''    <p>The check is guarded by an anti-debug trap: if a breakpoint byte (INT3) is found inside it, the game loops forever printing "Not Jersey Key, Not Dallas Key, must be Florida Key". At runtime the game re-reads the serial and shuts down after ten mismatches ("SECURITY KEY MISMATCH").</p>
  </section>''',
        '''    <p>The check is guarded by an anti-debug trap: if a breakpoint byte (INT3) is found inside it, the game loops forever printing "Not Jersey Key, Not Dallas Key, must be Florida Key". At runtime the game re-reads the serial and shuts down after ten mismatches ("SECURITY KEY MISMATCH").</p>
''' + SERIAL + '  </section>')

    # --- option locks: meanings and the per-release menu/key split
    rep('''    <p>Of the rest, one slot is set by the game at runtime (0x0C), one only by the MegaNet server (0x1A), and 15 are never read by Crown.</p>''',
        '''    <p>Of the rest, one slot is set by the game at runtime (0x0C), one only by the MegaNet server (0x1A), and 15 are never read by Crown.</p>
''' + OPTMEAN.rstrip('\n'))

    # --- the closing paragraph of the option section described only the Jade/Crown layout
    rep('Gen 3 keys also carry a 224-bit per-game enable bitmap (DATA2[0x14..0x2F]) and a game price'
        ' list in DATA1, where bytes 0xF0–0xFF set the price for the game IDs that follow.',
        'Jade and Crown keys also carry a 224-bit per-game enable bitmap (DATA2[0x14..0x2F]) and a game'
        ' price list in DATA1, where bytes 0xF0–0xFF set the price for the game IDs that follow.'
        ' Sapphire keeps both in DATA1 instead, and its option table sits at DATA2[0x16] — see the'
        ' layout table above.')

    # --- Force / ION: per-release game tables
    rep('''    <p class="muted">Verification: every Force/ION DS1991-era dump decrypts byte-exact and
    re-encrypts byte-exact, and the password generators reproduce the passwords stored in 48 of 49
    dumps across the whole collection.</p>
  </section>''',
        GAMETABLES + '''    <p class="muted">Verification: every Force/ION DS1991-era dump decrypts byte-exact and
    re-encrypts byte-exact, and the password generators reproduce the passwords stored in 48 of 49
    dumps across the whole collection.</p>
  </section>''')

    # --- the key-editor section sits before the 2007-format one; the TOC lists it after
    i = s.index('    <section id="editor">')
    j = s.index('</section>', i) + len('</section>')
    block = s[i:j]
    s = s[:i] + s[j:]
    k = s.index('  <section id="open">')
    s = s[:k] + block.replace('    <section id="editor">', '  <section id="editor">') + '\n\n' + s[k:]

    # --- the editor does more than it did when the section was written
    rep('''accepts. Every save is re-decrypted to verify it.</p>''',
        '''accepts. Every save is re-decrypted to verify it.</p>
    <p>Its regression suite loads all 107 dumps in the collection, round-trips every one, generates a
    key for each of the 33 releases, and asserts the layout, name and serial rules above.</p>''')
    return s.rstrip('\n') + '\n' + SENTINEL + '\n'


def main():
    s = open(PAGE, encoding='utf-8').read()
    if SENTINEL in s:
        print('megatouch-security-keys.html already has the P21b changes, skipped')
    else:
        out = patch(s)                      # build first: a failure must not truncate the page
        open(PAGE, 'w', encoding='utf-8').write(out)
        print('megatouch-security-keys.html patched (P21b), %d bytes' % len(out.encode('utf-8')))
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'p20-update-share.py')],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit(r.stderr)


if __name__ == '__main__':
    main()
