"""mtkeylib.py - one model for every Megatouch security key, all four generations.

Wraps the crypto modules into a single editable object:

    k = Key.load('MJADE_full_0900400002B65782')
    k.version, k.container, k.serial, k.gen
    k.fields()            -> [Field(...)]  every named field, decoded
    k.set('country', 1)   -> writes it back into the plaintext
    k.options()           -> [(index, name, state)]
    k.games()             -> [(id, name, enabled, price, continue_cost)]
    k.image()             -> the full container image, re-encrypted for k.serial
    k.save(path)
    k.retarget('4700400002501B82')   -> same contents on another button serial
    Key.new('I2014', serial=...)     -> a blank key of that version

Generations (Docs/01, Docs/18, Docs/19):
  gen 1/2  DS1991, signature in D0[0..7]            (XL R1 .. Double Diamond, Titanium,
                                                     Emerald, Ruby, Force 2002/2003)
  gen 3    DS1991, signature in D0[0x28..0x2F]      (Sapphire, Jade, Crown,
                                                     Force 2004/2005/2006, ION 2006)
  gen 4    DS1995/DS1996, 1024-byte block           (Force 2007-2011, ION 2007-2014,
                                                     Touch2Play 2013, Firefly 2010)
"""
import os, re, json, struct, time, hashlib

import mtkey
import mtkey4
import mtpass

HERE = os.path.dirname(os.path.abspath(__file__))


def _data_dirs():
    # next to this module (scripts/, Run/), or inside a PyInstaller bundle
    import sys
    dirs = [os.path.join(HERE, 'data')]
    if getattr(sys, '_MEIPASS', None):
        dirs.append(os.path.join(sys._MEIPASS, 'data'))
    return dirs


def _load_data(name):
    for d in _data_dirs():
        p = os.path.join(d, name)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                return json.load(f)
    return {}


OPTION_NAMES = _load_data('options.json')
GAME_NAMES = _load_data('games.json')
OPTION_CATALOG = _load_data('option_catalog.json')     # labels, descriptions, menu/key classes (P21)
GAME_TABLES = _load_data('game_tables.json')           # per-version game names (P21)

# ---------------------------------------------------------------- version catalogue

# Gen 1-3: cipher scheme in mtkey.SCHEMES, password scheme in mtpass.SCHEMES,
# signature (hex or None), signature offset within the 232-byte plaintext layout.
# The 232-byte layout is  ID0(8) D0(48) ID1(8) D1(48) ID2(8) D2(48) SCRATCH(64).
D0 = 8
D1 = 8 + 48 + 8
D2 = 8 + 48 + 8 + 48 + 8
SCRATCH = 168

DS1991_VERSIONS = {
    # name                 gen cipher             password     signature            part no.
    'XL R1':              (1, 'M1',              'M1',        '1122334455667788', 'SA3022'),
    'XL Super 5000':      (1, 'M1',              'M1',        '5152535455667788', 'SA3031'),
    'XL 6000':            (1, 'M1',              'M1',        '5052535455667789', 'SA3019'),
    'MAXX 3.06':          (1, 'M1',              'M1',        '5052535455667789', 'SA3028'),
    'XL Gold':            (1, 'XGOLD/M2K',       'XGOLD',     '5052535455667789', 'SA3039'),
    'MAXX 2K':            (1, 'XGOLD/M2K',       'M2K',       '5052535455667789', 'SA3035'),
    'XL Platinum':        (1, 'XPLAT/MDIAMOND',  'XPLAT',     '5052535455667789', 'SA3046'),
    'MAXX Diamond':       (1, 'XPLAT/MDIAMOND',  'MDIAMOND',  '5052535455667789', 'SA3042'),
    'XL Titanium':        (2, 'XTIT/MEMERALD',   'XTIT',      'E84208866740 0282'.replace(' ', ''), 'SA3052'),
    'MAXX Emerald':       (2, 'XTIT/MEMERALD',   'MEMERALD',  'DD62104321100293', 'SA3048'),
    'Force 2002':         (2, 'XTIT/MEMERALD',   'F2002',     'DD62104321100293', 'SA3050'),
    'MAXX Ruby 2':        (2, 'MRUBY',           'MRUBY',     'DE62104321100293', 'SA3056'),
    'Force 2003':         (2, 'MRUBY',           'F2003',     'DE62104321100293', 'SA3059'),
    'MAXX Sapphire':      (3, 'MSAPPHIRE',       'MSAPPHIRE', '1234567890ABCDEF', 'SA3065'),
    'Force 2004':         (3, 'MSAPPHIRE',       'F2004',     '1234567890ABCDEF', 'SA3068'),
    'MAXX Jade':          (3, 'MJADE',           'MJADE',     '8723879FE2432498', 'SA3079'),
    'Force 2005':         (3, 'MJADE',           'F2005',     '8723879FE2432498', 'SA3083'),
    'MAXX Crown':         (3, 'MCROWN',          'MCROWN',    '8723879FE2432498', 'SA3511'),
    'Force 2006':         (3, 'MCROWN',          'FI2006',    '8624879FE2432498', 'SA3501'),
    'ION 2006':           (3, 'MCROWN',          'FI2006',    '342190FA11880410', 'SA3505'),
}

# Where each DS1991 family keeps its option table and its games (P21, from the binaries + NVRAM):
#   dos      options D2[0..0x13] (80 x 2 bit; checked against every DOS NVRAM), games = D1 nibbles
#            for ids 0x00-0x3F (0 = not on the key; Diamond-era value = price per play)
#   ruby     options D2[0..0x13]; games = D1 list of (id, price) pairs and single bytes id|0x80 =
#            disabled, FF-terminated, every unlisted game on at the default price D2[0x22]
#            (Ruby 2 SetGamePriceAndStatusFromKey)
#   sapphire options D2[0x16..0x2B] (88 x 2 bit, Sapphire KeyMgr::ExplodeOptions); price list
#            D1[0..0x11]; game enable bitmap D1[0x12..0x2F]; default price D2[2];
#            territory D2[4]
#   crown    options D2[0..0x13]; price list D1[0..0x1B]; bitmap D2[0x14..0x2F]; default price
#            D1[0x2A], premium price D1[0x1F] (Crown KeyMgr, Docs/04)
LAYOUT = {
    'XL R1': 'dos', 'XL Super 5000': 'dos', 'XL 6000': 'dos', 'MAXX 3.06': 'dos', 'XL Gold': 'dos',
    'MAXX 2K': 'dos', 'XL Platinum': 'dos', 'MAXX Diamond': 'dos', 'XL Titanium': 'dos',
    'MAXX Emerald': 'dos', 'Force 2002': 'dos',
    'MAXX Ruby 2': 'ruby', 'Force 2003': 'ruby',
    'MAXX Sapphire': 'sapphire', 'Force 2004': 'sapphire',
    'MAXX Jade': 'crown', 'Force 2005': 'crown', 'MAXX Crown': 'crown', 'Force 2006': 'crown',
    'ION 2006': 'crown',
}
OPT_BASE = {'dos': 0, 'ruby': 0, 'crown': 0, 'sapphire': 0x16}
OPT_COUNT = {'dos': 80, 'ruby': 80, 'crown': 80, 'sapphire': 88}
PREMIUM_IDS = set(range(0x71, 0x75)) | set(range(0xA3, 0xA9))

# Which build's operator menus each key version's option classes come from. 'how' says whether that
# build is the version's own software ('own'), byte-identical to it ('same binary'), or the nearest
# analysed build ('nearest'). DOS menus were not traced.
OPTION_CLASS_SOURCE = {
    'MAXX 3.06': ('DOS_306', 'own', 'MAXX 3.06 SETUP.DLL'),
    'XL Gold': ('DOS_2K', 'nearest', 'MAXX 2K V4.00 SETUP.DLL'),
    'MAXX 2K': ('DOS_2K', 'own', 'MAXX 2K V4.00 SETUP.DLL'),
    'XL Platinum': ('DOS_PLAT', 'own', 'XL Platinum V1.02 SETUP.DLL'),
    'MAXX Diamond': ('DOS_DIA', 'own', 'MAXX Diamond V6.03 SETUP.DLL'),
    'XL Titanium': ('DOS_TIT', 'own', 'XL Titanium V3.00 SETUP.DLL'),
    'MAXX Emerald': ('DOS_EME', 'own', 'MAXX Emerald V8.04 SETUP.DLL'),
    'Force 2002': ('DOS_EME', 'nearest', 'MAXX Emerald V8.04 SETUP.DLL (same cipher family)'),
    'MAXX Ruby 2': ('ruby2', 'own', 'Ruby 2 V11.00 opsetup.so'),
    'Force 2003': ('ruby2', 'same binary', 'Ruby 2 V11.00 (= Force 2003.5 start)'),
    'MAXX Sapphire': ('sapphire', 'own', 'Sapphire V12.01 opsetup.so'),
    'Force 2004': ('sapphire', 'nearest', 'Sapphire V12.01'),
    'MAXX Jade': ('jade', 'own', 'Jade V14.00 opsetup.so'),
    'Force 2005': ('jade', 'same binary', 'Jade V14.00 (= Force 2005 start)'),
    'MAXX Crown': ('crown', 'own', 'Crown V16.10 opsetup.so'),
    'Force 2006': ('crown', 'nearest', 'Crown V16.10'),
    'ION 2006': ('crown', 'nearest', 'Crown V16.10'),
    'ION 2007': ('I2011', 'nearest', 'ION 2011 opsetup.so'),
    'ION 2008': ('I2011', 'nearest', 'ION 2011 opsetup.so'),
    'ION 2009': ('I2011', 'nearest', 'ION 2011 opsetup.so'),
    'ION 2010': ('I2011', 'nearest', 'ION 2011 opsetup.so'),
    'ION 2011': ('I2011', 'own', 'ION 2011 opsetup.so'),
    'ION 2012': ('I2011', 'nearest', 'ION 2011 opsetup.so'),
    'ION 2013': ('I2014', 'nearest', 'ION 2014 opsetup.so'),
    'ION 2014': ('I2014', 'own', 'ION 2014 opsetup.so'),
    'Force 2007': ('I2011', 'nearest', 'ION 2011 opsetup.so (no Force menus extracted)'),
    'Force 2008': ('I2011', 'nearest', 'ION 2011 opsetup.so (no Force menus extracted)'),
    'Force 2009': ('I2011', 'nearest', 'ION 2011 opsetup.so (no Force menus extracted)'),
    'Force 2010': ('I2011', 'nearest', 'ION 2011 opsetup.so (no Force menus extracted)'),
    'Force 2011': ('I2011', 'nearest', 'ION 2011 opsetup.so (no Force menus extracted)'),
}
OPTION_CLASS_LABEL = {
    'menu': 'Operator menu (opsetup)',
    'key': 'Key only (set by Merit)',
    'runtime': 'Set by the game itself',
    'remote': 'Set by the MegaNet server',
    'unused': 'Not used by this software',
    'unknown': 'Not analysed for this release',
    'untraced': 'Not traced (DOS menus reach most options through a table)',
}

# Laser-serial rules per key version (Docs/05, P21). family: accepted 1-Wire family codes;
# windows: [(family, lo48, hi48)] - the 48-bit serial must fall inside one of them;
# status 'verified' = read from that software, 'inferred' = from a sibling build, 'none' = no check.
_W = 0x0040_0000_0000
SERIAL_RULES = {
    'MAXX Ruby 2': ('verified', 'Ruby 2 V11.00/V11.05 validate_key_range',
                    [(0x82, _W, _W + 0x189C1), (0x02, 0xB00DF9, 0xB013AD), (0x02, 0xB026F9, 0xB032B8)]),
    'Force 2003': ('verified', 'Force 2003.5 start is byte-identical to Ruby 2 V11.00 (v10.09 not checked)',
                   [(0x82, _W, _W + 0x189C1), (0x02, 0xB00DF9, 0xB013AD), (0x02, 0xB026F9, 0xB032B8)]),
    'MAXX Sapphire': ('verified', 'Sapphire V12.01 / Sapphire 2 V13.00', [(0x82, _W + 0x10680, _W + 0x24000)]),
    'Force 2004': ('inferred', 'Force 2004 is a different binary; Sapphire window assumed',
                   [(0x82, _W + 0x10680, _W + 0x24000)]),
    'MAXX Jade': ('verified', 'Jade V14.00/V14.21, Jade 2 V15.10', [(0x82, _W + 0x22917, _W + 0x53FFF)]),
    'Force 2005': ('verified', 'Force 2005 / 2005.5 start are byte-identical to Jade V14.00 / Jade 2',
                   [(0x82, _W + 0x22917, _W + 0x53FFF)]),
    'MAXX Crown': ('verified', 'Crown V16.10', [(0x82, _W + 0x31380, _W + 0x53FFF)]),
    'Force 2006': ('inferred', 'Force 2006 binary not analysed; Crown window assumed',
                   [(0x82, _W + 0x31380, _W + 0x53FFF)]),
    'ION 2006': ('inferred', 'ION 2006 binary not available; Crown window assumed',
                 [(0x82, _W + 0x31380, _W + 0x53FFF)]),
}
GEN4_FAMILIES = {0x0A: ('DS1995', 2048), 0x0C: ('DS1996', 8192), 0x8C: ('DS1996', 8192)}

# Gen 4 signatures observed in the dumps (Docs/19)
GEN4_SIGS = {
    'F2007': '64563647452C2837', 'I2007': '42367123EF235334',
    'F2008': 'E72136AB30C92156', 'I2008': '5621C930AB3621E7',
    'F2009': '6874328C954F6743', 'I2009': '213566732E476A32',
    'F2010': 'CFB4A9611BB72003', 'I2010': '29342DA908FBC6DE',
    'F2011': '90322BBAA4370CFE', 'I2011': None,
    'I2012': None, 'I2013': None, 'I2014': '93E41C6E20911B9B',
}

GEN4_LABEL = {
    'F2007': 'Force 2007', 'F2008': 'Force 2008', 'F2009': 'Force 2009',
    'F2010': 'Force 2010', 'F2011': 'Force 2011',
    'I2007': 'ION 2007', 'I2008': 'ION 2008', 'I2009': 'ION 2009',
    'I2010': 'ION 2010', 'I2011': 'ION 2011', 'I2012': 'ION 2012',
    'I2013': 'ION 2013', 'I2014': 'ION 2014',
}


def all_versions():
    """Every version the tool can read and write, newest-style last."""
    return list(DS1991_VERSIONS) + [GEN4_LABEL[v] for v in GEN4_LABEL]


def gen4_code(label):
    for k, v in GEN4_LABEL.items():
        if v == label:
            return k
    return None


# ---------------------------------------------------------------- fields

class Field:
    """One named, editable field. kind drives the editor the GUI offers."""

    def __init__(self, name, value, kind, offset, size, note=''):
        self.name = name
        self.value = value
        self.kind = kind          # 'str' | 'int' | 'hex' | 'float' | 'date' | 'ro'
        self.offset = offset
        self.size = size
        self.note = note

    def __repr__(self):
        return 'Field(%s=%r, %s @0x%X)' % (self.name, self.value, self.kind, self.offset)


def _s(buf, off, n):
    return bytes(buf[off:off + n]).split(b'\0')[0].decode('latin1', 'replace')


def _put_s(buf, off, n, text):
    raw = text.encode('latin1', 'replace')[:n]
    buf[off:off + n] = raw + b'\0' * (n - len(raw))


# ---------------------------------------------------------------- the key

class Key:
    def __init__(self, gen, version, container, serial, plain, passwords=None,
                 memory=None, path=None):
        self._names = {}
        self.gen = gen
        self.version = version            # a label from all_versions()
        self.container = container        # 'DS1991' | 'DS1995' | 'DS1996'
        self.serial = (serial or '').upper()
        self.plain = bytearray(plain)
        self.passwords = list(passwords) if passwords else None
        self.memory = bytearray(memory) if memory is not None else None
        self.path = path

    # ------------------------------------------------------------ loading

    @staticmethod
    def load(path, serial=None, version=None):
        """version: optional hint, needed only for a key whose part number was edited to
        something outside the factory SA list (the games never check it - Docs/02)."""
        size = os.path.getsize(path)
        if size in (256, 264, 232):
            return Key._load_ds1991(path, serial, version)
        return Key._load_gen4(path, serial, version)

    @staticmethod
    def _load_ds1991(path, serial=None, version=None):
        raw = open(path, 'rb').read()
        if len(raw) == 232:
            # already plaintext; identify by signature
            plain = raw
            ver = Key._ident_plain(plain)
            return Key(DS1991_VERSIONS[ver][0] if ver else 3, ver or 'MAXX Jade',
                       'DS1991', serial or '', plain, path=path)
        img, ser = mtkey.load_full(path, serial)
        if not ser:
            raise ValueError('no 16-hex serial in the file name and none given')
        hits = mtkey.try_all(img, ser)
        if version:
            g, cs, ps, sig, pn = DS1991_VERSIONS[version]
            plain = mtkey.decrypt(img, ser, cs)
            return Key(g, version, 'DS1991', ser, plain,
                       [bytes(img[64 * i + 8:64 * i + 16]) for i in range(3)], img, path)
        if not hits:
            raise ValueError('no cipher scheme decrypts this key')
        stored = [bytes(img[64 * i + 8:64 * i + 16]) for i in range(3)]
        # prefer a version whose password set also matches
        best = None
        for cipher, plain in hits:
            for ver, (g, cs, ps, sig, pn) in DS1991_VERSIONS.items():
                if cs != cipher:
                    continue
                score = 0
                if sig and Key._sig_of(plain, g) == bytes.fromhex(sig):
                    score += 2
                if [bytes(x) for x in mtpass.passwords(ser, ps)] == stored:
                    score += 1
                if best is None or score > best[0]:
                    best = (score, ver, g, plain)
        if best is None:
            cipher, plain = hits[0]
            return Key(3, 'MAXX Jade', 'DS1991', ser, plain, stored, img, path)
        _, ver, g, plain = best
        return Key(g, ver, 'DS1991', ser, plain, stored, img, path)

    @staticmethod
    def _load_gen4(path, serial=None, version=None):
        raw = open(path, 'rb').read()
        if len(raw) == 1024:
            for code in mtkey4.SCHEMES:
                if mtkey4.plausible(raw, code):
                    c = code.rstrip('b')
                    return Key(4, GEN4_LABEL.get(c, c), 'DS1996', serial or '', raw,
                               path=path)
        mem, ser = mtkey4.load(path, serial)
        hint = gen4_code(version) if version else None
        hits = []
        if ser:
            if hint:
                off = mtkey4.SCHEMES[hint][2]
                blk = mem if len(mem) == 1024 else mem[off:off + 1024]
                hits = [(hint, mtkey4.decrypt_block(blk, ser, hint))]
            else:
                hits = mtkey4.try_all(mem, ser) or mtkey4.try_all(mem, ser, strict=False)
        if not hits:
            raise ValueError('no Gen 4 scheme decrypts this key (serial %r). If the part '
                             'number was edited, pass version=' % ser)
        # Force and ION of the same year share a magic and a block offset, so several
        # schemes can decrypt the same block. The 8-byte signature at 0xF5 separates them,
        # and unlike the part number it is actually checked by the game (Docs/19).
        def rank(h):
            c, pl = h
            sig = GEN4_SIGS.get(c.rstrip('b'))
            return 0 if (sig and bytes(pl[0xF5:0xFD]) == bytes.fromhex(sig)) else 1
        hits.sort(key=rank)
        code, plain = hits[0]
        code = code.rstrip('b')          # the I2012 second-magic variant
        container = 'DS1995' if len(mem) == 2048 else 'DS1996'
        return Key(4, GEN4_LABEL.get(code, code), container, ser, plain,
                   memory=mem, path=path)

    @staticmethod
    def _sig_of(plain, gen):
        return bytes(plain[D0 + 0x28:D0 + 0x30]) if gen == 3 else bytes(plain[D0:D0 + 8])

    @staticmethod
    def _ident_plain(plain):
        for ver, (g, cs, ps, sig, pn) in DS1991_VERSIONS.items():
            if sig and Key._sig_of(plain, g) == bytes.fromhex(sig):
                return ver
        return None

    @staticmethod
    def new(version, serial='0000400000000000'):
        """A blank key of the given version, ready to fill in."""
        code = gen4_code(version)
        if code:
            plain = bytearray(1024)
            _put_s(plain, 0, 8, (mtkey4.VALIDATORS[code][0][0] + '01'))
            struct.pack_into('<I', plain, 9, int(time.time()))
            _put_s(plain, 0x0D, 4, 'R00')
            _put_s(plain, 0x16, 10, 'USA-STD')
            _put_s(plain, 0x2A, 200, 'us.accessmerit.com')
            _put_s(plain, 0x35B, 100, 'meritgames.com/us-portal.htm')
            sig = GEN4_SIGS.get(code)
            if sig:
                plain[0xF5:0xFD] = bytes.fromhex(sig)
            # sane US coin defaults
            struct.pack_into('<6f', plain, 0x172, 0.25, 0.25, 0, 0, 0, 1)
            plain[0x192:0x198] = bytes([1, 2, 4, 6, 30, 0])
            struct.pack_into('<6f', plain, 0x198, 0.25, 0.5, 0.75, 1, 5, 0)
            plain[0x170] = 1
            plain[0x171] = 1
            k = Key(4, version, 'DS1995' if code == 'I2007' else 'DS1996',
                    serial, plain, memory=bytearray(2048 if code == 'I2007' else 8192))
            k.fix_checksum()
            return k
        g, cs, ps, sig, pn = DS1991_VERSIONS[version]
        plain = bytearray(232)
        _put_s(plain, 0, 8, pn + '01')
        _put_s(plain, 56, 8, time.strftime('%m/%d/%y'))
        _put_s(plain, 112, 8, 'R00')
        if sig:
            if g == 3:
                plain[D0 + 0x28:D0 + 0x30] = bytes.fromhex(sig)
            else:
                plain[D0:D0 + 8] = bytes.fromhex(sig)
        if g == 3:
            _put_s(plain, D1 + 0x20, 10, 'USA-STD')
        else:
            _put_s(plain, D2 + 0x18, 10, 'USA-STD')
            plain[D0 + 0x28:D0 + 0x2C] = bytes.fromhex('0011007F')
        return Key(g, version, 'DS1991', serial, plain,
                   [bytes(x) for x in mtpass.passwords(serial, ps)])

    # ------------------------------------------------------------ named fields

    def fields(self):
        return self._fields4() if self.gen == 4 else self._fields123()

    def _fields4(self):
        p = self.plain
        f = [
            Field('part number', _s(p, 0, 8), 'str', 0, 8),
            Field('revision', _s(p, 0x0D, 4), 'str', 0x0D, 4),
            Field('programming date', self._date4(), 'date', 9, 4, 'time_t, little endian'),
            Field('territory', _s(p, 0x16, 10), 'str', 0x16, 10),
            Field('country code', p[0xF2], 'int', 0xF2, 1, '0 = USA, 1 = Canada'),
            Field('NJ exception', p[0xF3], 'int', 0xF3, 1),
            Field('lockout value', p[0xF4], 'int', 0xF4, 1),
            Field('region', p[0x3EF], 'int', 0x3EF, 1),
            Field('signature', bytes(p[0xF5:0xFD]).hex().upper(), 'hex', 0xF5, 8),
            Field('checksum', '%04X' % self.stored_checksum(), 'ro', 0x355, 2,
                  'computed %04X' % self.checksum()),
            Field('server URL', _s(p, 0x2A, 200), 'str', 0x2A, 200),
            Field('web portal URL', _s(p, 0x35B, 100), 'str', 0x35B, 100),
            Field('language mask', '%016X' % struct.unpack_from('<Q', p, 0x104)[0], 'hex', 0x104, 8),
            Field('default language mask', '%08X' % struct.unpack_from('<I', p, 0x10C)[0],
                  'hex', 0x10C, 4),
            Field('pricing scheme', p[0x170], 'int', 0x170, 1),
            Field('default currency', p[0x171], 'int', 0x171, 1),
            Field('ChampEd game cost', struct.unpack_from('<H', p, 0xFE)[0], 'int', 0xFE, 2),
            Field('ChampEd prize mode', (struct.unpack_from('<H', p, 0x100)[0] >> 5) & 3,
                  'ro', 0x100, 2),
            Field('ChampEd pool rate', struct.unpack_from('<H', p, 0x102)[0] * 5, 'ro', 0x102, 2),
            Field('unit time 0x2718 (s)', struct.unpack_from('<H', p, 0x357)[0], 'int', 0x357, 2),
            Field('unit time 0x271B (s)', struct.unpack_from('<H', p, 0x359)[0], 'int', 0x359, 2),
        ]
        for i in range(4):
            f.append(Field('currency name %d' % i, _s(p, 0x114 + 23 * i, 23),
                           'str', 0x114 + 23 * i, 23))
        for i in range(6):
            f.append(Field('coin channel %d value' % i,
                           struct.unpack_from('<f', p, 0x172 + 4 * i)[0], 'float',
                           0x172 + 4 * i, 4))
        for i in range(6):
            f.append(Field('channel %d credits' % i, p[0x192 + i], 'int', 0x192 + i, 1))
        for i in range(6):
            f.append(Field('channel %d credit value' % i,
                           struct.unpack_from('<f', p, 0x198 + 4 * i)[0], 'float',
                           0x198 + 4 * i, 4))
        f.append(Field('serial token @0x012', bytes(p[0x12:0x16]).hex().upper(), 'hex', 0x12, 4,
                       'excluded from the checksum'))
        f.append(Field('serial tokens @0x3F0', bytes(p[0x3F0:0x400]).hex().upper(), 'hex',
                       0x3F0, 16, 'never read by the game'))
        return f

    def _date4(self):
        t = struct.unpack_from('<I', self.plain, 9)[0]
        try:
            return time.strftime('%Y-%m-%d', time.gmtime(t))
        except (ValueError, OSError, OverflowError):
            return 'invalid (%u)' % t

    def _fields123(self):
        p = self.plain
        g = self.gen
        f = [
            Field('part number', _s(p, 0, 8), 'str', 0, 8),
            Field('programming date', _s(p, 56, 8), 'str', 56, 8, 'MM/DD/YY'),
            Field('revision', _s(p, 112, 8), 'str', 112, 8),
        ]
        if g == 3:
            sapph = self.layout() == 'sapphire'
            bo, _bm = self._bitmap_pos(0x44)
            f += [Field('signature', bytes(p[D0 + 0x28:D0 + 0x30]).hex().upper(), 'hex',
                        D0 + 0x28, 8)]
            if sapph:
                # Sapphire keeps the territory at D2[4]; its country-code byte was not located
                f += [Field('territory', _s(p, D2 + 4, 10), 'str', D2 + 4, 10),
                      Field('default game price', p[D2 + 2] & 0xF, 'int', D2 + 2, 1,
                            'credits for games not in the price list')]
            else:
                f += [Field('territory', _s(p, D1 + 0x20, 10), 'str', D1 + 0x20, 10),
                      Field('country code', p[D1 + 0x2E], 'int', D1 + 0x2E, 1,
                            '0 USA, 1 Canada, 3/4 UK'),
                      Field('default game price', p[D1 + 0x2A] & 0xF, 'int', D1 + 0x2A, 1,
                            'credits for games not in the price list'),
                      Field('premium game price', p[D1 + 0x1F] & 0xF, 'int', D1 + 0x1F, 1,
                            'games 0x71-0x74, 0xA3-0xA8 not in the list')]
            f += [
                Field('lockout value', p[D0 + 0x27], 'int', D0 + 0x27, 1),
                Field('default language mask',
                      '%08X' % struct.unpack_from('<I', p, D0 + 3)[0], 'hex', D0 + 3, 4),
                Field('platform bit (Force hardware)', bool(p[bo] & 8), 'bool', bo, 1,
                      'the enable bit of game 0x44 (Bowling, Force-only)'),
                Field('TournaMAXX game cost', p[D0 + 1] & 0x1F, 'int', D0 + 1, 1),
                Field('TournaMAXX prize mode', (p[D0 + 1] >> 5) & 3, 'int', D0 + 1, 1),
            ]
            for i in range(6):
                f.append(Field('currency name %d' % i, _s(p, SCRATCH + 8 * i, 8),
                               'str', SCRATCH + 8 * i, 8))
        else:
            f += [
                Field('signature', bytes(p[D0:D0 + 8]).hex().upper(), 'hex', D0, 8),
                Field('territory', _s(p, D2 + 0x18, 10), 'str', D2 + 0x18, 10),
                Field('region/language dword',
                      bytes(p[D0 + 0x28:D0 + 0x2C]).hex().upper(), 'hex', D0 + 0x28, 4,
                      '0011007F USA, 0030008F Canada'),
            ]
            if self.layout() == 'ruby':
                f.append(Field('default game price', p[D2 + 0x22] & 0xF, 'int', D2 + 0x22, 1,
                               'credits for games not in the game list'))
            for i in range(4):
                f.append(Field('coin channel %d' % i,
                               bytes(p[D0 + 8 + 4 * i:D0 + 12 + 4 * i]).hex().upper(),
                               'hex', D0 + 8 + 4 * i, 4))
            for i in range(6):
                f.append(Field('currency name %d' % i, _s(p, SCRATCH + 8 * i, 8),
                               'str', SCRATCH + 8 * i, 8))
        if self.passwords:
            for i, pw in enumerate(self.passwords):
                f.append(Field('subkey %d password' % i, bytes(pw).hex().upper(), 'ro', -1, 8,
                               'regenerated from the serial on save'))
        return f

    def set(self, field, value):
        """Write a Field (or its name) back into the plaintext."""
        if isinstance(field, str):
            field = next(x for x in self.fields() if x.name == field)
        p, o, n = self.plain, field.offset, field.size
        if o < 0 or field.kind == 'ro':
            raise ValueError('%s is read-only' % field.name)
        if field.kind == 'str':
            _put_s(p, o, n, str(value))
        elif field.kind == 'int':
            v = int(str(value), 0)
            if field.name.startswith('TournaMAXX game cost'):
                p[o] = (p[o] & ~0x1F) | (v & 0x1F)
            elif field.name.startswith('TournaMAXX prize mode'):
                p[o] = (p[o] & ~0x60) | ((v & 3) << 5)
            elif n == 1:
                p[o] = v & 0xFF
            else:
                struct.pack_into('<' + {2: 'H', 4: 'I'}[n], p, o, v)
        elif field.kind == 'hex':
            raw = bytes.fromhex(re.sub(r'[^0-9A-Fa-f]', '', str(value)))[:n]
            p[o:o + len(raw)] = raw
        elif field.kind == 'float':
            struct.pack_into('<f', p, o, float(value))
        elif field.kind == 'bool':
            p[o] = (p[o] | 8) if value else (p[o] & ~8)
        elif field.kind == 'date':
            if self.gen == 4:
                t = int(time.mktime(time.strptime(str(value), '%Y-%m-%d')))
                struct.pack_into('<I', p, o, t)
            else:
                _put_s(p, o, n, str(value))
        if self.gen == 4:
            self.fix_checksum()

    # ------------------------------------------------------------ options

    def layout(self):
        """'gen4', or the DS1991 family layout: 'dos' | 'ruby' | 'sapphire' | 'crown' (see LAYOUT)."""
        return 'gen4' if self.gen == 4 else LAYOUT.get(self.version, 'crown')

    def option_count(self):
        # Every generation carries the option table. Gen 1/2 included: D2[0..0x13] matches the
        # operator-option bytes of every DOS NVRAM (locked slots 100%, defaults 89-100%) - P21.
        if self.gen == 4:
            return 120
        return OPT_COUNT[self.layout()]

    def options(self):
        """[(index, label, state)] - state 0 locked off, 1 forced on, 2/3 operator-selectable."""
        return [(i, self.option_label(i), self.option(i)) for i in range(self.option_count())]

    def option_label(self, i):
        e = OPTION_CATALOG.get('slots', {}).get(str(i))
        if not e:
            return 'Slot 0x%02X (no name known)' % i
        if self.layout() == 'crown' and e.get('crown_label'):
            return e['crown_label']
        return e['label']

    def option_info(self, i):
        """Everything known about slot i for this key's software:
        label, desc, source ('merit' help text | 'code'), enum, crown_note, cls, cls_label."""
        e = dict(OPTION_CATALOG.get('slots', {}).get(str(i)) or
                 {'label': 'Slot 0x%02X' % i, 'desc': 'Beyond the 120 named slots.', 'source': 'code',
                  'enum': '', 'crown_note': ''})
        if self.layout() == 'crown' and e.get('crown_label'):
            # Jade/Crown code uses this slot differently from Merit's later (ION-era) name
            e['desc'] = '%s Later ION builds call this slot "%s": %s' % (
                e['crown_note'], e['label'], e['desc'])
            e['label'] = e['crown_label']
            e['crown_note'] = ''
        elif self.layout() != 'crown':
            e['crown_note'] = ''
        src = OPTION_CLASS_SOURCE.get(self.version)
        cls = 'unknown'
        if src:
            cls = OPTION_CATALOG.get('builds', {}).get(src[0], {}).get(str(i), 'unknown')
        e['cls'] = cls
        e['cls_label'] = OPTION_CLASS_LABEL[cls]
        return e

    def option_class_source(self):
        """(build, how, text) the menu/key classification comes from, or None (DOS: not traced)."""
        return OPTION_CLASS_SOURCE.get(self.version)

    def _opt_pos(self, i):
        o = D2 + OPT_BASE[self.layout()] + (i >> 2)
        return o, 6 - 2 * (i & 3)

    def option(self, i):
        if self.gen == 4:
            return self.plain[0x2DD + i]
        o, sh = self._opt_pos(i)
        return (self.plain[o] >> sh) & 3

    def set_option(self, i, state):
        state &= 3
        if self.gen == 4:
            self.plain[0x2DD + i] = state
            self.fix_checksum()
            return
        o, sh = self._opt_pos(i)
        self.plain[o] = (self.plain[o] & ~(3 << sh)) | (state << sh)

    # ------------------------------------------------------------ games

    def game_family(self):
        return 'FORCE' if self.version.startswith('Force') else 'ION'

    def name_tables(self):
        """[(table id, label)] usable for this key: its own software first, then every other."""
        v = GAME_TABLES.get('versions', {}).get(self.version, {})
        own = list(v.get('tables', []))
        g4 = ('ION4', 'FORCE4')
        rest = [t for t in GAME_TABLES.get('tables', {}) if t not in own and
                ((t in g4) == (self.gen == 4))]
        return [(t, GAME_TABLES['tables'][t]['label']) for t in own + rest]

    def name_table(self):
        """The table currently used for names (the version's own unless one was chosen)."""
        if getattr(self, '_table', None):
            return self._table
        v = GAME_TABLES.get('versions', {}).get(self.version, {})
        return (v.get('tables') or [None])[0]

    def names_are_nearest(self):
        """True when the names come from a stand-in build rather than this version's software."""
        v = GAME_TABLES.get('versions', {}).get(self.version, {})
        chosen = getattr(self, '_table', None)
        if chosen and chosen not in v.get('tables', []):
            return True
        return bool(v.get('nearest'))

    def set_name_table(self, table_id):
        self._table = table_id

    def _name_chain(self):
        first = self.name_table()
        v = GAME_TABLES.get('versions', {}).get(self.version, {})
        chain = [first] + [t for t in v.get('tables', []) if t != first]
        return [t for t in chain if t in GAME_TABLES.get('tables', {})]

    def game_name(self, gid):
        if self._names and gid in self._names:
            return self._names[gid]
        for t in self._name_chain():
            n = GAME_TABLES['tables'][t]['names'].get(str(gid))
            if n:
                return n
        if self.gen == 4:
            e = GAME_NAMES.get(self.game_family(), {}).get(str(gid))
            if e:
                return e['desc'] or e['tag']
        return 'game 0x%02X' % gid

    def game_flags(self, gid):
        for t in self._name_chain():
            tab = GAME_TABLES['tables'][t]
            if str(gid) in tab['names']:
                return tab.get('flags', {}).get(str(gid), [])
        return []

    def load_game_names(self, mapping):
        """mapping: {id: name}, e.g. from scripts/gamedata.py for a specific build."""
        self._names = dict(mapping)

    def table_size(self):
        t = self.name_table()
        return len(GAME_TABLES['tables'][t]['names']) if t else 0

    def game_count(self):
        lay = self.layout()
        if lay == 'gen4':
            return 300
        cap = {'dos': 64, 'ruby': 0x80, 'sapphire': 240, 'crown': 224}[lay]
        n = self.table_size()
        return min(cap, n) if n else cap

    def games(self):
        """[(id, name, enabled, price, continue_cost)]; price None = no price known."""
        out = []
        for g in range(self.game_count()):
            en, pr, cc = self.game(g)
            out.append((g, self.game_name(g), en, pr, cc))
        return out

    # -- Gen 3 price list: bytes >= 0xF0 set the running price, other bytes are game ids, FF ends
    def _plist_area(self):
        return {'crown': 0x1C, 'sapphire': 0x12}[self.layout()]

    def _plist(self):
        p, n = self.plain, self._plist_area()
        if self.layout() == 'sapphire' and p[D1] == 0:
            # Sapphire's alternative form: (id, price) pairs, FF FF ends (GetGamePriceFromKey)
            out = {}
            for i in range(0, n - 1, 2):
                a, b = p[D1 + i], p[D1 + i + 1]
                if a == 0xFF and b == 0xFF:
                    break
                out[a] = b & 0xF
            return out
        out, price = {}, None
        for i in range(n):
            x = p[D1 + i]
            if x == 0xFF:
                break
            if x >= 0xF0:
                price = x & 0xF
            elif price is not None:
                out[x] = price
        return out

    def _set_plist(self, prices):
        n = self._plist_area()
        body = bytearray()
        for pr in sorted(set(prices.values())):
            body.append(0xF0 | pr)
            body += bytes(sorted(g for g, v in prices.items() if v == pr))
        if len(body) > n:
            raise ValueError("the key's price list holds %d bytes; these prices need %d. Use "
                             "fewer games at a non-default price." % (n, len(body)))
        self.plain[D1:D1 + n] = bytes(body) + b'\xff' * (n - len(body))

    def default_price(self, gid=None):
        """The price unlisted games get, or None where the key's default is not known."""
        lay = self.layout()
        if lay == 'crown':
            if gid is not None and gid in PREMIUM_IDS:
                return self.plain[D1 + 0x1F] & 0xF
            return self.plain[D1 + 0x2A] & 0xF
        if lay == 'ruby':
            return self.plain[D2 + 0x22] & 0xF
        if lay == 'sapphire':
            return self.plain[D2 + 2] & 0xF      # GetGamePriceFromKey: DallasKeyP3+0x12
        return None

    # -- Ruby list: (id, price) pairs; a single byte id|0x80 = game disabled; FF ends; 0x30 bytes
    def _ruby_list(self):
        p, i, out = self.plain, 0, {}
        while i <= 0x2F:
            x = p[D1 + i]
            if x == 0xFF:
                break
            if x & 0x80:
                out[x & 0x7F] = None
                i += 1
            else:
                out[x] = (p[D1 + i + 1] & 0xF) if i + 1 < 48 else 0
                i += 2
        return out

    def _set_ruby_list(self, entries):
        body = bytearray()
        for g in sorted(entries):
            v = entries[g]
            body += bytes([g | 0x80]) if v is None else bytes([g, v & 0xF])
        if len(body) + 1 > 0x30:
            raise ValueError('the Ruby game list holds 0x30 bytes; this needs %d' % (len(body) + 1))
        self.plain[D1:D1 + 0x30] = bytes(body) + b'\xff' + b'\x00' * (0x2F - len(body))

    def _bitmap_pos(self, gid):
        base = D1 + 0x12 if self.layout() == 'sapphire' else D2 + 0x14
        return base + gid // 8, 0x80 >> (gid % 8)

    def game(self, gid):
        """(enabled, price, continue_cost). price None = no default price known for this layout."""
        lay = self.layout()
        if lay == 'gen4':
            b = self.plain[0x1B0 + gid]
            if self._code4() in ('F2007', 'I2007'):
                # 2007 keys end before the bitmap: a game is on when it has a price (Docs/19)
                return b != 0, b & 0xF, b >> 4
            bit = bool(self.plain[0x3BF + gid // 8] & (0x80 >> (gid % 8)))
            return bit, b & 0xF, b >> 4
        if lay in ('crown', 'sapphire'):
            o, m = self._bitmap_pos(gid)
            pr = self._plist().get(gid)
            return bool(self.plain[o] & m), (pr if pr is not None else self.default_price(gid)), 0
        if lay == 'ruby':
            e = self._ruby_list()
            if gid in e and e[gid] is None:
                return False, self.default_price(), 0
            return True, e.get(gid, self.default_price()), 0
        nib = self.plain[D1 + (gid >> 1)]
        v = (nib >> 4) if gid % 2 == 0 else (nib & 0xF)
        return v != 0, v, 0

    def set_game(self, gid, enabled=None, price=None, continue_cost=None):
        lay = self.layout()
        if lay == 'gen4' and self._code4() in ('F2007', 'I2007'):
            cur = self.plain[0x1B0 + gid]
            pr = cur & 0xF if price is None else price & 0xF
            cc = cur >> 4 if continue_cost is None else continue_cost & 0xF
            if enabled is False:
                pr, cc = 0, 0
            elif enabled and pr == 0:
                pr = 1
            self.plain[0x1B0 + gid] = (cc << 4) | pr
            self.fix_checksum()
            return
        if lay == 'gen4':
            if enabled is not None:
                o = 0x3BF + gid // 8
                m = 0x80 >> (gid % 8)
                self.plain[o] = (self.plain[o] | m) if enabled else (self.plain[o] & ~m)
            if price is not None or continue_cost is not None:
                b = self.plain[0x1B0 + gid]
                if price is not None:
                    b = (b & 0xF0) | (price & 0xF)
                if continue_cost is not None:
                    b = (b & 0x0F) | ((continue_cost & 0xF) << 4)
                self.plain[0x1B0 + gid] = b
            self.fix_checksum()
            return
        if lay in ('crown', 'sapphire'):
            if price is not None:
                pl = self._plist()
                dflt = self.default_price(gid)
                if dflt is not None and (price & 0xF) == dflt:
                    pl.pop(gid, None)
                else:
                    pl[gid] = price & 0xF
                self._set_plist(pl)
            if enabled is not None:
                o, m = self._bitmap_pos(gid)
                self.plain[o] = (self.plain[o] | m) if enabled else (self.plain[o] & ~m)
            return
        if lay == 'ruby':
            e = self._ruby_list()
            on, cur, _ = self.game(gid)
            on = on if enabled is None else enabled
            pr = cur if price is None else price & 0xF
            if not on:
                e[gid] = None
            elif pr == self.default_price():
                e.pop(gid, None)
            else:
                e[gid] = pr
            self._set_ruby_list(e)
            return
        # dos: one nibble per game, 0 = not on the key
        o = D1 + (gid >> 1)
        cur = self.game(gid)[1]
        if enabled is False:
            v = 0
        elif price is not None:
            v = price & 0xF
        elif enabled and cur == 0:
            v = 1
        else:
            v = cur
        if gid % 2 == 0:
            self.plain[o] = (self.plain[o] & 0x0F) | (v << 4)
        else:
            self.plain[o] = (self.plain[o] & 0xF0) | v

    # ------------------------------------------------------------ checksum / crypto

    def _code4(self):
        return gen4_code(self.version)

    def checksum(self):
        return mtkey4.checksum(bytes(self.plain), self._code4()) if self.gen == 4 else None

    def stored_checksum(self):
        return mtkey4.stored_checksum(bytes(self.plain), self._code4()) if self.gen == 4 else None

    def fix_checksum(self):
        if self.gen == 4:
            self.plain = bytearray(mtkey4.fix_checksum(bytes(self.plain), self._code4()))

    def checksum_ok(self):
        if self.gen != 4:
            return None
        return self.checksum() == self.stored_checksum()

    def has_serial(self):
        return len(self.serial or '') == 16

    def image(self):
        """The full container image, re-encrypted for self.serial."""
        if not self.has_serial():
            raise ValueError('no button serial set - the cipher (and, below Gen 4, the '
                             'subkey passwords) are derived from it. Use "Change button '
                             'serial" first, or save the decrypted plaintext instead.')
        if self.gen == 4:
            code = self._code4()
            blk = mtkey4.encrypt_block(bytes(self.plain), self.serial, code)
            size = mtkey4.SCHEMES[code][5]
            mem = bytearray(self.memory if self.memory and len(self.memory) == size
                            else bytes(size))
            off = mtkey4.SCHEMES[code][2]
            mem[off:off + 1024] = blk
            return bytes(mem)
        g, cs, ps, sig, pn = DS1991_VERSIONS[self.version]
        pw = tuple(bytes(x) for x in mtpass.passwords(self.serial, ps))
        self.passwords = list(pw)
        return mtkey.encrypt(bytes(self.plain), self.serial, cs, pw)

    def save(self, path, with_serial=True, plaintext=False):
        data = bytes(self.plain) if plaintext else self.image()
        if with_serial and not plaintext:
            data += bytes.fromhex(self.serial)
        with open(path, 'wb') as f:
            f.write(data)
        return hashlib.sha256(data).hexdigest()

    def retarget(self, new_serial):
        """Same contents on a different button serial (re-keys the cipher and passwords)."""
        k = Key(self.gen, self.version, self.container, new_serial.upper(),
                bytes(self.plain), memory=None)
        if self.gen == 4:
            k.memory = bytearray(mtkey4.SCHEMES[k._code4()][5])
        return k

    def verify_roundtrip(self):
        """Re-encrypt then decrypt and confirm the plaintext is unchanged.
        Returns None when there is no serial to encrypt against."""
        if not self.has_serial():
            return None
        img = self.image()
        if self.gen == 4:
            code = self._code4()
            off = mtkey4.SCHEMES[code][2]
            back = mtkey4.decrypt_block(img[off:off + 1024], self.serial, code)
        else:
            g, cs, ps, sig, pn = DS1991_VERSIONS[self.version]
            back = mtkey.decrypt(img, self.serial, cs)
        return bytes(back) == bytes(self.plain)

    def serial_report(self):
        """check_serial() for this key's own version and serial."""
        return check_serial(self.version, self.serial)

    def summary(self):
        bits = ['%s  (gen %d, %s)' % (self.version, self.gen, self.container),
                'serial %s' % (self.serial if self.has_serial() else 'NOT SET')]
        if self.gen == 4:
            bits.append('checksum %s' % ('OK' if self.checksum_ok() else 'MISMATCH'))
        return '   '.join(bits)


def crc8(data):
    """Dallas 1-Wire CRC-8, for building a valid ROM id."""
    c = 0
    for b in data:
        for _ in range(8):
            mix = (c ^ b) & 1
            c >>= 1
            if mix:
                c ^= 0x8C
            b >>= 1
    return c


def make_serial(family, serial48):
    """Print-order serial string (CRC first .. family last) from a family + 48-bit serial."""
    rom = bytes([family]) + int(serial48).to_bytes(6, 'little')
    return (rom + bytes([crc8(rom)]))[::-1].hex().upper()


def parse_serial(serial):
    """Print-order serial string -> (family, serial48, crc). Raises ValueError if not 16 hex."""
    s = re.sub(r'[^0-9A-Fa-f]', '', serial or '')
    if len(s) != 16:
        raise ValueError('a button serial is 16 hex digits (printed order, CRC first .. family last)')
    rom = bytes.fromhex(s)[::-1]          # family, s1..s6, crc
    return rom[0], int.from_bytes(rom[1:7], 'little'), rom[7]


def fix_crc(serial):
    """Same family + serial with the correct 1-Wire CRC."""
    fam, s48, _ = parse_serial(serial)
    return make_serial(fam, s48)


def check_serial(version, serial):
    """Would this release accept a button with this serial? -> [(level, message)],
    level 'ok' | 'warn' | 'error'. Checks the 1-Wire CRC, the family code and the laser-serial
    window the software enforces (Docs/05; Force/ION builds P21; Gen 4 has no window, Docs/19)."""
    out = []
    try:
        fam, s48, crc = parse_serial(serial)
    except ValueError as e:
        return [('error', str(e))]
    good = crc8(bytes([fam]) + s48.to_bytes(6, 'little'))
    if crc != good:
        out.append(('warn', 'CRC byte is %02X but a real button with this family and serial has %02X '
                            '(%s). Emulators may not care; a 1-Wire reader rejects it.'
                    % (crc, good, make_serial(fam, s48))))
    else:
        out.append(('ok', '1-Wire CRC is correct.'))
    code = gen4_code(version)
    if code:
        if fam not in GEN4_FAMILIES:
            out.append(('error', 'Family %02X is not a DS1995 (0A) or DS1996 (0C/8C). %s reads anything '
                                 'else as an old DS1991 key, so this key would not be found.'
                        % (fam, version)))
        else:
            part, size = GEN4_FAMILIES[fam]
            need = mtkey4.SCHEMES[code][2] + 1024
            if need > size:
                out.append(('error', '%s keeps its block at offset %d, which needs %d bytes; a %s '
                                     '(family %02X) only has %d.' % (version, need - 1024, need, part,
                                                                      fam, size)))
            else:
                out.append(('ok', 'Family %02X (%s) holds the %s block.' % (fam, part, version)))
        out.append(('ok', 'The 2007+ software has no laser-serial window (Docs/19).'))
        return out
    rule = SERIAL_RULES.get(version)
    if fam not in (0x02, 0x82):
        out.append(('error' if rule else 'warn',
                    'Family %02X is not a DS1991 (02) or DS1425 (82) MultiKey.' % fam))
    if not rule:
        out.append(('ok', '%s does not check the laser serial (no window in the DOS software).'
                    % version))
        return out
    status, why, windows = rule
    fams = sorted({w[0] for w in windows})
    hit = any(fam == f and lo <= s48 <= hi for f, lo, hi in windows)
    desc = '; '.join('family %02X %04X_%08X-%04X_%08X' % (f, lo >> 32, lo & 0xFFFFFFFF, hi >> 32,
                                                          hi & 0xFFFFFFFF) for f, lo, hi in windows)
    if hit:
        out.append(('ok' if status == 'verified' else 'warn',
                    'Serial %04X_%08X is inside the window %s %s (%s).'
                    % (s48 >> 32, s48 & 0xFFFFFFFF, version,
                       'checks' if status == 'verified' else 'probably checks', why)))
    else:
        msg = ('%s shuts down at boot ("KEY RANGE MISMATCH") unless the button is %s. '
               'This one is family %02X, serial %04X_%08X.'
               % (version, desc, fam, s48 >> 32, s48 & 0xFFFFFFFF))
        if fam not in fams:
            msg += ' The family is wrong as well.'
        if status != 'verified':
            msg += ' (Window inferred: %s.)' % why
        out.append(('error' if status == 'verified' else 'warn', msg))
    return out


def suggest_serial(version, rng=None):
    """A made-up serial this release would accept (right family, inside its window, valid CRC).
    For emulators / 1-Wire emulators only - it is not a real Merit button."""
    import random
    rng = rng or random.Random()
    code = gen4_code(version)
    if code:
        fam = 0x0A if code == 'I2007' else 0x0C
        return make_serial(fam, _W + rng.randint(0x10000, 0x7FFFF))
    rule = SERIAL_RULES.get(version)
    if rule:
        fam, lo, hi = rule[2][0]
        return make_serial(fam, rng.randint(lo, hi))
    return make_serial(0x02, rng.randint(0x800000, 0xFFFFFF))


def recover_gen4_serial(block1024):
    """For a Gen 4 XOR-mode block with no known serial: recover the cipher key from the
    'SAnnnn' prefix, invert it to the button's inner six serial bytes, and identify the
    version. Returns [(version_label, print_order_serial, decrypted)]. See Docs/18.
    """
    out = []
    for code in mtkey4.SCHEMES:
        mode, magic, _off, _nc, _um, _sz = mtkey4.SCHEMES[code]
        if mode != 'xor':
            continue
        magic = bytes.fromhex(magic)
        for sa in mtkey4.VALIDATORS[code][0]:
            kk = [block1024[i] ^ sa.encode()[i] for i in range(6)]
            ser = [0] * 8
            for i in range(6):
                ser[6 - i] = (magic[5 - i] ^ kk[i]) & 0xFF
            s = bytes(ser).hex().upper()
            dec = mtkey4.decrypt_block(block1024, s, code)
            if mtkey4.plausible(dec, code):
                c = code.rstrip('b')
                out.append((GEN4_LABEL.get(c, c), s, dec))
    return out
