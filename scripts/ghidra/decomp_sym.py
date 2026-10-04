# args: <outfile> <symbol-substring|0xaddr>...  decompile all functions whose name contains substring
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
args = getScriptArgs(); out = open(args[0], "w")
fm = currentProgram.getFunctionManager(); d = DecompInterface(); d.openProgram(currentProgram); mon = ConsoleTaskMonitor()
done = set()
for q in args[1:]:
    if q.startswith("0x"):
        fs = [fm.getFunctionContaining(toAddr(q))]
    else:
        fs = [f for f in fm.getFunctions(True) if q in f.getName()]
    if not fs or fs[0] is None: out.write("// !! nothing for %s\n" % q); continue
    for f in fs:
        if f.getEntryPoint() in done: continue
        done.add(f.getEntryPoint())
        r = d.decompileFunction(f, 300, mon)
        out.write("// ===== %s @ %s\n" % (f.getName(), f.getEntryPoint()))
        out.write(r.getDecompiledFunction().getC() if r.decompileCompleted() else "// failed\n")
out.close()
