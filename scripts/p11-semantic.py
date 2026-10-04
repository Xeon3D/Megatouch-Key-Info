# p11-semantic.py: resolve named NVRAM fields per Linux build by the distinctive functions that touch
# them (functions that use exactly one or few offsets pin the field). Writes analysis/p11/semantic.json
import json, re, collections
P8 = 'F:/MTKeyWork/analysis/p8/'
BUILDS = {'ruby2': ['ruby2_1100_start', 'ruby2_1100_opsetup'], 'sapphire': ['sapph_1201_start', 'sapph_1201_opsetup'],
          'jade': ['jade_1400_start', 'jade_1400_opsetup'], 'jade2': ['jade2_1510_start', 'jade2_1510_opsetup'],
          'crown': ['crown_start', 'crown_opsetup'], 'sapphire2': ['sapph2_1300_start', 'sapph2_1300_opsetup'], 'jade1421': ['jade_1421_start', 'jade_1421_opsetup']}
# field: (type, [function name regexes]; the field is the offset ALL listed functions touch, smallest if several)
SPEC = {
 'six_star_pin':            ('u32', [r'^SetNewSixStarPIN__17STM_SetSixStarPIN']),
 'security_lock_mask':      ('u32', [r'^SecurityIsLocked__Fi']),
 'security_pin':            ('u32', [r'^EnterSetSecurityPIN__17STM_SecuritySetup', r'^EnterSecurityPIN__20STM_SecurityEnterPIN']),
 'theft_deterrent_pin':     ('u32', [r'^EnterTheftDetPIN__18STM_TheftDeterrent']),
 'theft_deterrent_week':    ('u32', [r'^SetTheftDetWeek__18STM_TheftDeterrent']),
 'default_language':        ('u32', [r'^SetNextDefaultLanguage__12STM_OP_Page2']),
 'system_volume':           ('u32', [r'^ChangeSystemVolume__17STM_VolumeControl']),
 'currency_type':           ('u32', [r'SetCurrencyType']),
 'value_of_credit':         ('u32', [r'^SetCurrencyValue__20CSM_SetValueOfCredit']),
 'location_number':         ('str9', [r'^EnterLocationNumber__17STM_SetLocationNo']),
 'operator_game_number':    ('str11', [r'^EnterOperatorGameNumber__21STM_SetOperatorGameNo']),
 'game_serial_number':      ('str16', [r'^EnterSerialNumber__16STM_SetGameSerialNo']),
 'meritmoney_start_hour':   ('u8', [r'^SetStartHour__14PNM_MeritMoney']),
 'meritmoney_start_minute': ('u8', [r'^SetStartMinute__14PNM_MeritMoney']),
 'meritmoney_end_hour':     ('u8', [r'^SetEndHour__14PNM_MeritMoney']),
 'meritmoney_end_minute':   ('u8', [r'^SetEndMinute__14PNM_MeritMoney']),
 'meritmoney_free_game_limit': ('u32', [r'^SetFreeGameLimit__14PNM_MeritMoney']),
 'promo_start_hour':        ('u8', [r'^SetStartHour__16PNM_PromoCredits']),
 'promo_end_hour':          ('u8', [r'^SetEndHour__16PNM_PromoCredits']),
 'promo_idle_time':         ('u8', [r'^SetIdleTime__16PNM_PromoCredits']),
 'promo_free_credits':      ('u8', [r'^SetFreeCredits__16PNM_PromoCredits']),
 'cco_pin':                 ('u32', [r'^SetNewPIN__10CCO_SetPIN']),
 'cco_time_mode_rate':      ('u32', [r'^SetTimeModeRate__12CCO_Settings']),
 'cco_play_mode_rate':      ('u32', [r'^SetPlayModeRate__12CCO_Settings']),
 'touchtunes_credits':      ('u32', [r'^UpdateTouchTunesCredits__11BSM_BD_Main']),
 'tournamaxx_credits':      ('u32', [r'^UpdateTournaMAXXCredits__11BSM_BD_Main']),
 'current_credits':         ('u32', [r'^ClearCredits__8CSM_Main']),
 'last_clear_date':         ('u32', [r'^UpdateLastClearCurrentDate__11BSM_BD_Main']),
}
refs = {}
for b, files in BUILDS.items():
    fo = collections.defaultdict(set)
    for f in files:
        for line in open(P8 + f + '.nvrefs.tsv', encoding='utf-8', errors='replace').readlines()[1:]:
            p = line.split('\t')
            if len(p) >= 3: fo[p[2]].add(int(p[0], 16))
    refs[b] = fo
out = {}
for b, fo in refs.items():
    out[b] = {}
    for field, (typ, pats) in SPEC.items():
        sets = []
        for pat in pats:
            s = set().union(*[o for fn, o in fo.items() if re.search(pat, fn)]) if any(re.search(pat, fn) for fn in fo) else None
            if s is not None: sets.append(s)
        if not sets: continue
        common = set.intersection(*sets)
        if common: out[b][field] = {'offset': min(common), 'type': typ, 'candidates': sorted(common)[:6]}
json.dump(out, open('F:/MTKeyWork/analysis/p11/semantic.json', 'w'), indent=1)
fields = sorted(SPEC)
print('field'.ljust(28) + ''.join(b.ljust(10) for b in BUILDS))
for f in fields:
    print(f.ljust(28) + ''.join((hex(out[b][f]['offset']) + ('*' if len(out[b][f]['candidates']) > 1 else '') if f in out[b] else '-').ljust(10) for b in BUILDS))
