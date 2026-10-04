# Verify MCROWN scheme against the two known Crown plaintexts.
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import mtkey
K = 'F:/MTKeyWork/Key Info & Dumps/New Keys/MAXX Crown/'
pairs = [('F:/TouchPPBox Folder/keys/MCROWN_full_FF004000036F1F82', open(K + 'Crown USA-STD/key', 'rb').read()[8:]),
         (K + 'Crown CAN-VER2/MCROWN_full_6D000000CB053702', None)]
for path, want in pairs:
    img, ser = mtkey.load_full(path)
    d = mtkey.decrypt(img, ser, 'MCROWN')
    print(os.path.basename(path), d[:8], d[56:64], d[112:120])
    if want:
        diff = [i for i in range(232) if d[i] != want[i]]
        print('  diffs vs known plaintext:', len(diff), [hex(i) for i in diff][:20])
        print('  scratch dec ', d[168:].hex()); print('  scratch want', want[168:].hex())
