# args: <outfile> <symbol>...  decompile every function that references the named symbol(s)
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
args = getScriptArgs(); out = open(args[0], "w")
fm = currentProgram.getFunctionManager(); st = currentProgram.getSymbolTable(); rm = currentProgram.getReferenceManager()
d = DecompInterface(); d.openProgram(currentProgram); mon = ConsoleTaskMonitor(); done = set()
for name in args[1:]:
    for sym in st.getSymbols(name):
        targets = [sym.getAddress()]
        # also the GOT/pointer slots that point at the symbol (PIC code references those)
        for r in rm.getReferencesTo(sym.getAddress()):
            targets.append(r.getFromAddress())
        for t in targets:
            for r in rm.getReferencesTo(t):
                f = fm.getFunctionContaining(r.getFromAddress())
                if f is None or f.getEntryPoint() in done: continue
                done.add(f.getEntryPoint())
                res = d.decompileFunction(f, 300, mon)
                out.write("// ===== %s @ %s (refs %s)\n" % (f.getName(), f.getEntryPoint(), name))
                out.write(res.getDecompiledFunction().getC() if res.decompileCompleted() else "// failed\n")
out.close()
