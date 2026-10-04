# funcstart.py flat.bin addr -> print start of Watcom function containing addr (prologue scan backwards)
import sys, re
img = open(sys.argv[1], 'rb').read(); base = 0x10000; a = int(sys.argv[2], 16) - base
best = None
for m in re.finditer(rb'(?<=[\xc3\x00\x90])[\x50-\x57]{0,6}\x55\x89\xe5', img[max(0, a-0x4000):a]):
    best = max(0, a-0x4000) + m.start()
print(hex(best + base))
