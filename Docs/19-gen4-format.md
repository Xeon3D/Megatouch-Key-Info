# 19 — Gen 4 key format (Force 2007–2011, ION 2007–2014, Touch2Play 2013, Firefly 2010)

Evidence: `KeyManager::{Init,Read,ParseOptionData,Check}` and all 64 accessors in the ION 2014
`start` binary (`analysis/p19/raw/I2014.keymgr.asm`, produced by `scripts/p19-accessors.sh`);
the generated enum tables lifted out of `libenums.so` (`scripts/p19-enum2.py` →
`analysis/p19/json/*.enum_*.json`); the decoder `scripts/keyinfo4.py`; the per-key report
`analysis/p19/raw/gen4_report.txt`; the cross-key differential `analysis/p19/raw/grid4.txt`.

## Why the object offsets *are* the key offsets

`KeyManager::Read` does `memset(this, 0, 0x3F0)` and then
`USBIO::ReadDS1995KeyDataWithV40FailOver(this, 0x3F0)` — the decrypted key block is read
**straight into the KeyManager object at offset 0**. So every `[this + X]` with X < 0x3F0 in
the Gen 4 branch of an accessor is literally key offset X. (The legacy DS1991 branch instead
uses `this+0x3F0` = ID1, `this+0x400` = D0, `0x430` = ID2, `0x440` = D1, `0x470` = ID3,
`0x480` = D2, `0x4B0` = scratch, which independently reproduces the whole `Docs/01` Gen 3
map — including territory at D1[0x20], signature at D0[0x28], country at D1[0x2E], lockout at
D0[0x27] and the game bitmap at D2[0x14] whose bit for game 0x44 is D2[0x1C] bit 3.)

The container holds 1024 bytes but the game only consumes **0x3F0 (1008)**; the last 16 bytes
are never read by `start`.

## Field map

| Offset | Size | Field | Accessor |
|---|---|---|---|
| 0x000 | 8 | part number, ASCII `SAnnnnTT` | `PartNumber` |
| 0x008 | 1 | unused (0) | |
| 0x009 | 4 | **programming date — `time_t`, little endian** (`gmtime_r(this+9)` → `MM/DD/YY`) | `Date` |
| 0x00D | 4 | revision, ASCII (`R00`) | `Revision` |
| 0x011 | 1 | unused | |
| 0x012 | 4 | serial-bound token; **excluded from the checksum**, differs per button | — |
| 0x016 | 10 | territory / country description, ASCII (`USA-STD`, `USA-VER1`, …) | `CountryDesc` |
| 0x02A | 200 | MegaNet server URL, ASCII (`us.accessmerit.com`) | `ServerURL` |
| 0x0F2 | 1 | country code (0 = USA, 1 = Canada, …) | `Country` |
| 0x0F3 | 1 | New Jersey exception number | `NJExceptionNumber` |
| 0x0F4 | 1 | lockout value | `LockoutValue` |
| 0x0F5 | 8 | **signature** | `Check` |
| 0x0FE | 2 | ChampEdition game cost | `ChampEdGameCost` |
| 0x100 | 2 | ChampEdition prize mode (bits 5–6) | `ChampEdPrizeMode` |
| 0x102 | 2 | ChampEdition prize pool rate (× 5) | `ChampEdPrizePoolRate` |
| 0x104 | 8 | language mask (64 bit) | `LanguageMask` |
| 0x10C | 4 | default-language mask (index = highest set bit of mask+1) | `DefaultLanguageInx` |
| 0x114 | 4 × 23 | currency name strings | `Currency(i)` |
| 0x170 | 1 | default pricing scheme | `DefaultPricingScheme` |
| 0x171 | 1 | default currency | `DefaultCurrency` |
| 0x172 | 6 × f32 | coin-channel value (denomination) | `ChannelValue(i)` |
| 0x192 | 6 × u8 | credits awarded per channel | `Credits(i)` |
| 0x198 | 6 × f32 | credit value per channel | `Value(i)` |
| 0x1B0 | 300 × u8 | **per-game price**: low nibble = price per player, high nibble = continue cost | `DefaultGamePrice`, `DefaultGameContinueCost` |
| 0x2DC | 1 | price for game 0x2718 | `DefaultGamePrice(0x2718)` |
| 0x2DD | 120 × u8 | **option slots**, one byte each | `Option`, `ParseOptionData` |
| 0x355 | 2 | **checksum** (u16, little endian) | `Checksum`, `Check` |
| 0x357 | 2 | unit time for game 0x2718 (seconds) | `UnitTime` |
| 0x359 | 2 | unit time for game 0x271B (seconds) | `UnitTime` |
| 0x35B | 100 | web portal URL, ASCII (`meritgames.com/us-portal.htm`) | `WebPortalURL` |
| 0x3BF | 48 | **game enable bitmap**, 300 bits, MSB first within each byte | `IsActive` |
| 0x3EF | 1 | region | `Region` |
| 0x3F0 | 16 | three copies of a 4-byte serial-bound token; **never read by the game** | — |

Differences from Gen 3 (`Docs/01`): the date became a `time_t` instead of ASCII `MM/DD/YY`;
the territory string moved from D1[0x20] to 0x016; the signature moved from D0[0x28] to 0x0F5;
the option table grew from 80 slots × 2 bits to **120 slots × 1 byte**; the per-game price
array became 300 entries of two nibbles; a 300-bit game bitmap and a 16-bit checksum were
added; and the key now carries the MegaNet server URL and the web-portal URL as plain strings.

## Checksum

```
sum = Σ block[0 .. 0x3EF]  minus block[18..21]  minus block[0x355..0x356]
stored at block[0x355] (u16 LE)
```
`KeyManager::Check` implements exactly that (loop index 0..0x3EF, `cmp ecx,0x12` → skip four
bytes, `lea eax,[ecx-0x355]; cmp eax,1; jbe` → skip two), matching keyflasher's validators.
Force 2007 / ION 2007 sum only to **0x35B** instead, and their data stops before the bitmap,
so for that generation game enablement comes from the price array alone and 0x3BF/0x3EF are
not meaningful. Every genuine dump in the corpus validates (`gen4_report.txt`).

## Signatures the ION 2014 gate accepts

`KeyManager::Check` builds five 8-byte constants on the stack and compares them
case-insensitively against the decoded signature. Two are used on the legacy DS1991 path, three
on the Gen 4 path:

| Path | Signature | Seen on |
|---|---|---|
| Gen 4 | `93E41C6E20911B9B` | the ION 2014 key in the corpus |
| Gen 4 | `CFB4A9611BB72003` | the Force 2010 dump |
| Gen 4 | `00000000C7723CEF` | not seen in the corpus |
| legacy | `0123456789ABCDFF` | not seen (a Sapphire-style variant) |
| legacy | built elsewhere in the function | — |

Per-version signatures from the dumps themselves (byte-exact, at 0x0F5):

| Version | Signature | | Version | Signature |
|---|---|---|---|---|
| Force 2007 | `64563647452C2837` | | ION 2007 | `42367123EF235334` |
| Force 2008 | `E72136AB30C92156` | | ION 2008 | `5621C930AB3621E7` |
| Force 2009 | `6874328C954F6743` | | ION 2009 | `213566732E476A32` |
| Force 2010 | `CFB4A9611BB72003` | | ION 2010 | `29342DA908FBC6DE` |
| Force 2011 | `90322BBAA4370CFE` | | ION 2011 | — (synthetic sample only) |
| | | | ION 2014 | `93E41C6E20911B9B` |

ION 2008's value is Force 2008's **byte-reversed**; the pairs are deliberately related.

## The 120 option slots — all named

Lifted from `xml_gameoptions::enum_GameOptionIndex_tag` in `libenums.so` (a jump table, so the
value → name mapping is exact, not inferred). `num_used_opts` = 120 sits at 0x78, confirming the
count; 0x79 and above return `_invalid_GameOptionIndex_enum`.

**The table is byte-identical across ION 2011, ION 2014, Touch2Play 2013 and Firefly 2010**
(zero differences in slots 0x00–0x78), and it agrees with every slot `Docs/04` had pinned by
hand for Crown: 0x0D `six_stars_enabled_inx`, 0x11 `golf_has_women_inx`, 0x14
`tournamaxx_enabled_inx`, 0x31 `lease_mode_enabled_inx`. So this table supersedes and completes
the partial Gen 3 table in `Docs/04` for slots 0x00–0x4F as well.

Slot semantics are unchanged from Gen 3: **0 = locked off, 1 = forced on, 2 or 3 = operator-
selectable** (`IsOptionSelectable` ⇔ value ∈ {2,3}); when selectable the effective value comes
from NVRAM (`NVRAMMap::IsOptionOn`).

*P21:* the names are now backed by meanings and by who writes each slot — 67 of the 120 carry
Merit's own operator help text, and each build's menus give the menu / key-only split (ION 2011,
ION 2014 and Touch2Play 2013: 69 menu, 18 key-only, 33 unused; Firefly 74 / 13 / 33). See
`Docs/21` and `scripts/data/option_catalog.json`.

| # | option | # | option | # | option |
|---|---|---|---|---|---|
| 0x00 | `sol_free_game_inx` | 0x29 | `free_play_enabled_inx` | 0x52 | `access_opsetup_from_sixstars` |
| 0x01 | `allow_game_continues_inx` | 0x2A | `games_easy_inx` | 0x53 | `access_unlock_firefly_from_sixstars` |
| 0x02 | `enable_rental_mode_inx` | 0x2B | `newtrivia_same_cat_inx` | 0x54 | `allow_player_unlock_firefly` |
| 0x03 | `psychographic_profiles_enabled_inx` | 0x2C | `newtrivia_extra_ques_inx` | 0x55 | `prize_pool_on_main_menu` |
| 0x04 | `bonus_replay_allowed_inx` | 0x2D | `my_merit_enabled_inx` | 0x56 | `access_location_card_setup_from_sixstars` |
| 0x05 | `price_in_cred_or_money_inx` | 0x2E | `continuous_bonus_round_inx` | 0x57 | `unused_option5_defyes` |
| 0x06 | `sort_price_descriptions_inx` | 0x2F | `senior_mode_enabled_inx` | 0x58 | `touchtunes_enabled` |
| 0x07 | `powsol_split_col_inx` | 0x30 | `enable_theft_deterrent_inx` | 0x59 | `generic_kidzpace_mode_enabled` |
| 0x08 | `master_sex_kill_inx` | 0x31 | `lease_mode_enabled_inx` | 0x5A | `access_free_credits_from_sixstars` |
| 0x09 | `trivia_show_answer_inx` | 0x32 | `tmaxx_from_6stars_inx` | 0x5B | `bypass_wireless_security` |
| 0x0A | `trivia_num_prim_rnds_inx` | 0x33 | `promo_credits_enabled_inx` | 0x5C | `allow_coin_in_table_modification` |
| 0x0B | `tmaxx_ok_in_freeplay` | 0x34 | `linked_games_enabled` | 0x5D | `uae_prize_mode_enabled` |
| 0x0C | `price_diff_than_tmaxx` | 0x35 | `no_names_in_hi_scores` | 0x5E | `unused_option3_defno` |
| 0x0D | `six_stars_enabled_inx` | 0x36 | `enable_web_filter` | 0x5F | `unused_option4_defno` |
| 0x0E | `powsol_free_game_inx` | 0x37 | `enable_high_res` | 0x60 | `disable_questionable_content` |
| 0x0F | `rental_mode_5_row_support` | 0x38 | `enable_megaweb` | 0x61 | `turn_off_automatic_reconnect` |
| 0x10 | `touch_2_play_mode_enabled` | 0x39 | `enable_prizezone` | 0x62 | `disable_ami_exit` |
| 0x11 | `golf_has_women_inx` | 0x3A | `enable_premium_erotic` | 0x63 | `enable_ami` |
| 0x12 | `phunt_new_ver_inx` | 0x3B | `enable_ent_channel_removed` | 0x64 | `creditcard_enabled` |
| 0x13 | `merit_money_enabled_inx` | 0x3C | `enable_ed_attract` | 0x65 | `creditcard_pulse_hard_meter` |
| 0x14 | `tournamaxx_enabled_inx` | 0x3D | `enable_coinless_coinop_inx` | 0x66 | `unused_option5_defno` |
| 0x15 | `music_timer_from_6stars_inx` | 0x3E | `enable_ddc` | 0x67 | `firefly_mode_enabled` |
| 0x16 | `plr_select_lang_inx` | 0x3F | `enable_quick_pricing` | 0x68 | `unused_option2_always` |
| 0x17 | `auto_clr_hiscr_inx` | 0x40 | `enable_prem_ero_idle_ad_ins` | 0x69 | `unused_option3_always` |
| 0x18 | `allow_clr_creds_inx` | 0x41 | `enable_sound_in_idle_mode` | 0x6A | `unused_option4_always` |
| 0x19 | `strip_moans_inx` | 0x42 | `enable_operator_website` | 0x6B | `unused_option5_always` |
| 0x1A | `hiscore_from_6stars_inx` | 0x43 | `enable_mindspark_mode` | 0x6C | `unused_option6_always` |
| 0x1B | `vbboard_from_6stars_inx` | 0x44 | `enable_showtenders_deprecated` | 0x6D | `allow_meganet_without_tournamaxx` |
| 0x1C | `volume_from_6stars_inx` | 0x45 | `enable_auto_continue` | 0x6E | `unused_option1_never` |
| 0x1D | `disable_free_creds_inx` | 0x46 | `enable_card_back_ad_support` | 0x6F | `unused_option2_never` |
| 0x1E | `allow_nudity_inx` | 0x47 | `enable_premiere_tourn_terminal` | 0x70 | `unused_option3_never` |
| 0x1F | `nudity_level_inx` | 0x48 | `sticker_book_timer_inx` | 0x71 | `unused_option4_never` |
| 0x20 | `show_deck_inx` | 0x49 | `player_key_enabled` | 0x72 | `enable_download_selector` |
| 0x21 | `checkers_rules_inx` | 0x4A | `enable_bowling_poker` | 0x73 | `creditcard_demo_mode` |
| 0x22 | `deck_fan_time_inx` | 0x4B | `slow_senior_games` | 0x74 | `enable_showtenders` |
| 0x23 | `lang_but_flags_inx` | 0x4C | `enable_hi_res_for_tt` | 0x75 | `enable_rev_share` |
| 0x24 | `tourn_support_inx_private` | 0x4D | `enable_erotic_in_attract_mode` | 0x76 | `network_access_from_six_stars` |
| 0x25 | `cal_from_6stars_inx` | 0x4E | `enable_erotic_in_new_games_cat` | 0x77 | `unused_option6_never` |
| 0x26 | `trit_face_up_inx` | 0x4F | `auto_place_erotic_in_new_games_cat` | 0x78 | `num_used_opts` |
| 0x27 | `strip_rewind_inx` | 0x50 | `network_options_from_6stars_inx` |  |  |
| 0x28 | `enable_kids_category_inx` | 0x51 | `alt_language_select_on` |  |  |

## Game ids

Gen 4 game ids are the values of the generated enum `xml_gameinfo::GameIds`, recovered from
`enum_GameIds_tag` in `libenums.so` (`scripts/p19-enum2.py`). The enum is sparse: ids
**0x000–0x12B** are real games (the range the key's price array and bitmap cover) and a second
block at **0x2718+** holds pseudo-entries that are not key-addressable — `g_menu`,
`calibrate`, `browser`, `layout`, `installer`, `enter_operator_pin_first_boot`,
`champed_loopsign`, … That second block is why earlier attempts to read the id order out of
`gamedata.xml` or `settings.xml` failed.

| Line | Builds merged | Dense ids pinned | Unpinned |
|---|---|---|---|
| ION (covers ION 2007–2014, Touch2Play 2013, Firefly 2010) | I2014, I2011, T2P2013, FIREFLY | **293 of 0x000–0x12C** | 230, 282, 294–299 |
| Force | F2011 only | 168 | the rest |

→ `analysis/p19/json/ION.gameids.merged.json`, `FORCE.gameids.merged.json`.

The merge across four ION builds is conflict-free except where a build genuinely renames a
slot (`g_sneak_peek_2014_01/02` became real games later) or where the sentinel
`max_used_game_range_id` marks that build's own upper bound. The Force line is only partly
pinned because Force 2011 uses an older generator shape (string loaded before the compare,
all matches jumping to one shared return) in which half the leaves are reached by
fall-through; that is a limitation of the extractor, not an unknown in the format. The key
data itself is fully decoded either way — only the *labels* for those ids are missing.

*P21:* that gap is closed in practice. The 168 ids Force 2011 does pin agree with the ION enum
**without a single conflict**, so the ION table fills the Force gaps and the key tool names Force
Gen 4 games from it (`scripts/data/game_tables.json`, table `FORCE4`; `Docs/21`). Only the 8
unpinned ION ids remain unlabelled anywhere.

Ground check: decoding the genuine ION 2014 key's price array with the merged ION table and
comparing the resulting names against the `GAME_ACTIVE` list in that machine's own
`/merit/settings.xml` gives a Jaccard overlap of **0.79**, and every remaining difference is
either a 0x2718+ pseudo-entry (which cannot be on a key) or a game the operator switched off.
Using `gamedata.xml` order instead scores 0.43–0.58, so the enum is the right source.

`gamedata.xml` (now at `/usr/local/gamedata/config/gamedata.xml`) remains the place to get a
**display name** for a symbolic id: it carries `<GameId>G_FOO</GameId>` plus `<Description>`
and `<ShortGameDesc>`. Extracted per build into `analysis/p19/xml/<tag>/`.

## Transport

`USBIO::ReadDS1995KeyData(buf, len, bool)` / `…WithV40FailOver(buf, 0x3F0)` read the block over
the USB I/O board. Unlike the Crown-era path (`Docs/03`), the ION board returns the data
**unmasked** — the V40.02 capture (`Docs/18`) concatenates straight into the encrypted block.
`USBIO::GetKeyFamilyCode()` selects Gen 4 vs legacy; `USBIO::USBReadKeyID`,
`usbioboard::USBIOBoard::ReadKeyID(key_id_t&)` read the ROM id; `KeyManager::ConfirmKey` is the
runtime still-present check. `KeyManager::WriteKeyData` exists — the game can *write* to the
button (the DS1995/DS1996 are plain read/write NVRAM, with no password gate at all).

## New surface found here (guardrail 7)

`KeyManager::Check` opens and reads **its own executable** with raw `open`/`read`/`close`
syscalls (0x400 bytes into a stack buffer) before doing the signature comparison — an
integrity self-check embedded in the key gate. Recorded as surface **N** in `CLAUDE.md`;
not analysed. The data it reads is also what makes the first ~40 bytes of `Check` disassemble
as garbage.

## Open

1. A genuine ION 2014 key dump. The only sample is internally inconsistent (country code 1
   with territory `USA-STD`, date decoding to 1977) and is probably hand-made.
2. The meaning of the serial-bound tokens at 0x012 (in the checksum's skip list) and the three
   copies at 0x3F0 (outside the data the game reads). Across six ION 2009 keys that are
   otherwise byte-identical, these are the *only* differing bytes, so they are derived from the
   button serial by something other than the cipher — likely the programmer's own anti-clone
   marker. Nothing in `start` reads 0x3F0.
3. Labels for the 8 unpinned ION ids. (The Force-line gap is closed in practice — ION fills it,
   see above.)
4. The Gen 4 NVRAM layout: settings moved to `/merit/settings.xml` + SQLite, and
   `/config/nvram.dat` shrank to 5 792 B, so the `Docs/08` NVRAM work does not carry over.
