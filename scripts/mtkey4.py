"""mtkey4.py - Megatouch Gen4 key crypto: Force 2007-2011 / ION 2007-2014.

Port of keyflasher AddDecrypter / XorDecrypter + per-version params and validators.
Container is a plain NVRAM iButton (no subkeys, no passwords):
  DS1995 (family 0x0A, 2048 B)       - ION 2007
  DS1996 (family 0x0C/0x8C, 8192 B)  - everything later
The key payload is a single 1024-byte block at GAME_OFFSET inside that memory.

Both ciphers derive a 6-byte key from a 6-byte per-version magic and the serial's
inner 6 bytes (serial string = OneWire print order: CRC first .. family last):
  ADD: kk[i] = magic[5-i] + serial[6-i]        XOR: kk[i] = magic[5-i] ^ serial[6-i]

usage: mtkey4.py decrypt <file> [serial]
       mtkey4.py scan <dir>
"""
import sys, os, re

# version: (mode, magic6, game_offset, n_chunks, update_mid, container_size)
SCHEMES = {
    'F2007':  ('add', '55AA72371221',    0, 31, None, 8192),
    'I2007':  ('add', '55AA72371221',    0, 31, None, 2048),
    'F2008':  ('add', '55AA72371221',    0, 32, None, 8192),
    'I2008':  ('add', '55AA72371221',    0, 32, None, 8192),
    'F2009':  ('xor', '36353759564E', 1024, None, True, 8192),
    'I2009':  ('xor', '36353759564E', 1024, None, True, 8192),
    'F2010':  ('xor', '3637374C4F42',    0, None, True, 8192),
    'I2010':  ('xor', '3637374C4F42',    0, None, True, 8192),
    'F2011':  ('xor', '393D3649564E',    0, None, False, 8192),
    'I2011':  ('xor', '45414156594C', 2048, None, False, 8192),
    'I2012':  ('xor', '726D5F6A634C', 2048, None, False, 8192),
    'I2012b': ('xor', '45414156594C', 2048, None, False, 8192),   # 2nd magic keyflasher tries
    'I2013':  ('xor', '6D6B5C68624C', 6144, None, False, 8192),
    'I2014':  ('xor', '756F726E6260', 2048, None, False, 8192),
}

# version: (sa_numbers, signature_hex_or_None, checksum_len, skip_idx, ck_idx)
VALIDATORS = {
    'F2007': (('SA3526',),          '64563647452C2837', 0x35B, (853, 854),                 (853, 854)),
    'I2007': (('SA3522', 'SA3523'), '42367123EF235334', 0x35B, (853, 854),                 (853, 854)),
    'F2008': (('SA3542', 'SA3543'), 'E72136AB30C92156', 0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2008': (('SA3547', 'SA3548'), '5621C930AB3621E7', 0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'F2009': (('SA3570', 'SA3572'), '6874328C954F6743', 0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2009': (('SA3559', 'SA3560'), '213566732E476A32', 0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'F2010': (('SA3579',),          None,               0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2010': (('SA3590',),          None,               0x3EF, (18, 19, 20, 21, 853, 854), (853, 854)),
    'F2011': (('SA3603', 'SA3604'), None,               0x3F0, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2011': (('SA3605', 'SA3607'), None,               0x3F0, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2012': (('SA3614', 'SA3617'), None,               0x3F0, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2013': (('SA3623', 'SA3624'), None,               0x3F0, (18, 19, 20, 21, 853, 854), (853, 854)),
    'I2014': (('SA3628', 'SA3630'), None,               0x3F0, (18, 19, 20, 21, 853, 854), (853, 854)),
}
VALIDATORS['I2012b'] = VALIDATORS['I2012']


def _derive(magic, serial8, op):
    """6-byte cipher key from magic and the serial's inner 6 bytes."""
    if op == 'add':
        return [(magic[5 - i] + serial8[6 - i]) & 0xFF for i in range(6)]
    return [(magic[5 - i] ^ serial8[6 - i]) & 0xFF for i in range(6)]


def _is_special(data):
    """F08/I08 only: block already begins with 'SA' and byte 17 == 0x18."""
    return data[17] == 0x18 and data[0] == 0x53 and data[1] == 0x41


def _add(block, kk, n_chunks, enc):
    data = bytearray(block)
    special = _is_special(data)
    start = 0x16 if special else 0
    n = 32 * n_chunks
    m = 0
    for i in range(start, n):
        k = (i % 32) if special else (i // 32)
        t = (k ^ kk[m % 6]) - k
        m += 1
        data[i] = (data[i] + t) & 0xFF if enc else (data[i] - t) & 0xFF
    return data, special


def _xor(block, kk, update_mid, enc):
    data = bytearray(block)
    kk = list(kk)
    for i in range(4):
        prev = data[i + 18]
        data[i + 18] ^= kk[i]
        if update_mid:
            kk[i] = data[i + 18] if enc else prev
    for i in range(1024):
        if 18 <= i < 22:
            continue
        data[i] ^= kk[i % 6]
    return data


def decrypt_block(block1024, serial, version):
    mode, magic, _, n_chunks, update_mid, _ = SCHEMES[version]
    kk = _derive(bytes.fromhex(magic), bytes.fromhex(serial), mode)
    if mode == 'add':
        data, special = _add(block1024, kk, n_chunks, False)
        if n_chunks == 32 and not special:        # F08/I08 postProcess
            data[0x3E0:0x400] = b'\0' * 32
        return bytes(data)
    return bytes(_xor(block1024, kk, update_mid, False))


def encrypt_block(dec1024, serial, version):
    mode, magic, _, n_chunks, update_mid, _ = SCHEMES[version]
    kk = _derive(bytes.fromhex(magic), bytes.fromhex(serial), mode)
    if mode == 'add':
        return bytes(_add(dec1024, kk, n_chunks, True)[0])
    return bytes(_xor(dec1024, kk, update_mid, True))


def checksum(dec1024, version):
    _, _, n, skip, _ = VALIDATORS[version]
    s = sum(dec1024[:n]) - sum(dec1024[i] for i in skip)
    return s & 0xFFFF


def stored_checksum(dec1024, version):
    lo, hi = VALIDATORS[version][4]
    return dec1024[lo] | (dec1024[hi] << 8)


def fix_checksum(dec1024, version):
    out = bytearray(dec1024)
    lo, hi = VALIDATORS[version][4]
    ck = checksum(out, version)
    out[lo], out[hi] = ck & 0xFF, (ck >> 8) & 0xFF
    return bytes(out)


def plausible(dec, version, strict=True):
    """keyflasher's acceptance test. With strict=False the SA-number whitelist and the
    signature are dropped and the 16-bit checksum is required instead -- needed because the
    part number is freely editable (no game ever checks it, Docs/02) while the checksum is a
    far stronger signal."""
    sa, sig = VALIDATORS[version][0], VALIDATORS[version][1]
    if b'merit' not in dec:
        return False
    if b'\0' * 16 not in dec:
        return False
    if not strict:
        return dec[:2] == b'SA' and checksum(dec, version) == stored_checksum(dec, version)
    if dec[:6].decode('latin1') not in sa:
        return False
    if sig and bytes.fromhex(sig) not in dec:
        return False
    return True


def load(path, serial=None):
    """Returns (memory_bytes, serial). Accepts 1024/2048/8192 with optional 8-byte serial tail."""
    b = open(path, 'rb').read()
    for size in (8192, 2048, 1024):
        if len(b) == size + 8:
            return b[:size], (serial or b[size:].hex().upper())
    if serial is None:
        m = re.search(r'([0-9A-Fa-f]{16})', os.path.basename(path))
        serial = m and m.group(1).upper()
    return b, serial


def try_all(mem, serial, strict=True):
    """Returns [(version, decrypted1024)] for every Gen4 scheme that validates."""
    out = []
    for v in SCHEMES:
        off = SCHEMES[v][2]
        if len(mem) == 1024:
            block = mem
        elif off + 1024 <= len(mem):
            block = mem[off:off + 1024]
        else:
            continue
        dec = decrypt_block(block, serial, v)
        if plausible(dec, v, strict):
            out.append((v, dec))
    return out


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'decrypt':
        mem, ser = load(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        for v, d in try_all(mem, ser):
            ok = 'ok' if checksum(d, v) == stored_checksum(d, v) else \
                 'BAD calc=%04X stored=%04X' % (checksum(d, v), stored_checksum(d, v))
            print(v, d[:8].decode('latin1'), 'cksum', ok)
            open(sys.argv[2] + '.dec1024', 'wb').write(d)
    elif cmd == 'scan':
        for dp, _, fs in os.walk(sys.argv[2]):
            for f in sorted(fs):
                p = os.path.join(dp, f)
                if os.path.getsize(p) not in (1024, 1032, 2048, 2056, 8192, 8200):
                    continue
                mem, ser = load(p)
                if not ser:
                    print('%-52s -- no serial' % os.path.relpath(p, sys.argv[2])[:52])
                    continue
                hits = try_all(mem, ser)
                desc = ' | '.join('%s %s' % (v, d[:8].decode('latin1')) for v, d in hits) or 'NO SCHEME'
                print('%-52s %s %s' % (os.path.relpath(p, sys.argv[2])[:52], ser, desc))
