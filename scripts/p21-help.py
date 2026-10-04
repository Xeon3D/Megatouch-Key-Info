"""p21-help.py - harvest Merit's operator-menu help text ("<b>Label</b>|explanation") and six-star labels
from each opsetup.so -> analysis/p21/helptext.json  {build: [[label, text], ...]} (read-only on the binaries)."""
import re, json, os
SRC = {'I2014': 'analysis/p19/bin/I2014/opsetup.so', 'I2011': 'analysis/p19/bin/I2011/opsetup.so',
       'T2P2013': 'analysis/p19/bin/T2P2013/opsetup.so', 'FIREFLY': 'analysis/p19/bin/FIREFLY/opsetup.so',
       'CROWN': 'Executables/MAXX Crown (V16.10)/opsetup.so', 'JADE2': 'Executables/MAXX Jade 2 (V15.10)/opsetup.so',
       'SAPPHIRE': 'Executables/MAXX Sapphire (V12.01)/opsetup.so', 'RUBY2': 'Executables/Maxx Ruby 2 (V11.00)/opsetup.so'}
out = {}
for tag, p in SRC.items():
    if not os.path.exists(p):
        continue
    b = open(p, 'rb').read()
    items = []
    for m in re.finditer(rb'<b>([^<]{2,80})</b>\|([ -~]{0,600})', b):
        items.append([m.group(1).decode('latin1'), m.group(2).decode('latin1')])
    for m in re.finditer(rb'Check this box to ([ -~]{5,200})\x00+(Access [ -~]{3,60}from 6 stars:)', b):
        items.append([m.group(2).decode('latin1'), 'Check this box to ' + m.group(1).decode('latin1')])
    out[tag] = items
    print(tag, len(items))
json.dump(out, open('analysis/p21/helptext.json', 'w'), indent=1)
