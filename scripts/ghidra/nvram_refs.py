# Ghidra postScript: for every function referencing symbol NVRAMData (directly or via its GOT slot),
# decompile it and record each constant offset used with the NVRAMData base.
# args: <outfile.tsv> [symbol=NVRAMData]
import re
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
args = getScriptArgs(); out = open(args[0], "w"); symname = args[1] if len(args) > 1 else "NVRAMData"
fm = currentProgram.getFunctionManager(); st = currentProgram.getSymbolTable(); rm = currentProgram.getReferenceManager()
d = DecompInterface(); d.openProgram(currentProgram); mon = ConsoleTaskMonitor()
funcs = {}
for sym in st.getSymbols(symname):
    targets = [sym.getAddress()] + [r.getFromAddress() for r in rm.getReferencesTo(sym.getAddress())]
    for t in targets:
        for r in rm.getReferencesTo(t):
            f = fm.getFunctionContaining(r.getFromAddress())
            if f is not None: funcs[f.getEntryPoint()] = f
pat_plus = re.compile(r'NVRAMData_[0-9a-f]+\s*\+\s*(0x[0-9a-f]+|\d+)\)?')
pat_idx = re.compile(r'NVRAMData_[0-9a-f]+\[(0x[0-9a-f]+|\d+)\]')
pat_var = re.compile(r'NVRAMData_[0-9a-f]+\[[^\]]*?\+\s*(0x[0-9a-f]+|\d+)\]')
out.write("offset\tkind\tfunction\tcontext\n")
for ep, f in sorted(funcs.items()):
    res = d.decompileFunction(f, 120, mon)
    if not res.decompileCompleted(): continue
    for line in res.getDecompiledFunction().getC().splitlines():
        for pat, kind in ((pat_plus, "ptr"), (pat_idx, "idx"), (pat_var, "arr")):
            for m in pat.finditer(line):
                off = int(m.group(1), 0)
                out.write("%#07x\t%s\t%s\t%s\n" % (off, kind, f.getName(), line.strip()[:160].replace("\t", " ")))
out.close()
print("functions scanned: %d" % len(funcs))
