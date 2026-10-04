# Solve DS91-style params (laserMath[4], inc, seeds) for Crown from known plaintext/ciphertext pair.
import sys
base = 'F:/MTKeyWork/Key Info & Dumps/New Keys/MAXX Crown/Crown CAN-VER2/'
c = open(base + 'MCROWN_full_6D000000CB053702', 'rb').read()[:256]
k = open(base + 'key_out', 'rb').read()
# key_out layout: ID0 ID1 ID2 then DATA0 DATA1 DATA2 then scratch
P = [k[0:8] + k[0x18:0x48], k[8:16] + k[0x48:0x78], k[16:24] + k[0x78:0xa8]]
C = [c[64*s:64*s+8] + c[64*s+16:64*s+64] for s in range(3)]
for s in range(3):
    sols = []
    for inc in range(256):
        for m in range(256):
            lm = [None]*4; okk = True
            for i in range(56):
                x = ((C[s][i] - (m + i*inc)) & 0xff) ^ P[s][i]
                if lm[i % 4] is None: lm[i % 4] = x
                elif lm[i % 4] != x: okk = False; break
            if okk: sols.append((inc, m, lm))
    print('subkey', s, len(sols), [(hex(a), hex(b), bytes(l).hex()) for a, b, l in sols[:4]])
# Using subkey0 solution (inc=0x16, lm), decrypt subkeys 1,2 for each candidate seed and show
inc, lm = 0x16, bytes.fromhex('03027d36')
for s in (1, 2):
    for m in range(256):
        d = bytes((((C[s][i] - (m + i*inc)) & 0xff) ^ lm[i % 4]) for i in range(56))
        if d[:2] in (b'10', b'R0') or sum(a == b for a, b in zip(d, P[s])) > 30:
            print(s, hex(m), d[:8], d[8:].hex(), 'match', sum(a == b for a, b in zip(d, P[s])))
