# 05 — Laser-serial (ROM ID) checks

Evidence: `analysis/p5/crown_serialcheck.c`, `analysis/p5/rangechecks.asm` (`scripts/p5-rangedis.sh`),
call sites via `scripts/p5-callsite.sh`, range-constant scan `scripts/p5-rangescan.py`.

## The range check (Sapphire 2 → Crown)

Static function (Crown `0x0823e140`), called from `InitVars` (boot) and `Unlock_System_Vars`;
`0` ⇒ `KeyShutDown(<obfuscated message>)`:

```
serial48 = ROM[6]:ROM[5]:ROM[4]:ROM[3]:ROM[2]:ROM[1]      (ROM[0] = family, ROM[7] = CRC)
accept  ⇔ ROM[0] == 0x82  &&  serial48 >> 32 == 0x0040  &&  LO <= (serial48 & 0xFFFFFFFF) <= HI
```

| Version | Family | Accepted 48-bit serial | call site |
|---|---|---|---|
| Ruby 2 V11.00/V11.05 (`validate_key_range`, "KEY RANGE MISMATCH") | 0x82 | `0040_00000000`–`0040_000189C1` | `InitVars` |
|  | **0x02** | `0000_00B00DF9`–`0000_00B013AD` or `0000_00B026F9`–`0000_00B032B8` | |
| Sapphire V12.01 (`FUN_0813d0c0`), Sapphire 2 V13.00 | 0x82 | `0040_00010680`–`0040_00024000` | `InitVars` (V12.01 confirmed) |
| Jade V14.00 / V14.21, Jade 2 V15.10 | 0x82 | `0040_00022917`–`0040_00053FFF` | `InitVars`, `Unlock_System_Vars` |
| Crown V16.10 | 0x82 | `0040_00031380`–`0040_00053FFF` | `InitVars`, `Unlock_System_Vars` |

Ruby 2 is the only build that still accepts DS1991 (family 0x02) buttons, from two specific Merit lots.
The windows move upward over time (consistent with Merit buying consecutive DS1425 lots), and each build
also accepts somewhat older lots.

No laser-serial window exists in any DOS version (immediate-constant scan `scripts/p7-dosrange.py`
found only unrelated constants). DOS keys are bound by password/cipher (laser-derived) only.

Known keys against it:

| Key | family | low 32 | Jade | Crown | own version |
|---|---|---|---|---|---|
| MJADE 0900400002B65782 | 0x82 | 0x0002B657 | pass | fail (below 0x31380) | |
| MJADE 4700400002501B82 | 0x82 | 0x0002501B | pass | fail | |
| MCROWN FF004000036F1F82 | 0x82 | 0x00036F1F | pass | pass | |
| MCROWN 6D000000CB053702 (CAN-VER2) | **0x02** | — | fail | **fail** | |
| MJADE 64000000C235D602 (SA307933) | **0x02** | — | fail | fail | |
| MSAPPHIRE A9004000019A9582 / F600400001124782 | 0x82 | 0x00019A95 / 0x00011247 | fail | fail | (Sapphire: pass) |
| MRUBY EC00400000E98382 (SA3061) | 0x82 | 0x0000E983 | fail | fail | (Ruby 2: pass) |
| MRUBY FB22334455667702 | 0x02 | high word 0x2233 | fail | fail | (Ruby 2: fail — synthetic serial) |

Consequence: a Jade/Jade 2/Crown key has to be a family-0x82 button **whose factory serial is inside
Merit's purchased block**; keyflasher can rewrite contents and passwords but not the ROM serial, so a
DS1991 (0x02) blank re-flashed with Crown/Jade data is shut down at boot even though it decrypts and
passes the signature gate. (Implication for the CAN-VER2 Crown dump: it cannot be an original Merit Crown
key — or that cabinet ran a patched binary. Origin unknown (user, 2026-10-03). Its three passwords are
exactly what keyflasher's generator produces for its own 0x02 serial, which fits Crown data re-flashed
onto a DS1991 blank.)

**Re-serialised copy (P17).** `scripts/p17-reserial.py` moves a Jade/Crown key's contents onto another
ROM serial: it decrypts, re-encrypts with the new serial's laserMath, regenerates the DS1991 passwords and
computes the 1-Wire CRC. The password generator and the CRC are checked against the original dumps.
`analysis/p17/MCROWN_full_8900400004CA0282` holds the CAN-VER2 plaintext unchanged on serial
`0x82 / 0040_0004CA02`. That serial is inside the Crown window and also passes the Jade/Jade 2 window;
the serial was picked arbitrarily, so it is not a real Merit button. It is for the emulator or a
1-Wire emulator only; a real DS1991's ROM serial cannot be changed.

## Gen 4 (Force 2007–2011, ION 2007–2014, Touch2Play, Firefly) — the window is gone (P19)

`InitVars` in the ION 2014 build (`0x21f17e`, 4 434 B) compares **no immediate ≥ 0x10000** at
all, and there is no `validate_key_range`-style callee; the only key-related calls are
`Key()`, `KeyShutDown`, `Unlock_System_Vars` and `findint3`. So the 48-bit serial window that
Ruby 2 → Crown enforced (table above) was **dropped** once Merit moved to the DS1995/DS1996
containers. It became redundant: the Gen 4 keystream is derived directly from the button's
inner six serial bytes (`Docs/18`), so a key written for one button simply decrypts to
garbage on another and fails both the signature at 0x0F5 and the 16-bit checksum at 0x355.
`findint3` and `KeyShutDown` survive unchanged.

Every genuine Gen 4 dump still carries a serial in Merit's `0040_00xxxxxx` block, so the lots
continued — nothing in the software checks it.

**Platform discrimination also moved.** `ForceChk1` (Docs/02) is replaced by
`system_info::SystemInfo::IsPlatformION()`, `IsPlatformGameTime()`, `IsPlatformMindSpark()`,
`HasEntertainerIOBoard()`, `HasESKey()` and `HasImprovedAmp()`, all called from `InitVars`;
the motherboard enum is now generated (`system_info::enum_MotherBoards_tag`). The key-side
platform bit is unchanged in meaning (`Docs/18`).

## Anti-tamper around it
- `findint3(fn)`: if byte 3 or byte 0x1C of the check function (or of `FUN_0823f970`) is `0xCC` (INT3),
  the game loops forever cycling video modes and logging "Not Jersey Key, Not Dallas Key, must be
  Florida Key" — a debugger trap.
- Error strings go through `u_m_m_s` (XOR with key string `m_m_k`) so they don't appear in `strings`.

## Runtime "same key still present" check
`ConfirmKeyID` / `USBIO::USBConfirmKeyID`: periodically re-reads the ROM ID and compares it to the
boot-time `k_laser`; more than 10 consecutive mismatches ⇒ `KeyShutDown("SECURITY KEY MISMATCH")`.

## Other serial uses (not checks)
- Menu shows `ID: %02X…` (`MainMenuScreen::LoadGraphics`).
- TournaMAXX licensing derives the request code and validates the auth code from the laser serial
  (`TT_GetLicenseRequestCode`, `TT_ConfirmAuthCode`, `TT_LoadKeyFile` keyseed).
- MegaNet login sends it (`Process_Login_Request`); the server side has its own "INVALID SERIAL
  NUMBER / SECURITY KEY VIOLATION" errors (DOS string table `0x123fbc`) — out of scope.
