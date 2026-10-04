# Verify mtkey.py decrypt == keyflasher *_decrypted_* and encrypt round-trips (ignoring PW bytes)
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
ok = bad = 0
for full in glob.glob('**/*_full_*', recursive=True):
    dec = full.replace('_full_', '_decrypted_')
    if not os.path.exists(dec): continue
    img, ser = mtkey.load_full(full); h = mtkey.try_all(img, ser)
    want = open(dec, 'rb').read()
    if h and h[0][1] == want: ok += 1
    else: bad += 1; print('MISMATCH', full)
    if h:
        re_ = mtkey.encrypt(h[0][1], ser, h[0][0])
        diff = [i for i in range(256) if re_[i] != img[i] and not (i < 192 and 8 <= i % 64 < 16)]
        if diff: print('ENC MISMATCH', full, diff[:10])
print('ok', ok, 'bad', bad)
