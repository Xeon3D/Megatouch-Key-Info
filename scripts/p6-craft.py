"""p6-craft.py - make falsification test keys for MegaPPBox: change only ID0 (part number), re-encrypt
with the same scheme/serial, keep the original password bytes. Prints input + output SHA256.

usage: p6-craft.py <full_264_file> <new-ID0 (8 chars)> <out_file>
"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey

src, newid, out = sys.argv[1], sys.argv[2].encode(), sys.argv[3]
assert len(newid) == 8
raw = open(src, 'rb').read()
img, ser = mtkey.load_full(src)
(scheme, dec), = mtkey.try_all(img, ser)
dec2 = newid + dec[8:]
pw = tuple(img[64*s+8: 64*s+16] for s in range(3))
enc = mtkey.encrypt(dec2, ser, scheme, pw)
assert mtkey.decrypt(enc, ser, scheme) == dec2
open(out, 'wb').write(enc + raw[256:] if len(raw) == 264 else enc)
print(f'{scheme} {dec[:8].decode()} -> {newid.decode()}  serial {ser}')
print('in ', hashlib.sha256(raw).hexdigest(), src)
print('out', hashlib.sha256(open(out, "rb").read()).hexdigest(), out)
