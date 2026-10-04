"""test-mtkeytool.py - regression test for mtkeylib / mtkeytool over the whole key corpus.

Every check asserts; a failure is a non-zero exit. Written after a smoke test "passed"
while an open had silently failed and left the previous key on screen - so every open is
checked by its return value and by the version it actually produced.

    python test-mtkeytool.py            # model only (no GUI, no display needed)
    python test-mtkeytool.py --gui      # also drive the Tk app headlessly
"""
import os
import sys
import glob
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkeylib as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = [os.path.join(ROOT, 'Key Info & Dumps'), r'F:\TouchPPBox Folder\keys']
SIZES = (232, 256, 264, 1024, 1032, 2048, 2056, 8192, 8200)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def corpus():
    seen = set()
    for root in CORPUS:
        if not os.path.isdir(root):
            continue
        for dp, _, fs in os.walk(root):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                try:
                    if os.path.getsize(p) not in SIZES:
                        continue
                except OSError:
                    continue
                # Tommy's ION 2014 pair is a documented damaged/emulated dump: key_out has a
                # one-bit error at offset 18 and laser_out is an 8-byte ROM, not a key
                # (Docs/18). They are expected not to load.
                if f in ('key_out', 'laser_out'):
                    continue
                if f in seen or f.endswith(('.md', '.txt', '.json')):
                    continue
                seen.add(f)
                yield p


def test_corpus():
    n = ok = 0
    for p in corpus():
        n += 1
        name = os.path.basename(p)
        ser = '0000400003994F00' if 'FORCE 2011' in name else None
        try:
            k = L.Key.load(p, ser)
        except Exception as e:
            fails.append('load %s: %s' % (name, e))
            continue
        ok += 1
        rt = k.verify_roundtrip()
        if rt is None:
            check(not k.has_serial(), 'no-serial key reported correctly %s' % name)
        else:
            check(rt, 'round-trip %s' % name)
        if k.gen == 4:
            check(k.checksum_ok(), 'checksum %s' % name)
        check(len(k.fields()) > 8, 'fields %s' % name)
        check(len(k.options()) == k.option_count(), 'option count %s' % name)
        check(len(k.games()) == k.game_count(), 'game count %s' % name)
    print('corpus: %d files, %d loaded' % (n, ok))
    if n == 0:
        # Run/ is meant to be copyable to a machine that has no key collection; the corpus
        # tests are a bonus there, not a requirement.
        print('  (no key collection found next to this copy - corpus tests skipped)')
        return
    check(ok >= 40, 'expected at least 40 loadable dumps, got %d' % ok)


def test_edit_cycle():
    tmp = tempfile.mkdtemp()
    samples = [p for p in corpus()
               if os.path.basename(p).startswith(('MJADE_full', 'I2009_full', 'F2007_full',
                                                  'M2K_full', 'MCROWN_full'))]
    if not samples:
        print('edit cycle: no key collection, skipped')
        return
    check(len(samples) >= 4, 'edit-cycle samples found: %d' % len(samples))
    for p in samples:
        k = L.Key.load(p)
        before = k.version
        k.set('part number', 'SA999988')
        if k.option_count():
            k.set_option(0x14, 1)
        k.set_game(0x20, enabled=True, price=5)
        out = os.path.join(tmp, os.path.basename(p) + '.edited')
        k.save(out)
        k2 = L.Key.load(out)
        check(k2.version == before, 'version kept after edit: %s -> %s' % (before, k2.version))
        check(bytes(k2.plain) == bytes(k.plain), 'plaintext survives save/reload %s' % before)
        check(k2.game(0x20)[0] and k2.game(0x20)[1] == 5, 'game edit persisted %s' % before)
        if k2.option_count():
            check(k2.option(0x14) == 1, 'option edit persisted %s' % before)
        if k2.gen == 4:
            check(k2.checksum_ok(), 'checksum after edit %s' % before)
    print('edit cycle: %d keys' % len(samples))


def test_generate():
    for v in L.all_versions():
        fam = 0x8C if (v.startswith(('ION 20', 'Force 20')) and v[-4:] >= '2007') else 0x82
        k = L.Key.new(v, L.make_serial(fam, 0x00400003_1380))
        check(k.verify_roundtrip(), 'generated %s round-trip' % v)
        if k.gen == 4:
            check(k.checksum_ok(), 'generated %s checksum' % v)
    print('generate: %d releases' % len(L.all_versions()))


def test_retarget():
    p = next((x for x in corpus() if os.path.basename(x).startswith('MJADE_full')), None)
    if p is None:
        print('retarget: no key collection, skipped')
        return
    k = L.Key.load(p)
    new = L.make_serial(0x82, 0x00400004_CA02)
    k2 = k.retarget(new)
    check(bytes(k2.plain) == bytes(k.plain), 'retarget preserves plaintext')
    check(k2.verify_roundtrip(), 'retarget round-trip')
    check(k2.image() != k.image(), 'retarget actually changes the ciphertext')
    print('retarget: ok')


def test_serial_recovery():
    p = os.path.join(ROOT, 'Key Info & Dumps', 'Force - ION', 'Force 2011', 'FORCE 2011.bin')
    if not os.path.isfile(p):
        print('serial recovery: sample missing, skipped')
        return
    hits = L.recover_gen4_serial(open(p, 'rb').read())
    check(bool(hits), 'serial recovered from FORCE 2011.bin')
    if hits:
        ver, ser, dec = hits[0]
        check(ver == 'Force 2011', 'recovered version %s' % ver)
        check(ser[2:14] == '004000039 94F'.replace(' ', ''), 'recovered serial %s' % ser)
    print('serial recovery: ok')


def _by_version():
    out = {}
    for p in corpus():
        try:
            k = L.Key.load(p)
        except Exception:
            continue
        out.setdefault(k.version, []).append((os.path.basename(p), k))
    return out


def test_layouts_and_names():
    """P21: every DS1991 generation has the 80/88-slot option table; games decode per family and
    every enabled game of a release with its own game table has a name."""
    kv = _by_version()
    if not kv:
        print('layouts: no key collection, skipped')
        return
    for v, ks in kv.items():
        for name, k in ks:
            check(k.option_count() == (88 if k.layout() == 'sapphire' else 80 if k.gen < 4 else 120),
                  'option count %s %s' % (v, name))
            on = [g for g in k.games() if g[2]]
            named = [g for g in on if not g[1].startswith('game 0x')]
            if k.gen < 4:
                check(len(named) == len(on), 'all enabled games named %s %s (%d/%d)'
                      % (v, name, len(named), len(on)))
            else:
                check(len(named) >= 0.97 * len(on), 'gen4 names %s %s (%d/%d)' % (v, name, len(named), len(on)))
    crown = [k for n, k in kv.get('MAXX Crown', []) if n.startswith('MCROWN_full_FF00')]
    if crown:
        k = crown[0]
        on = [g for g in k.games() if g[2]]
        check(len(on) == 101, 'Crown USA enables 101 games, got %d' % len(on))
        check(sum(1 for g in on if g[3] == 2) == 13, 'Crown USA: 13 enabled games at price 2')
        before = bytes(k.plain)
        k.set_game(0x05, price=3)
        check(k.game(0x05)[1] == 3, 'Crown price edit takes effect')
        k.set_game(0x05, price=k.default_price(0x05))
        check(bytes(k.plain) == before, 'Crown price list restored byte-exact')
        classes = [k.option_info(i)['cls'] for i in range(80)]
        check(classes.count('menu') == 53 and classes.count('key') == 10,
              'Crown options: 53 menu / 10 key-only (Docs/04), got %d / %d'
              % (classes.count('menu'), classes.count('key')))
        check(k.option_info(0x14)['cls'] == 'key', 'TournaMAXX is key-only on Crown')
    for v, ks in kv.items():
        if v in ('ION 2007', 'Force 2007'):
            for n, k in ks:
                check(sum(1 for g in k.games() if g[2]) > 100, '2007 keys: games on by price %s' % n)
    emer = [k for n, k in kv.get('MAXX Emerald', []) if n.startswith('MEMERALD_full_6C')]
    if emer:
        check(not emer[0].game(0x22)[0] and not emer[0].game(0x24)[0],
              'Emerald key: H2H games 0x22/0x24 off (matches NVRAM)')
    print('layouts and names: %d releases' % len(kv))


def test_serial_rules():
    c = lambda v, s: [lvl for lvl, _ in L.check_serial(v, s)]
    check('error' not in c('MAXX Crown', 'FF004000036F1F82'), 'Crown USA serial accepted by Crown')
    check('error' in c('MAXX Crown', '6D000000CB053702'), 'CAN-VER2 DS1991 rejected by Crown')
    check('error' in c('MAXX Crown', '0900400002B65782'), 'old Jade lot rejected by Crown')
    check('error' not in c('MAXX Jade', '0900400002B65782'), 'Jade lot accepted by Jade')
    check('error' not in c('MAXX Diamond', '4C000000937D1702'), 'DOS: no window')
    check('error' in c('MAXX Ruby 2', 'FB22334455667702'), 'synthetic Ruby serial rejected')
    check('warn' in c('MAXX Jade', '0000400002B65782'), 'bad CRC reported')
    check(L.fix_crc('0000400002B65782') == '0900400002B65782', 'fix_crc')
    for v in L.all_versions():
        s = L.suggest_serial(v)
        check('error' not in c(v, s), 'suggested serial accepted by %s (%s)' % (v, s))
        k = L.Key.new(v, s)
        check(k.verify_roundtrip(), 'generated %s on its suggested serial' % v)
    print('serial rules: ok')


def test_gui():
    import mtkeytool as T
    app = T.App()
    app.withdraw()
    shown = []
    T.messagebox.showerror = lambda t, m, **k: shown.append(m)
    good = next((x for x in corpus() if os.path.basename(x).startswith('MCROWN_full')), None)
    if good is None:
        app.key = L.Key.new('ION 2014', L.make_serial(0x8C, 0x00400003_1380))
        app.refresh_all()
    else:
        check(app.open_path(good) is True, 'GUI opens a real key')
        check(app.key is not None and app.key.version == 'MAXX Crown', 'GUI identified Crown')
    before = app.key.version
    bogus = os.path.join(ROOT, 'Key Info & Dumps', 'nope', 'does_not_exist')
    check(app.open_path(bogus) is False, 'GUI reports a missing file')
    check(bool(shown), 'GUI raised an error dialog for the missing file')
    check(app.key.version == before, 'GUI kept the previous key after a failed open')
    check(len(app.tv_fields.get_children()) > 8, 'GUI populated the field view')
    check(len(app.tv_games.get_children()) > 0, 'GUI populated the game view')
    groups = app.tv_opts.get_children()
    check(any(g == 'grp-menu' for g in groups) and any(g == 'grp-key' for g in groups),
          'GUI options split into operator-menu and key-only groups: %s' % (groups,))
    n_opts = sum(len(app.tv_opts.get_children(g)) for g in groups)
    check(n_opts == app.key.option_count(), 'GUI lists every option slot (%d)' % n_opts)
    desc = app.tv_opts.item(app.tv_opts.get_children('grp-key')[0], 'values')[3]
    check(len(desc) > 10 and '_inx' not in desc, 'GUI option description is prose: %r' % desc)
    check(bool(app.cb_table.cget('values')), 'GUI offers game-name tables')
    names = [app.tv_games.item(i, 'values')[1] for i in app.tv_games.get_children()]
    check(sum(1 for x in names if x.startswith('game 0x')) == 0, 'GUI game names all resolved')
    app.tv_opts.selection_set(app.tv_opts.get_children('grp-key')[0])
    app.show_option_detail()
    check('[' in app.opt_detail.get('1.0', 'end'), 'GUI option detail pane filled')
    app.destroy()
    print('gui: ok')


if __name__ == '__main__':
    test_corpus()
    test_edit_cycle()
    test_generate()
    test_retarget()
    test_serial_recovery()
    test_layouts_and_names()
    test_serial_rules()
    if '--gui' in sys.argv:
        test_gui()
    if fails:
        print('\nFAILURES (%d):' % len(fails))
        for f in fails:
            print('  -', f)
        sys.exit(1)
    print('\nall checks passed')
