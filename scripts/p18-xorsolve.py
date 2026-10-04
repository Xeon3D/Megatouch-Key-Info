"""p18-xorsolve.py - identify a Gen4 XOR-mode key block with no serial and no version.

The XOR cipher is a repeating 6-byte key over the whole 1024-byte block (except bytes
18..21). Any run of plaintext zeros therefore prints the key verbatim, and the part
number 'SAnnnn' at offset 0 gives it directly. Once the key kk is known:
    serial[6-i] = magic[5-i] ^ kk[i]
identifies the version (the magic whose recovered inner serial bytes are a sane Merit
serial) and the button's serial at the same time.

usage: p18-xorsolve.py <file> [<file> ...]
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey4

SANE_PREFIX = bytes.fromhex('004000')   # every Merit DS1995/DS1996 lot seen so far


def kk_from_prefix(block, sa):
    """kk from the known 6-byte part-number prefix at offset 0."""
    return [block[i] ^ sa[i] for i in range(6)]


def kk_from_zeros(block):
    """kk from the most common period-6 phase-aligned byte at each phase."""
    kk = []
    for phase in range(6):
        c = collections.Counter(block[i] for i in range(phase, 1024, 6) if not 18 <= i < 22)
        kk.append(c.most_common(1)[0][0])
    return kk


def serial_from_kk(kk, version):
    magic = bytes.fromhex(mtkey4.SCHEMES[version][1])
    ser = [0] * 8
    for i in range(6):
        ser[6 - i] = (magic[5 - i] ^ kk[i]) & 0xFF
    return bytes(ser)


def solve(block):
    """Returns a list of (version, serial_inner6, kk, decrypted, checksum_ok)."""
    results = []
    cands = [kk_from_zeros(block)]
    for v in mtkey4.SCHEMES:
        for sa in mtkey4.VALIDATORS[v][0]:
            cands.append(kk_from_prefix(block, sa.encode()))
    seen = set()
    for kk in cands:
        t = tuple(kk)
        if t in seen:
            continue
        seen.add(t)
        for v in mtkey4.SCHEMES:
            if mtkey4.SCHEMES[v][0] != 'xor':
                continue
            ser = serial_from_kk(kk, v)
            dec = bytes(block[i] ^ kk[i % 6] if not 18 <= i < 22 else block[i] for i in range(1024))
            # re-run the real decrypt with the recovered serial so the 18..21 window
            # and updateMagicMidCycle are handled exactly as the game does it.
            dec = mtkey4.decrypt_block(block, ser.hex().upper(), v)
            if not mtkey4.plausible(dec, v):
                continue
            ck = mtkey4.checksum(dec, v) == mtkey4.stored_checksum(dec, v)
            results.append((v, ser[1:7], bytes(kk), dec, ck))
    return results


def main():
    for path in sys.argv[1:]:
        mem = open(path, 'rb').read()
        print('%s  (%d bytes)' % (os.path.basename(path), len(mem)))
        offs = range(0, max(1, len(mem) - 1023), 1024)
        hit = False
        for o in offs:
            block = mem[o:o + 1024]
            if len(block) < 1024:
                continue
            for v, inner, kk, dec, ck in solve(block):
                sane = 'merit-lot' if inner.startswith(SANE_PREFIX) else 'UNUSUAL LOT'
                print('  off=0x%-5X %-7s part=%s  key=%s  serial[1..6]=%s (%s)  checksum=%s'
                      % (o, v, dec[:8].decode('latin1'), kk.hex().upper(),
                         inner.hex().upper(), sane, 'ok' if ck else 'BAD'))
                open(path + '.%s.dec1024' % v, 'wb').write(dec)
                hit = True
        if not hit:
            print('  nothing recovered (not XOR-mode, or not a Gen4 key block)')


if __name__ == '__main__':
    main()
