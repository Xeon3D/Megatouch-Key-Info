"""p18-recover.py - recover the cipher key (and the serial's inner 6 bytes) from a
Gen4 key block whose serial is unknown.

Both Gen4 ciphers use a 6-byte repeating key kk derived from the serial:
    XOR: kk[i] = magic[5-i] ^ serial[6-i]      =>  serial[6-i] = magic[5-i] ^ kk[i]
    ADD: kk[i] = magic[5-i] + serial[6-i]      =>  serial[6-i] = kk[i] - magic[5-i]
The plaintext always begins with the 6-byte part number prefix 'SAnnnn', and in XOR
mode byte i of the block is simply data[i] ^ kk[i % 6] (outside 18..21), so the first
six plaintext bytes hand over the whole key. ADD mode needs k = i//32 folded in.

usage: p18-recover.py <block_or_full_file> [offset]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkey4


def recover(block, version):
    """Returns (kk, inner6) or None, using the version's expected SA prefixes."""
    mode, magic, _, n_chunks, update_mid, _ = mtkey4.SCHEMES[version]
    magic = bytes.fromhex(magic)
    for sa in mtkey4.VALIDATORS[version][0]:
        want = sa.encode()
        if mode == 'xor':
            # i = 0..5 are all outside the 18..21 window, so kk[i] = cipher[i] ^ plain[i].
            kk = [block[i] ^ want[i] for i in range(6)]
            inner = [(magic[5 - i] ^ kk[i]) & 0xFF for i in range(6)]
        else:
            # ADD, non-special: data[i] = plain[i] + (k ^ kk[i]) - k with k = i//32 = 0.
            kk = [(block[i] - want[i]) & 0xFF for i in range(6)]
            inner = [(kk[i] - magic[5 - i]) & 0xFF for i in range(6)]
        # inner[j] corresponds to serial[6-j]; rebuild print-order bytes 1..6
        ser16 = [0] * 8
        for j in range(6):
            ser16[6 - j] = inner[j]
        cand = bytes(ser16)
        dec = mtkey4.decrypt_block(block, cand.hex().upper(), version)
        if mtkey4.plausible(dec, version):
            return kk, bytes(ser16[1:7]), dec, sa
    return None


def main():
    path = sys.argv[1]
    mem, ser = mtkey4.load(path)
    offs = [int(sys.argv[2], 0)] if len(sys.argv) > 2 else None
    print('%s  (%d bytes, serial from name: %s)' % (os.path.basename(path), len(mem), ser))
    found = False
    for v in mtkey4.SCHEMES:
        off = mtkey4.SCHEMES[v][2]
        for o in (offs or ([0] if len(mem) == 1024 else [off])):
            if o + 1024 > len(mem):
                continue
            r = recover(mem[o:o + 1024], v)
            if not r:
                continue
            kk, inner, dec, sa = r
            ck = mtkey4.checksum(dec, v)
            st = mtkey4.stored_checksum(dec, v)
            print('  %-7s off=0x%-4X part=%s  cipherkey=%s  serial[1..6]=%s  checksum=%s'
                  % (v, o, dec[:8].decode('latin1'), bytes(kk).hex().upper(),
                     inner.hex().upper(), 'ok' if ck == st else 'BAD %04X!=%04X' % (ck, st)))
            out = path + '.%s.dec1024' % v
            open(out, 'wb').write(dec)
            found = True
    if not found:
        print('  no version recovered')


if __name__ == '__main__':
    main()
