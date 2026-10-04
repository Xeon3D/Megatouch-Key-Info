"""p21-build-exe.py - build the Windows executable of the key editor: Run/Megatouch Key Tool.exe

One file, no Python needed on the target machine. Built with PyInstaller from build/venv
(created once: python -m venv build/venv && build/venv/Scripts/python -m pip install pyinstaller),
so the system Python stays untouched. The name tables (scripts/data/*.json) are bundled.

    python scripts/p21-build-exe.py

The build ends by launching the packaged .exe in its --selftest mode on real keys from the
collection (one per key generation) and checking what its window showed, so a broken
executable cannot be produced silently. Prints the SHA-256 of the result.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts')
BUILD = os.path.join(ROOT, 'build')
VPY = os.path.join(BUILD, 'venv', 'Scripts', 'python.exe')
ICON = os.path.join(BUILD, 'keytool.ico')
OUT = os.path.join(ROOT, 'Run', 'Megatouch Key Tool.exe')
SAMPLES = [  # one key per generation, (path, expected version)
    (r'F:\TouchPPBox Folder\keys\MCROWN_full_FF004000036F1F82', 'MAXX Crown'),
    (os.path.join(ROOT, 'Key Info & Dumps', 'New Keys', 'MAXX Emerald', 'MEMERALD_full_6C000000A5DEE502'),
     'MAXX Emerald'),
    (os.path.join(ROOT, 'Key Info & Dumps', 'New Keys', 'MAXX Sapphire', 'MSAPPHIRE_full_F600400001124782'),
     'MAXX Sapphire'),
]


def make_icon():
    """A small iButton-style icon (steel can, teal face). Needs Pillow; skipped without it."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    im = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((12, 12, 244, 244), fill=(150, 156, 162, 255), outline=(70, 74, 80, 255), width=8)
    d.ellipse((44, 44, 212, 212), fill=(15, 111, 120, 255))
    d.ellipse((92, 92, 164, 164), fill=(220, 236, 236, 255))
    im.save(ICON, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    return ICON


def gen4_sample():
    for dp, _, fs in os.walk(os.path.join(ROOT, 'Key Info & Dumps', 'Force - ION')):
        for f in sorted(fs):
            if f.startswith('I2014_full_') or f.startswith('I2009_full_'):
                return os.path.join(dp, f)
    return None


def main():
    if not os.path.exists(VPY):
        sys.exit('build/venv missing: python -m venv build/venv && '
                 'build/venv/Scripts/python -m pip install pyinstaller')
    os.makedirs(BUILD, exist_ok=True)
    icon = make_icon()
    cmd = [VPY, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--windowed',
           '--name', 'MegatouchKeyTool',
           '--add-data', os.path.join(SRC, 'data') + os.pathsep + 'data',
           '--paths', SRC,
           '--distpath', os.path.join(BUILD, 'dist'), '--workpath', os.path.join(BUILD, 'work'),
           '--specpath', BUILD]
    if icon:
        cmd += ['--icon', icon]
    cmd.append(os.path.join(SRC, 'mtkeytool.py'))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit('PyInstaller failed')
    exe = os.path.join(BUILD, 'dist', 'MegatouchKeyTool.exe')
    shutil.copy2(exe, OUT)

    samples = list(SAMPLES)
    g4 = gen4_sample()
    if g4:
        samples.append((g4, None))
    fails = []
    for path, want in samples:
        if not os.path.exists(path):
            print('  sample missing, skipped:', path)
            continue
        res_file = os.path.join(tempfile.mkdtemp(), 'selftest.json')
        rc = subprocess.run([OUT, '--selftest', res_file, path], timeout=180).returncode
        res = json.load(open(res_file)) if os.path.exists(res_file) else {}
        ok = (rc == 0 and res.get('opened') and res.get('data_loaded') and res.get('roundtrip')
              and (want is None or res.get('version') == want) and res.get('unnamed') == 0
              and 'grp-menu' in res.get('groups', []))
        print('  %-6s %-14s options %-3s groups %s games %s unnamed %s serial %s' % (
            'ok' if ok else 'FAIL', res.get('version'), res.get('options'),
            [g[4:] for g in res.get('groups', [])], res.get('games_shown'), res.get('unnamed'),
            res.get('serial')))
        if not ok:
            fails.append(os.path.basename(path))
    if fails:
        sys.exit('self-test FAILED for: ' + ', '.join(fails))
    data = open(OUT, 'rb').read()
    print('built %s  %d bytes  sha256 %s' % (OUT, len(data), hashlib.sha256(data).hexdigest()))


if __name__ == '__main__':
    main()
