"""p20-update-share.py - bring the shareable HTML pages up to date with P18-P20.

Two outputs in share/:
  megatouch-security-keys.html  the research page. Patched in place: two new sections
                                (Force/ION line, the 2007 key format), new table-of-contents
                                entries, refreshed header counts, and a rewritten Open items
                                section. The hand-made design is left alone.
  megatouch-keys-guide.html     regenerated wholesale from keyinfo-human.md by make-share.py's
                                renderer, reusing the research page's stylesheet.

Idempotent: a sentinel comment makes a second run a no-op for the patched page.

    python scripts/p20-update-share.py
"""
import os
import re
import sys
import html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARE = os.path.join(ROOT, 'share')
PAGE = os.path.join(SHARE, 'megatouch-security-keys.html')
GUIDE = os.path.join(SHARE, 'megatouch-keys-guide.html')
SENTINEL = '<!-- p20: Force/ION + Gen 4 sections added -->'

FORCE_SECTION = """
  <section id="forceion">
    <div class="sec-head"><h2>The Force / ION line</h2><span class="tag">2002–2014</span></div>
    <p>Force and ION are not separate systems. They are the <strong>same software as the Maxx of the
    same year</strong>, and the key decides which product the machine becomes — Maxx Ruby&nbsp;2 V11.00
    and Force 2003.5 share a game binary, as do Jade&nbsp;2 V15.10 and Force 2005.5. Through 2006 the
    Force and ION keys reuse their Maxx cousin's cipher byte for byte; only the signature and the
    password constants differ. Force 2003 even uses the <em>same passwords</em> as Maxx Ruby&nbsp;2.</p>
    <div class="tbl"><table>
      <thead><tr><th>Version</th><th>Button</th><th>Cipher</th><th>Signature</th></tr></thead>
      <tbody>
        <tr><td>Force 2002 <span class="muted">(a DOS build)</span></td><td>DS1991</td><td>= Emerald</td><td><code>DD62104321100293</code></td></tr>
        <tr><td>Force 2003</td><td>DS1991</td><td>= Ruby</td><td><code>DE62104321100293</code></td></tr>
        <tr><td>Force 2004</td><td>DS1991/DS1425</td><td>= Sapphire</td><td><code>1234567890ABCDEF</code></td></tr>
        <tr><td>Force 2005</td><td>DS1425</td><td>= Jade</td><td><code>8723879FE2432498</code></td></tr>
        <tr><td>Force 2006</td><td>DS1425</td><td>= Crown</td><td><code>8624879FE2432498</code></td></tr>
        <tr><td>ION 2006</td><td>DS1425</td><td>= Crown</td><td><code>342190FA11880410</code></td></tr>
        <tr><td>Force 2007–2011</td><td><strong>DS1996</strong></td><td>Gen&nbsp;4 keystream</td><td>per year, see below</td></tr>
        <tr><td>ION 2007</td><td><strong>DS1995</strong></td><td>Gen&nbsp;4 keystream</td><td><code>42367123EF235334</code></td></tr>
        <tr><td>ION 2008–2014</td><td><strong>DS1996</strong></td><td>Gen&nbsp;4 keystream</td><td>per year</td></tr>
      </tbody>
    </table></div>
    <p>This also settles an old question. The Crown key gate accepts two signature values, and the
    second (ending <code>87</code>) was suspected to be the Force one. It is not: Force 2005 carries
    exactly the same signature as Maxx Jade, and the Force/Maxx difference lands on the <em>first</em>
    byte instead — Force 2006 reads <code>86&nbsp;24…</code> where Crown reads
    <code>87&nbsp;23…</code>. That is the cabinet-platform modifier seen from the key side for the
    first time. The <code>87</code>-ending variant belongs to a different rule, about high-bit
    characters in the territory name.</p>
    <p class="muted">Verification: every Force/ION DS1991-era dump decrypts byte-exact and
    re-encrypts byte-exact, and the password generators reproduce the passwords stored in 48 of 49
    dumps across the whole collection.</p>
  </section>
"""

GEN4_SECTION = """
  <section id="gen4">
    <div class="sec-head"><h2>The 2007 key format</h2><span class="tag">Force 2007+, ION 2007+</span></div>
    <p>In 2007 Merit abandoned the DS1991 MultiKey. From Force 2007 and ION 2007 the key is an ordinary
    memory iButton — a <strong>DS1995</strong> (2&nbsp;KB) or <strong>DS1996</strong> (8&nbsp;KB) —
    with <strong>no protected compartments and no passwords at all</strong>. The entire key is one
    1024-byte block in plain memory, and only a weak keystream stands in front of it.</p>
    <p>That keystream is a repeating six-byte pattern built from the button's serial and a per-year
    constant. Since the plaintext always begins with the part number <code>SAnnnn</code>, six known
    characters hand over the whole pattern, and long runs of blank data print it outright. Running the
    derivation backwards even recovers the button's serial number — which is how two unlabelled
    dumps in the collection were identified, one as a Force 2011 key and one as an ION 2014 key read
    over USB.</p>
    <p>The layout was read straight out of the game software: <code>KeyManager::Read</code> copies the
    decrypted block into its own object at offset zero, so every field offset in the code <em>is</em> a
    key offset.</p>
    <div class="tbl"><table>
      <thead><tr><th>Offset</th><th>Field</th></tr></thead>
      <tbody>
        <tr><td><code>0x000</code></td><td>part number, <code>SAnnnnTT</code></td></tr>
        <tr><td><code>0x009</code></td><td>programming date — now a Unix timestamp, not text</td></tr>
        <tr><td><code>0x00D</code></td><td>revision</td></tr>
        <tr><td><code>0x016</code></td><td>territory name</td></tr>
        <tr><td><code>0x02A</code></td><td>MegaNet server address, as readable text</td></tr>
        <tr><td><code>0x0F2</code></td><td>country code, New Jersey exception, lockout value</td></tr>
        <tr><td><code>0x0F5</code></td><td><strong>signature</strong></td></tr>
        <tr><td><code>0x104</code></td><td>language masks; currency names at <code>0x114</code></td></tr>
        <tr><td><code>0x172</code></td><td>six coin channels: value, credits, credit value</td></tr>
        <tr><td><code>0x1B0</code></td><td><strong>price for each of 300 games</strong>, two nibbles per byte (play / continue)</td></tr>
        <tr><td><code>0x2DD</code></td><td><strong>120 option switches</strong>, one byte each</td></tr>
        <tr><td><code>0x355</code></td><td><strong>16-bit checksum</strong></td></tr>
        <tr><td><code>0x35B</code></td><td>web portal address</td></tr>
        <tr><td><code>0x3BF</code></td><td><strong>game enable bitmap</strong>, 300 bits</td></tr>
        <tr><td><code>0x3EF</code></td><td>region</td></tr>
        <tr><td><code>0x3F0</code></td><td>serial-tied bytes the game never reads</td></tr>
      </tbody>
    </table></div>
    <p>Two checks the earlier keys did not have: a <strong>16-bit checksum</strong> over the block, and
    an integrity check in which the program <strong>reads its own executable file</strong> while
    validating the key. One check was dropped: the laser-serial window is gone, because keying the
    cipher to the button's serial made it redundant.</p>
    <p class="muted">Verification: all 22 Gen&nbsp;4 dumps decrypt byte-exact against the reference
    plaintexts, every stored checksum validates, and all 22 re-encrypt byte-exact. The checksum the
    software itself computes matches the independent implementation exactly.</p>
  </section>
"""

OPEN_ITEMS = """
  <section id="open">
    <div class="sec-head"><h2>Open items</h2><span class="tag">what is still unknown</span></div>
    <ul class="plain">
      <li><strong>A genuine ION 2014 key dump.</strong> The only sample contradicts itself — country
      code 1 (Canada) with territory text <code>USA-STD</code>, and a date that decodes to 1977 — so
      it is almost certainly hand-made.</li>
      <li><strong>The serial-tied bytes</strong> at offset <code>0x012</code> and the three copies at
      <code>0x3F0</code> on Gen&nbsp;4 keys. Six otherwise byte-identical ION 2009 keys differ in
      nothing else, and the game never reads <code>0x3F0</code> — most likely the programmer's own
      anti-clone marker.</li>
      <li><strong>Game names</strong> for 8 ION slots and most of the Force-line slots. A limitation of
      the table extractor, not a gap in the format: the key data decodes either way.</li>
      <li><strong>The 2007-and-later settings memory</strong>, which moved to XML files plus SQLite, so
      none of the earlier NVRAM mapping carries over.</li>
      <li><strong>The executable self-read</strong> inside the Gen&nbsp;4 key check — found, not
      analysed.</li>
      <li><strong>Option names on the DOS machines</strong>, and the credit-book rows in the Linux
      <code>amusement.db</code> (an obsolete SQLite&nbsp;2 file).</li>
      <li><strong>Why a Jade-labelled key carries the Force platform bit.</strong> Two keys with the
      same part number SA3079 differ in it, so it is a per-key choice rather than a property of the
      part number.</li>
      <li>MegaNet server-side serial checks remain out of scope — they run on Merit's servers.</li>
    </ul>
  </section>
"""


def patch_page():
    s = open(PAGE, encoding='utf-8').read()
    if SENTINEL in s:
        print('megatouch-security-keys.html already updated, skipped')
        return
    # 1. table of contents
    old_toc = '<a href="#crown">Crown crypto</a><a href="#open">Open items</a>'
    assert old_toc in s, 'table of contents anchor not found'
    s = s.replace(old_toc,
                  '<a href="#crown">Crown crypto</a>'
                  '<a href="#forceion">Force / ION</a><a href="#gen4">2007 format</a>'
                  '<a href="#open">Open items</a>', 1)

    # 2. header scope + counts
    old_lede = ('How the Dallas iButton keys work across every Megatouch version from XL R1 to '
                'MAXX Crown: what the software checks, what the key contains, and why a given key '
                'does or doesn’t boot.')
    if old_lede in s:
        s = s.replace(old_lede,
                      'How the Dallas iButton keys work across every Megatouch version from XL R1 '
                      '(1997) to ION 2014: what the software checks, what the key contains, and why '
                      'a given key does or doesn’t boot. Covers the Maxx/XL line, the Force / ION '
                      'line, and the 2007 switch to password-free memory buttons.', 1)
    old_meta = ('<div class="meta"><span>25 DOS builds · 21 Linux builds analysed</span>'
                '<span>23 unique key dumps decrypted</span><span>October 2026</span></div>')
    m = re.search(r'<div class="meta">.*?</div>', s, re.S)
    if m:
        s = s.replace(m.group(0),
                      '<div class="meta"><span>26 DOS builds · 28 Linux builds analysed</span>'
                      '<span>60 key dumps decrypted, every one byte-exact</span>'
                      '<span>33 releases supported by the editor</span>'
                      '<span>October 2026</span></div>', 1)

    # 3. new sections + rewritten Open items, inserted before the existing Open items
    m = re.search(r'\n\s*<section id="open">.*?</section>', s, re.S)
    assert m, 'open-items section not found'
    s = s.replace(m.group(0), '\n' + FORCE_SECTION + GEN4_SECTION + OPEN_ITEMS, 1)

    s = s.replace('</body>', SENTINEL + '\n</body>', 1)
    open(PAGE, 'w', encoding='utf-8').write(s)
    print('megatouch-security-keys.html patched (+2 sections, new TOC, new open items)')


def rebuild_guide():
    """Re-run make-share.py's Markdown renderer over the updated keyinfo-human.md."""
    import subprocess
    import shutil
    import tempfile
    # make-share.py rewrites BOTH pages, and re-wrapping an already-wrapped document gives it
    # a second doctype/head. So render into a scratch directory and copy back only the guide;
    # the research page is patched in place by patch_page() and must not be re-wrapped.
    tmpdir = tempfile.mkdtemp()
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'scripts', 'make-share.py'),
                        PAGE, os.path.join(ROOT, 'keyinfo-human.md'), tmpdir],
                       capture_output=True, text=True)
    built = os.path.join(tmpdir, 'megatouch-keys-guide.html')
    ok = r.returncode == 0 and os.path.exists(built) and os.path.getsize(built) > 10000
    if ok:
        shutil.copyfile(built, GUIDE)
    shutil.rmtree(tmpdir, ignore_errors=True)
    if not ok:
        print('make-share.py failed, guide left untouched:\n' + r.stdout + r.stderr)
        return 1
    print('megatouch-keys-guide.html rebuilt from keyinfo-human.md (%d bytes)'
          % os.path.getsize(GUIDE))
    return 0


if __name__ == '__main__':
    patch_page()
    sys.exit(rebuild_guide())
