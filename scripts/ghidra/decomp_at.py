# Ghidra headless postScript: decompile the function CONTAINING each address arg.
# args: <outfile> <addr> [<addr> ...]   (appends all to one file)
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
from ghidra.app.cmd.function import CreateFunctionCmd
args = getScriptArgs()
out = open(args[0], "w")
fm = currentProgram.getFunctionManager(); af = currentProgram.getAddressFactory()
d = DecompInterface(); d.openProgram(currentProgram); mon = ConsoleTaskMonitor()
seen = set()
for a in args[1:]:
    addr = af.getAddress(a)
    f = fm.getFunctionContaining(addr)
    if f is None:
        disassemble(addr); CreateFunctionCmd(addr).applyTo(currentProgram, mon); f = fm.getFunctionContaining(addr)
    if f is None:
        out.write("// !! no function for %s\n" % a); continue
    if f.getEntryPoint() in seen: continue
    seen.add(f.getEntryPoint())
    r = d.decompileFunction(f, 300, mon)
    out.write("// ===== %s (contains %s)\n" % (f.getEntryPoint(), a))
    out.write(r.getDecompiledFunction().getC() if r.decompileCompleted() else "// decompile failed\n")
out.close()
