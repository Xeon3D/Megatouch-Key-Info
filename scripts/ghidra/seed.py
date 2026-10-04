# Ghidra preScript for flat LE images. args: <entry-hex> [<seedfile>]
# Seeds entry + every fixup target that lands in the code object, enables aggressive finder.
args = getScriptArgs()
setAnalysisOption(currentProgram, "Aggressive Instruction Finder", "true")
a = toAddr(args[0]); disassemble(a); createFunction(a, "entry")
if len(args) > 1:
    n = 0
    for line in open(args[1]):
        line = line.strip()
        if not line: continue
        x = toAddr(int(line, 16))
        if getInstructionAt(x) is None: disassemble(x)
        if getFunctionAt(x) is None and createFunction(x, None) is not None: n += 1
    print("seeded functions: %d" % n)
