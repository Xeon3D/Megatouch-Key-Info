"""p17-reserial.py - move a key's contents onto a different 1-Wire ROM serial (for emulators / DS1991
replacements). Decrypts with the source serial, re-encrypts every subkey + scratchpad with the new
serial's laserMath, and regenerates the three DS1991 passwords for the new serial. The plaintext is
unchanged (asserted by a round trip). Prints input + output SHA256.

usage: p17-reserial.py <full_264 key> <family hex> <48-bit serial hex> <out_dir>
  e.g. p17-reserial.py MCROWN_full_6D000000CB053702 82 00400004CA02 analysis/p17

Password generation = keyflasher PasswordGenerator (Jade-style init (i + k[i] + 0x27/0x30/0x42),
then merit_encrypt with laserMath and blkVCode[0..2]); verified to reproduce the passwords stored in
the original CAN-VER2 Crown dump. Only schemes with that password style are supported.
"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey

PW_STYLE = {'MJADE', 'MCROWN'}   # Jade-style password init (keyflasher MJadePasswordGenerator)

def crc8(data):                   # Dallas/Maxim 1-Wire CRC (x^8 + x^5 + x^4 + 1, reflected)
    c = 0
    for b in data:
        for _ in range(8):
            mix = (c ^ b) & 1; c >>= 1
            if mix: c ^= 0x8C
            b >>= 1
    return c

def rom_serial(family, s48):
    rom = bytes([family]) + s48.to_bytes(6, 'little')
    return (rom + bytes([crc8(rom)]))[::-1].hex().upper()   # printed form: CRC first .. family last

def passwords(serial, scheme):
    lmf, inc, _, magic = mtkey.SCHEMES[scheme]
    key = mtkey.keybytes(serial); m = lmf(key); out = []
    for s, c in enumerate((0x27, 0x30, 0x42)):
        p = list(key)
        if s: p[0] = s
        for i in range(7):
            t = i + key[i] + c; p[i] = (t + t // 0xFF) ^ p[i]
        seed = magic[s]
        for i in range(8):
            p[i] ^= m[i % 4]; p[i] += seed; seed += inc
        out.append(bytes(x & 0xFF for x in p))
    return out

if __name__ == '__main__':
    src, fam, s48, outdir = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3], 16), sys.argv[4]
    raw = open(src, 'rb').read(); img, ser = mtkey.load_full(src)
    (scheme, dec), = mtkey.try_all(img, ser)
    assert scheme in PW_STYLE, f'{scheme}: password generator not ported'
    old_pw = tuple(img[64 * s + 8: 64 * s + 16] for s in range(3))
    assert tuple(passwords(ser, scheme)) == old_pw, 'generator does not reproduce the source passwords'
    new = rom_serial(fam, s48)
    enc = mtkey.encrypt(dec, new, scheme, tuple(passwords(new, scheme)))
    assert mtkey.decrypt(enc, new, scheme) == dec
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f'{scheme}_full_{new}')
    open(out, 'wb').write(enc + bytes.fromhex(new))
    print(f'{scheme} {dec[:8].decode()} serial {ser} -> {new} (CRC {new[:2]})')
    print('in ', hashlib.sha256(raw).hexdigest(), src)
    print('out', hashlib.sha256(open(out, 'rb').read()).hexdigest(), out)
