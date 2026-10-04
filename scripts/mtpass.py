"""mtpass.py - DS1991 subkey password generation for every Megatouch release.

Port of keyflasher's *PasswordGenerator classes (plus MCROWN, which keyflasher lacks and
which P17 recovered from the Crown binaries). A DS1991 subkey only answers with real data
when read with the right 8-byte password, so these are needed to write a physical key --
the cipher in mtkey.py is a separate layer applied to the data itself.

Shape, for all schemes:
    key   = ROM bytes in ROM order (key[0] = family, key[1..6] = serial, key[7] = CRC)
    m     = magic(key)                 4 bytes derived from the ROM (same formula as laserMath)
    pass  = initPasswords(key)         3 x 8 bytes, fixed constants or ROM-derived
    then each password is run through merit_encrypt with seed blkVCode[s]:
            p[i] ^= m[i%4]; p[i] += seed; seed += inc

usage: mtpass.py <full_264_dump> [...]      -> checks generated vs. stored passwords
       mtpass.py --table <serial>           -> prints all schemes' passwords for a serial
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey

B = 0xFF


def _emerald_init(key):
    return [[0x20, 0x3A, 0x42, 0x18, 0xFE, 0xCE, 0x99, 0x10],
            [0x31, 0x09, 0x4F, 0x21, 0xAA, 0x55, 0x91, 0x22],
            [0x33, 0x19, 0x54, 0xAF, 0xFA, 0x55, 0xAA, 0x16]]


def _emerald_xor_init(key):
    """Emerald constants XOR'd with 0x02/0x31/0x10 - used by Ruby, Force 2002 and Force 2003."""
    p = _emerald_init(key)
    for x, c in zip(p, (0x02, 0x31, 0x10)):
        for i in range(8):
            x[i] ^= c
    return p


def _rom_init(key, consts, mode):
    """ROM-derived init: three copies of the ROM with byte 0 forced to 0/1/2, then mixed."""
    p = [list(key), list(key), list(key)]
    p[1][0], p[2][0] = 1, 2
    for s in range(3):
        for i in range(7):
            if mode == 'add_div':                     # Jade / Crown
                t = i + key[i] + consts[s]
                p[s][i] = (t + t // 0xFF) ^ p[s][i]
            elif mode == 'mod':                       # Force / Ion 2006
                t = i + key[i] + consts[s]
                p[s][i] ^= (t % 0xFF) & B
            elif mode == 'sapphire':
                k7 = key[7]
                v = (k7 % 0x7,
                     k7 + (((((k7 * 0x8 - k7) * 8 + k7) >> 8) >> 2) * -0x12),
                     k7 & 0x1F)[s]
                p[s][i] ^= v
            elif mode == 'f04':
                k7 = key[7]
                v = (k7 & 0xF,
                     k7 + (((((k7 * 0x20 - k7) * 8 + k7) >> 8) >> 5) * -0x21),
                     k7 + ((((k7 * 0x1B) >> 8) >> 1) * -0x11) - (((k7 * 0x1B) >> 8) & 0xFE))[s]
                p[s][i] ^= v
            elif mode == 'f05':
                t = i + key[i] + (0x03, 0x11, 0x99)[s]
                p[s][i] = (t + t // 0xFF) ^ p[s][i]
    return p


# scheme: (magic_fn, init_fn, blkVCode, inc)
SCHEMES = {
    'M1':             (mtkey._lm_zero,  lambda k: [[0xCC, 0xE3, 0xAA, 0xF0, 0x0F, 0x3C, 0xAE, 0xCE]] * 3,
                       [0, 0, 0, 0], 0x00),
    'XGOLD':          (mtkey._lm_m2k,   lambda k: [[0xAA, 0x34, 0x76, 0xE1, 0x99, 0x00, 0x44, 0x54],
                                                   [0x66, 0x87, 0x11, 0x66, 0x23, 0xCB, 0xBC, 0x07],
                                                   [0x22, 0x41, 0x65, 0xAF, 0xD3, 0xFF, 0x76, 0x20]],
                       [0x55, 0x54, 0x53, 0x52], 0x31),
    'M2K':            (mtkey._lm_m2k,   lambda k: [[0x36, 0x87, 0x34, 0x12, 0x35, 0x89, 0x32, 0xCF],
                                                   [0x73, 0x76, 0xDF, 0xE9, 0x21, 0x37, 0x8A, 0x13],
                                                   [0x89, 0xD8, 0xC1, 0xE0, 0x02, 0x3D, 0x00, 0x20]],
                       [0x55, 0x54, 0x53, 0x52], 0x31),
    'XPLAT':          (mtkey._lm_dia,   lambda k: [[0x66, 0x0B, 0xCA, 0x74, 0x2A, 0x50, 0x33, 0xC0],
                                                   [0x66, 0xBA, 0xCE, 0x03, 0x66, 0xEF, 0xB0, 0x04],
                                                   [0x0F, 0xB7, 0xDB, 0x66, 0xD1, 0xE2, 0x1B, 0xC0]],
                       [0x55, 0x54, 0x53, 0x52], 0x31),
    'MDIAMOND':       (mtkey._lm_dia,   lambda k: [[0x83, 0xF8, 0x01, 0x76, 0x22, 0x56, 0x8B, 0xF0],
                                                   [0xB9, 0xFF, 0xFF, 0x00, 0x00, 0x33, 0xD2, 0x5E],
                                                   [0x8A, 0x65, 0x14, 0x8B, 0x75, 0x08, 0x38, 0x06]],
                       [0x55, 0x54, 0x53, 0x52], 0x31),
    'XTIT':           (mtkey._lm_eme,   lambda k: [[0x10, 0x57, 0xEF, 0x22, 0x01, 0x36, 0x8A, 0x9F],
                                                   [0x2E, 0x23, 0x91, 0xFF, 0xA5, 0x82, 0x09, 0x8C],
                                                   [0x92, 0x48, 0x10, 0x95, 0x8D, 0xAB, 0x87, 0x54]],
                       [0x73, 0x3C, 0xAA, 0xE7], 0x31),
    'MEMERALD':       (mtkey._lm_eme,   _emerald_init,     [0x73, 0x3C, 0xAA, 0xE7], 0x31),
    'F2002':          (mtkey._lm_eme,   _emerald_xor_init, [0x73, 0x3C, 0xAA, 0xE7], 0x31),
    'MRUBY':          (mtkey._lm_ruby,  _emerald_xor_init, [0x61, 0xE3, 0x5A, 0x13], 0x17),
    'F2003':          (mtkey._lm_ruby,  _emerald_xor_init, [0x61, 0xE3, 0x5A, 0x13], 0x17),
    'MSAPPHIRE':      (mtkey._lm_sapph, lambda k: _rom_init(k, None, 'sapphire'),
                       [0xA7, 0x67, 0x9A, 0xAA], 0x53),
    'F2004':          (mtkey._lm_sapph, lambda k: _rom_init(k, None, 'f04'),
                       [0xA7, 0x67, 0x9A, 0xAA], 0x53),
    'MJADE':          (mtkey._lm_jade,  lambda k: _rom_init(k, (0x27, 0x30, 0x42), 'add_div'),
                       [0xFF, 0x35, 0x5A, 0x4B], 0x16),
    'F2005':          (mtkey._lm_jade,  lambda k: _rom_init(k, None, 'f05'),
                       [0xFF, 0x35, 0x5A, 0x4B], 0x16),
    'MCROWN':         (mtkey._lm_crown, lambda k: _rom_init(k, (0x27, 0x30, 0x42), 'add_div'),
                       [0x12, 0x78, 0x37, 0xF3], 0x16),
    'FI2006':         (mtkey._lm_crown, lambda k: _rom_init(k, (0x03, 0x11, 0x99), 'mod'),
                       [0x12, 0x78, 0x37, 0xF3], 0x16),
}

# which password scheme goes with which mtkey.py cipher scheme (for the DS1991 generations)
CIPHER_TO_PASS = {
    'M1': ['M1'],
    'XGOLD/M2K': ['XGOLD', 'M2K'],
    'XPLAT/MDIAMOND': ['XPLAT', 'MDIAMOND'],
    'XTIT/MEMERALD': ['XTIT', 'MEMERALD', 'F2002'],
    'MRUBY': ['MRUBY', 'F2003'],
    'MSAPPHIRE': ['MSAPPHIRE', 'F2004'],
    'MJADE': ['MJADE', 'F2005'],
    'MCROWN': ['MCROWN', 'FI2006'],
}


def passwords(serial, scheme):
    """Returns the three 8-byte subkey passwords for this ROM serial and scheme."""
    magic_fn, init_fn, blk, inc = SCHEMES[scheme]
    key = mtkey.keybytes(serial)
    m = [x & B for x in magic_fn(key)]
    out = []
    for s, p in enumerate(init_fn(key)):
        p = list(p)
        seed = blk[s]
        for i in range(8):
            p[i] ^= m[i % 4]
            p[i] += seed
            seed += inc
        out.append(bytes(x & B for x in p))
    return out


def identify(img256, serial):
    """Returns [(cipher_scheme, pass_scheme, decrypted)] consistent with the stored passwords."""
    hits = []
    stored = [img256[64 * s + 8: 64 * s + 16] for s in range(3)]
    for cs, dec in mtkey.try_all(img256, serial):
        for ps in CIPHER_TO_PASS.get(cs, []):
            if [bytes(x) for x in passwords(serial, ps)] == stored:
                hits.append((cs, ps, dec))
    return hits


if __name__ == '__main__':
    if sys.argv[1] == '--table':
        ser = sys.argv[2]
        for s in SCHEMES:
            print('%-10s %s' % (s, ' '.join(p.hex().upper() for p in passwords(ser, s))))
        sys.exit()
    ok = bad = 0
    for path in sys.argv[1:]:
        if os.path.getsize(path) not in (256, 264):
            continue
        img, ser = mtkey.load_full(path)
        stored = [img[64 * s + 8: 64 * s + 16] for s in range(3)]
        if all(b == b'\0' * 8 for b in stored):
            print('%-44s %s  (no passwords stored)' % (os.path.basename(path)[:44], ser))
            continue
        hit = [s for s in SCHEMES if [bytes(p) for p in passwords(ser, s)] == stored]
        ciph = [c for c, d in mtkey.try_all(img, ser)]
        if hit:
            ok += 1
        else:
            bad += 1
        print('%-44s %s cipher=%-16s passwords=%s' % (
            os.path.basename(path)[:44], ser, ','.join(ciph) or '-', ','.join(hit) or 'NO MATCH'))
    print('\n== password scheme identified for %d dumps, unmatched %d ==' % (ok, bad))
