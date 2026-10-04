# Megatouch Key Info

How the Dallas iButton security keys of Merit Megatouch machines work, across every release from
**XL R1 (1997) to ION 2014**: the XL / MAXX line, the Force line, ION, Touch2Play and Firefly.
What is on a key, how each software release decides to accept one, what the key controls (territory,
games, prices, feature locks), the serial-number ranges, and the settings memory that mirrors it - plus
a key editor that reads, edits and generates keys for all 33 releases.

Everything here comes from static analysis of the original game software, decryption of key dumps, and
boot tests in the MegaPPBox emulator. Where something is inferred rather than proven, the text says so.

## Start here

| If you want | Read |
|---|---|
| a plain-language explanation | [`keyinfo-human.md`](keyinfo-human.md), or the page [`share/megatouch-keys-guide.html`](share/megatouch-keys-guide.html) |
| the research summary as a web page | [`share/megatouch-security-keys.html`](share/megatouch-security-keys.html) |
| the full technical detail | [`keyinfo.md`](keyinfo.md) and the per-topic write-ups in [`Docs/`](Docs) |
| to open or edit a key | the **Megatouch Key Tool** - see below |

Download the two HTML pages and open them in any browser; they are self-contained.

## Megatouch Key Tool

A window that opens any key dump from any release, shows every field, option switch and game by name,
lets you change them, and saves the result re-encrypted for whichever button serial you choose. It can
also generate a blank key for any release, and checks a serial against the range each release enforces.

- **Windows:** download `Megatouch Key Tool.exe` from the [Releases](../../releases) page and run it.
  No installation and no Python needed. (It is unsigned, so Windows SmartScreen may ask you to confirm.)
- **Any OS:** with Python 3 and tkinter, run `python Run/mtkeytool.py [key file]`.

See [`Run/README.md`](Run/README.md) for what each tab does.

## What is in this repository

| Path | What |
|---|---|
| `keyinfo.md`, `keyinfo-human.md` | the two handover documents (technical, and plain-language) |
| `Docs/` | per-topic write-ups: key format, version acceptance, Crown cipher, territories and options, serial ranges, settings memory, the Force / ION line, the 2007 key format, the key editor |
| `share/` | the two standalone web pages |
| `Run/` | the key editor, ready to run (Python source; the `.exe` is on the Releases page) |
| `scripts/` | the analysis scripts behind the findings, including the editor's source and its data tables |

**What is deliberately not here:** no key dumps or key images, no decrypted key contents, no Merit
software, disk images, settings files or game tables, and nothing extracted from them. The editor needs
your own key dumps to work on. Most analysis scripts expect a local workspace layout (drive paths to the
original software and images) and are included as a record of method rather than as turnkey tools.

## Credits

The DS1991-era decryption and password generators build on **Nicholas Navaroli's keyflasher** and his
keyless work; the Crown and 2007-and-later formats were recovered for this project. Megatouch, MAXX,
Force, ION and related names are trademarks of their owners. This is independent preservation and
interoperability research, not affiliated with or endorsed by Merit or its successors.
