"""mtkey.py - Megatouch DS1991 key crypto (port of keyflasher DS91Decrypter + per-version params).

Encrypted DS1991 image (256 B) = 3 secure subkeys x [ID 8][PW 8][DATA 48] + scratchpad 64.
Decrypted "232" layout (keyflasher) = ID0 DATA0 ID1 DATA1 ID2 DATA2 SCRATCH(64).
Serial string is the OneWire address as printed (CRC first .. family last), e.g. 6D000000CB053702.

usage: mtkey.py decrypt <full_264_or_256_file> [serial]   -> prints version + writes <file>.dec232
       mtkey.py scan <dir>                                 -> decrypt every 256/264-byte file found
"""
import sys, os, re

def _lm_m2k(k):   # XGOLD, M2K
    return [k[2] ^ ((k[0] + k[1]) | k[4]), k[2] | ((k[0] - k[1]) ^ k[3]),
            k[1] & (k[3] + k[2] + k[4]), k[4] | ((k[3] + k[1]) - k[2])]
def _lm_dia(k):   # XPLAT, MDIAMOND
    return [k[2] ^ ((k[2] + k[1]) | k[4]), k[2] | ((k[3] - k[0]) ^ k[3]),
            k[1] & (k[3] + k[1] + k[4]), k[4] | ((k[0] + k[1]) - k[2])]
def _lm_eme(k):   # XTIT, MEMERALD
    return [k[3] ^ ((k[1] + k[4]) | k[2]), k[1] | ((k[2] - k[3]) ^ k[4]),
            k[4] ^ (k[3] + k[2] + k[1]), k[2] | ((k[4] + k[1]) - k[3])]
def _lm_ruby(k):
    return [((k[1] + k[3]) | k[4]) ^ k[3], (((k[3] - k[4]) ^ k[3]) | k[1]),
            (k[2] + k[1] + k[3]) ^ k[4], ((k[4] + k[2]) - k[1]) | k[2]]
def _lm_sapph(k):
    return [((k[1] ^ k[3]) - k[5]) + k[3], ((k[0] - k[5]) - k[3]) - k[1],
            ((k[2] - k[1]) + k[3]) ^ k[5], (((k[5] ^ k[2]) + k[1]) ^ k[2])]
def _lm_jade(k):
    return [((k[1] ^ k[5]) - k[3]) + k[2], ((k[1] - k[5]) - k[4]) - k[2], k[5] ^ k[1], k[2] ^ k[4]]
def _lm_crown(k):  # Crown start.elf merit_encrypt @0x0828bee0 (k = ROM bytes, family first)
    return [((k[3] - k[4]) - k[5]) ^ k[1] ^ 0x7F, (((k[1] + k[2]) - k[3]) - k[4]) ^ 0xF3,
            (k[4] + 0xBC) ^ (k[2] + k[2] + k[1]), k[4] + k[5] + k[1] + k[4] + 0x7F]
def _lm_zero(k):
    return [0, 0, 0, 0]

# name: (laserMath, inc, scratchBytes, magic4)
SCHEMES = {
    'M1':        (_lm_zero,  0x00, 64, bytes.fromhex('00000000')),
    'XGOLD/M2K': (_lm_m2k,   0x31, 64, bytes.fromhex('55545352')),
    'XPLAT/MDIAMOND': (_lm_dia, 0x31, 64, bytes.fromhex('55545352')),
    'XTIT/MEMERALD':  (_lm_eme, 0x31, 64, bytes.fromhex('733CAAE7')),
    'MRUBY':     (_lm_ruby,  0x17, 48, bytes.fromhex('61E35A13')),
    'MSAPPHIRE': (_lm_sapph, 0x53, 60, bytes.fromhex('A7679AAA')),
    'MJADE':     (_lm_jade,  0x16, 60, bytes.fromhex('FF355A4B')),
    'MCROWN':    (_lm_crown, 0x16, 60, bytes.fromhex('127837F3')),  # scratch count: verify
}

def keybytes(serial):
    return list(bytes.fromhex(serial))[::-1]   # [family, s1..s6, crc]

def _run(buf, lm, seed, inc, n, enc):
    for i in range(n):
        if enc:
            buf[i] = ((buf[i] ^ lm[i % 4]) + seed) & 0xFF
        else:
            buf[i] = ((buf[i] - seed) & 0xFF) ^ lm[i % 4]
        seed = (seed + inc) & 0xFF
    return seed

def _crypt(img256, serial, scheme, enc):
    lmf, inc, nscr, magic = SCHEMES[scheme]
    lm = [x & 0xFF for x in lmf(keybytes(serial))]
    m = list(magic)
    for i in range(3): m[i] = (m[i] + inc * 8) & 0xFF
    parts = []
    for s in range(3):
        idb = bytearray(img256[64*s: 64*s+8]); dat = bytearray(img256[64*s+16: 64*s+64])
        seed = _run(idb, lm, m[s], inc, 8, enc); _run(dat, lm, seed, inc, 48, enc)
        parts.append((idb, dat))
    scr = bytearray(img256[192:256]); _run(scr, lm, m[3], inc, nscr, enc)
    return parts, scr

def decrypt(img256, serial, scheme):
    parts, scr = _crypt(img256, serial, scheme, False)
    return b''.join(i + d for i, d in parts) + bytes(scr)          # 232-byte layout

def encrypt(dec232, serial, scheme, pw=(b'\0' * 8,) * 3):
    img = bytearray(256)
    for s in range(3):
        img[64*s: 64*s+8] = dec232[56*s: 56*s+8]; img[64*s+8: 64*s+16] = pw[s]
        img[64*s+16: 64*s+64] = dec232[56*s+8: 56*s+56]
    img[192:] = dec232[168:232]
    parts, scr = _crypt(img, serial, scheme, True)
    for s, (i, d) in enumerate(parts): img[64*s: 64*s+8] = i; img[64*s+16: 64*s+64] = d
    img[192:] = scr
    return bytes(img)

DATE = re.compile(rb'[0-9][0-9]/[0-9][0-9]/[0-9][0-9]')
def plausible(d):
    return d[:2] == b'SA' and d[2:8].isdigit() and DATE.fullmatch(d[56:64]) is not None

def try_all(img256, serial):
    return [(s, d) for s in SCHEMES if plausible(d := decrypt(img256, serial, s))]

def load_full(path, serial=None):
    b = open(path, 'rb').read()
    if len(b) == 264: serial = serial or b[256:].hex().upper(); b = b[:256]
    if serial is None:
        m = re.search(r'([0-9A-Fa-f]{16})', os.path.basename(path)); serial = m and m.group(1).upper()
    return b, serial

if __name__ == '__main__':
    if sys.argv[1] == 'decrypt':
        img, ser = load_full(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        for s, d in try_all(img, ser):
            print(s, d[:8], d[56:64], d[112:120]); open(sys.argv[2] + '.dec232', 'wb').write(d)
    elif sys.argv[1] == 'scan':
        for dp, _, fs in os.walk(sys.argv[2]):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                if os.path.getsize(p) not in (256, 264): continue
                img, ser = load_full(p)
                if not ser: print('?? no serial', p); continue
                hits = try_all(img, ser)
                print(f'{os.path.relpath(p, sys.argv[2])[:60]:60} {ser} ' +
                      (' | '.join(f'{s}: {d[:8].decode("latin1")} {d[56:64].decode("latin1")} {d[112:115].decode("latin1")}' for s, d in hits) or 'NO SCHEME'))
