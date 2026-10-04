# List all 8-byte constants built by 8 consecutive "movb $imm,-d(%ebp)" (c6 45 d imm) with consecutive d,
# in each Linux binary; flag known signatures/passwords.
import glob, os, re
KNOWN = {'8723879fe2432498': 'JADE/CROWN sig', '1234567890abcdef': 'SAPPHIRE sig', 'de62104321100293': 'RUBY sig',
         'dd62104321100293': 'EMERALD sig', 'cce3aaf00f3caece': 'M1 pw'}
files = sorted(glob.glob('F:/MTKeyWork/Executables/*/start.elf') + glob.glob('F:/MTKeyWork/Executables/*/opsetup.so') +
               [f for f in glob.glob('F:/MTKeyWork/Executables/*/start') if not os.path.exists(f + '.elf')])
for f in files:
    b = open(f, 'rb').read(); found = {}
    for m in re.finditer(rb'(?:\xc6\x45(.)(.)){8}', b, re.S):
        s = m.group(0); d = [s[i*4+2] for i in range(8)]; v = bytes(s[i*4+3] for i in range(8))
        if all(((d[i+1] - d[i]) & 0xff) == 1 for i in range(7)):
            found.setdefault(v.hex(), []).append(hex(m.start()))
    for m in re.finditer(re.escape(bytes.fromhex('8723879fe2432498')) + b'|' + re.escape(bytes.fromhex('1234567890abcdef')) + b'|' + re.escape(bytes.fromhex('de62104321100293')), b):
        found.setdefault(m.group(0).hex() + '(data)', []).append(hex(m.start()))
    print('==', os.path.relpath(f, 'F:/MTKeyWork/Executables'))
    for v, offs in found.items():
        print('   ', v, KNOWN.get(v[:16], ''), len(offs), offs[:3])
