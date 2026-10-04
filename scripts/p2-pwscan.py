# Scan every flat DOS image and Linux binary for known DS1991 password-init constants
# (as contiguous data, or as 8 consecutive "movb $imm,[ebp+d]" / "movb $imm,[abs]" stores).
import glob, os, re
PW = {
 'M1/fixed':  ['cce3aaf00f3caece'],
 'XGOLD':     ['aa3476e199004454', '6687116623cbbc07', '224165afd3ff7620'],
 'M2K':       ['3687341235893 2cf'.replace(' ', ''), '7376dfe921378a13', '89d8c1e0023d0020'],
 'XPLAT':     ['660bca742a5033c0', '66bace0366efb004', '0fb7db66d1e21bc0'],
 'MDIAMOND':  ['83f80176225 68bf0'.replace(' ', ''), 'b9ffff000033d25e', '8a65148b75083806'],
 'XTIT':      ['1057ef2201368a9f', '2e2391ffa582098c', '924810958dab8754'],
 'MEMERALD/MRUBY-base': ['203a4218fece9910', '31094f21aa559122', '331954affa55aa16'],
}
def stores(b):
    out = set()
    for m in re.finditer(rb'(?:\xc6\x45.(.)){8}', b, re.S):
        out.add(bytes(m.group(0)[i*4+3] for i in range(8)).hex())
    for m in re.finditer(rb'(?:\xc6\x05....(.)){8}', b, re.S):
        out.add(bytes(m.group(0)[i*7+6] for i in range(8)).hex())
    return out
files = sorted(glob.glob('F:/MTKeyWork/analysis/flat/*.bin')) + sorted(glob.glob('F:/MTKeyWork/Executables/*/start.elf') + glob.glob('F:/MTKeyWork/Executables/*/opsetup.so'))
for f in files:
    b = open(f, 'rb').read(); st = stores(b); hits = []
    for k, lst in PW.items():
        n = sum(1 for h in lst if bytes.fromhex(h) in b or h in st)
        if n: hits.append(f'{k}:{n}/{len(lst)}')
    print(f'{os.path.relpath(f, "F:/MTKeyWork")[:55]:55}', ' '.join(hits))
