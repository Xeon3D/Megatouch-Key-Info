"""p20-make-run.py - build Run/, a self-contained, double-clickable copy of the key editor.

Run/ holds only what the program needs: the five Python modules, the name tables, a
launcher that finds Python itself, and a README. Nothing in Run/ reaches back into the
workspace, so the folder can be copied anywhere (a USB stick, another machine).

    python scripts/p20-make-run.py          # (re)build Run/
    python scripts/p20-make-run.py --check  # verify an existing Run/ still works

The build ends by running the program's own regression suite from inside Run/, so a broken
copy cannot be produced silently.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts')
RUN = os.path.join(ROOT, 'Run')

MODULES = ['mtkeytool.py', 'mtkeylib.py', 'mtkey.py', 'mtkey4.py', 'mtpass.py', 'keyinfo4.py']
DATA = ['options.json', 'games.json', 'option_catalog.json', 'game_tables.json']

LAUNCHER = r"""@echo off
rem  Megatouch Key Tool - launcher
rem  Finds a Python 3 with tkinter and starts the editor. Pass a key file to open it.
setlocal
cd /d "%~dp0"

set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (where python >nul 2>&1 && set "PY=python")

if not defined PY (
  echo.
  echo   Python 3 was not found on this computer.
  echo.
  echo   Install it from https://www.python.org/downloads/ and tick
  echo   "Add python.exe to PATH" in the installer, then run this file again.
  echo.
  pause
  exit /b 1
)

%PY% -c "import tkinter" >nul 2>&1
if errorlevel 1 (
  echo.
  echo   This Python has no tkinter, which the editor needs for its window.
  echo   Re-run the Python installer and enable "tcl/tk and IDLE".
  echo.
  pause
  exit /b 1
)

%PY% "%~dp0mtkeytool.py" %*
if errorlevel 1 (
  echo.
  echo   The editor exited with an error. The message above says why.
  pause
)
endlocal
"""

PYW_NOTE = r"""@echo off
rem  Same as "Megatouch Key Tool.bat" but without a console window.
setlocal
cd /d "%~dp0"
set "PYW="
where pyw >nul 2>&1 && set "PYW=pyw -3"
if not defined PYW (where pythonw >nul 2>&1 && set "PYW=pythonw")
if not defined PYW (
  call "%~dp0Megatouch Key Tool.bat" %*
  exit /b
)
start "" %PYW% "%~dp0mtkeytool.py" %*
endlocal
"""

README = """# Megatouch Key Tool

Reads, edits and generates Merit Megatouch security keys for **every release from XL R1
(1997) to ION 2014** - the Maxx/XL line and the Force / ION line, plus Touch2Play and
Firefly.

## Running it

Double-click **`Megatouch Key Tool.exe`**. It is a single Windows program: no Python, no
installation, no admin rights, no internet. You can also drag a key file onto it.

If you prefer running from source (any OS with Python 3 + tkinter), double-click
**`Megatouch Key Tool.bat`** (or `Megatouch Key Tool (no console).bat`). If Python is missing
the launcher says so and points at python.org.

From a terminal:

    python mtkeytool.py                     open the editor
    python mtkeytool.py <key file>          open the editor on a key
    python test-mtkeytool.py                run the self-test (needs the key collection)

## What it does

**Opens any key.** Point it at a keyflasher dump (`*_full_*`, `*_encrypted_*`), a raw button
image, or a decrypted block. It works out the release, the button type and the cipher by
itself. For a 2007-or-later key with no serial on file it recovers the serial from the cipher
and asks whether to use it.

**Shows everything, by name.** Four tabs:

- *Fields* - part number, date, revision, territory, country, lockout, signature, checksum,
  language masks, coin channels, currency names, server and portal addresses, and the
  serial-tied bytes. Double-click a row to change it.
- *Options* - the feature switches (80 on DS1991-era keys - XL and DOS MAXX included - 88 on
  Sapphire, 120 on Force/ION 2007+), each with a plain name and a description of what it does,
  in Merit's own help-text words where the operator menus have them. They are grouped by who
  sets them: **the operator menus** (opsetup) or **the key only** (set by Merit), plus the
  ones the game, the MegaNet server or nobody uses. Each slot is locked off, forced on, or
  left to the operator. Select one to read the full description below the list.
- *Games* - every game with the name used by **that key's own software release** (the
  release's game table), whether the key enables it, its price (and continue cost on
  2007+ keys) and Merit's per-game flags (Force only, Prize Zone, continuable ...). "Game
  names from" switches to another release's table. Space toggles the selected game.
- *Raw plaintext* - a hex dump of the decrypted key.

**Saves a new key.** "Save as" writes either the encrypted button image (what you flash,
with the serial appended) or the decrypted plaintext. The checksum is recomputed, the cipher
re-applied and - for the DS1991-era releases - the three subkey passwords regenerated. Every
save is verified by decrypting the result again.

**Changes the button.** "Change button serial" moves a key's contents onto a different
1-Wire serial, re-keying the cipher and the passwords. While you type it checks the serial
against what that release enforces: the 1-Wire CRC ("Fix CRC" corrects it), the button family,
and - for Ruby 2 to Crown - the laser-serial window Merit's software accepts ("KEY RANGE
MISMATCH" otherwise). "Suggest a valid serial" picks one inside the window. Useful for
emulators; a real DS1991's laser serial cannot be changed.

**Generates a key from nothing.** "New" builds a blank key for any of the 33 releases, with
that release's signature, part number and sane US coin defaults, ready to fill in.

## Things worth knowing

- The six-digit model number (`SA3048`, `SA3511`, …) is **never checked** by any Megatouch
  software. The release is decided by the passwords, the cipher and the 8-byte signature.
- From Ruby 2 to Crown the Linux machines also require the button's factory serial to fall in
  a range Merit bought. The 2007-and-later machines dropped that check.
- Up to 2006 a key is a DS1991/DS1425 MultiKey (256 bytes, three password-protected
  compartments). From Force 2007 / ION 2007 it is a plain DS1995 or DS1996 memory button
  holding one 1024-byte block with **no passwords at all**.
- Changing the part number is safe (nothing checks it). Changing the **signature** or the
  **territory** is what makes a key stop booting.

## Files

| File | What |
|---|---|
| `mtkeytool.py` | the editor window |
| `mtkeylib.py` | the model: one object covering all four key generations |
| `mtkey.py` | cipher for the DS1991 releases (XL R1 … Crown, Force 2002-2006, ION 2006) |
| `mtkey4.py` | cipher and checksum for Force 2007-2011 / ION 2007-2014 |
| `mtpass.py` | subkey password generators for every DS1991 release |
| `keyinfo4.py` | command-line report for a Force/ION key |
| `data/options.json` | the 120 option-switch names |
| `data/games.json` | game id to name, for the Force and ION lines |
| `data/game_tables.json` | game names per release (each release's own game table) |
| `data/option_catalog.json` | option labels, descriptions, menu / key-only classes per release |
| `Megatouch Key Tool.exe` | the same program, packaged (built by `scripts/p21-build-exe.py`) |
| `test-mtkeytool.py` | regression suite |

Full technical write-ups live in the workspace this was built from: `Docs/01` (key format),
`Docs/18` (the Force/ION line), `Docs/19` (the 2007 format, all switch names), `Docs/21` (what each
switch does and who sets it, per-release game names, serial-range checks). Plain-language and
agent-readable summaries of the whole thing are `keyinfo-human.md` and `keyinfo.md`.

Authorized preservation and interoperability work.
"""


def build():
    keep = {}
    if os.path.isdir(RUN):
        # the packaged .exe is built separately (scripts/p21-build-exe.py) - keep it
        for f in os.listdir(RUN):
            if f.lower().endswith('.exe'):
                keep[f] = open(os.path.join(RUN, f), 'rb').read()
        # clear the contents, not the folder itself (Windows refuses while Explorer has it open)
        for f in os.listdir(RUN):
            p = os.path.join(RUN, f)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(os.path.join(RUN, 'data'), exist_ok=True)
    for f, data in keep.items():
        with open(os.path.join(RUN, f), 'wb') as fh:
            fh.write(data)
    for m in MODULES + ['test-mtkeytool.py']:
        shutil.copyfile(os.path.join(SRC, m), os.path.join(RUN, m))
    for d in DATA:
        shutil.copyfile(os.path.join(SRC, 'data', d), os.path.join(RUN, 'data', d))
    with open(os.path.join(RUN, 'Megatouch Key Tool.bat'), 'w', newline='\r\n') as f:
        f.write(LAUNCHER)
    with open(os.path.join(RUN, 'Megatouch Key Tool (no console).bat'), 'w', newline='\r\n') as f:
        f.write(PYW_NOTE)
    with open(os.path.join(RUN, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(README)
    print('built %s' % RUN)
    for root, _, files in os.walk(RUN):
        for f in sorted(files):
            p = os.path.join(root, f)
            print('   %-38s %7d B' % (os.path.relpath(p, RUN), os.path.getsize(p)))


def verify():
    """Import and exercise the copy in Run/, with the workspace scripts/ off sys.path."""
    code = (
        'import sys, os; sys.path.insert(0, os.getcwd());'
        'import mtkeylib as L;'
        'k = L.Key.new("ION 2014", L.make_serial(0x8C, 0x004000031380));'
        'assert k.verify_roundtrip() and k.checksum_ok();'
        'assert len(k.options()) == 120 and k.options()[0x14][1] == "TournaMAXX";'
        'assert k.option_info(0x14)["cls"] in ("menu", "key") and k.name_table() == "ION4";'
        'assert len(L.all_versions()) == 33;'
        'import mtkeytool;'
        'print("Run/ self-check OK:", k.summary())'
    )
    r = subprocess.run([sys.executable, '-c', code], cwd=RUN, capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode:
        return 1
    suite = os.path.join(RUN, 'test-mtkeytool.py')
    r = subprocess.run([sys.executable, suite], cwd=RUN, capture_output=True, text=True)
    tail = [l for l in r.stdout.strip().splitlines() if l.strip()][-1:]
    print('regression suite from Run/:', ' '.join(tail) or r.stderr.strip()[-200:])
    return r.returncode


if __name__ == '__main__':
    if '--check' not in sys.argv:
        build()
    sys.exit(verify())
