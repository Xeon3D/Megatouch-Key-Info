#!/usr/bin/env python3
"""mtkeytool.py - Megatouch security key editor (GUI).

Reads any Merit Megatouch key dump, shows every decoded field, lets you change the fields,
the 120/80 option locks and the per-game enable/price table, and writes the result back out
as a new key file - re-encrypted and re-password-ed for whatever button serial you point it
at. It can also generate a blank key for any of the 33 releases from XL R1 to ION 2014.

    python mtkeytool.py [key file]

Model layer: mtkeylib.Key (crypto in mtkey.py / mtkey4.py / mtpass.py).
Field maps: Docs/01 (gen 1-3), Docs/19 (gen 4). Option names: Docs/19.

Nothing here writes to a physical iButton; it produces files for keyflasher / an emulator.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mtkeylib as L

OPT_STATES = [('0 - locked off', 0), ('1 - forced on', 1),
              ('2 - operator selectable', 2), ('3 - operator selectable', 3)]


class App(tk.Tk):
    def __init__(self, path=None):
        super().__init__()
        self.title('Megatouch key tool')
        self.geometry('1060x720')
        self.minsize(820, 560)
        self.key = None
        self.dirty = False
        self._build()
        if path:
            self.open_path(path)
        else:
            self.set_status('Open a key dump, or File → New key to generate one.')

    # ------------------------------------------------------------------ chrome

    def _build(self):
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill='x')
        ttk.Button(bar, text='Open…', command=self.cmd_open).pack(side='left')
        ttk.Button(bar, text='New…', command=self.cmd_new).pack(side='left', padx=(6, 0))
        ttk.Button(bar, text='Save as…', command=self.cmd_save).pack(side='left', padx=(6, 0))
        ttk.Separator(bar, orient='vertical').pack(side='left', fill='y', padx=10)
        ttk.Button(bar, text='Change button serial…',
                   command=self.cmd_retarget).pack(side='left')
        ttk.Button(bar, text='Fix checksum', command=self.cmd_fix).pack(side='left', padx=(6, 0))
        ttk.Button(bar, text='Verify', command=self.cmd_verify).pack(side='left', padx=(6, 0))

        self.hdr = ttk.Label(self, padding=(10, 4), font=('TkDefaultFont', 10, 'bold'))
        self.hdr.pack(fill='x')

        self.nb = ttk.Notebook(self, padding=6)
        self.nb.pack(fill='both', expand=True)
        self.tab_fields = self._tab_fields()
        self.tab_options = self._tab_options()
        self.tab_games = self._tab_games()
        self.tab_raw = self._tab_raw()

        self.status = ttk.Label(self, padding=(10, 4), relief='sunken', anchor='w')
        self.status.pack(fill='x')

    def _tree(self, parent, cols, widths, stretch=None):
        frame = ttk.Frame(parent)
        tv = ttk.Treeview(frame, columns=cols, show='headings', selectmode='browse')
        for c, w in zip(cols, widths):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor='w',
                      stretch=(c == stretch) if stretch else False)
        sb = ttk.Scrollbar(frame, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        frame.pack(fill='both', expand=True)
        return tv

    def _tab_fields(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text='Fields')
        self.tv_fields = self._tree(f, ('field', 'value', 'offset', 'note'),
                                    (220, 330, 80, 300), stretch='note')
        self.tv_fields.bind('<Double-1>', self.edit_field)
        ttk.Label(f, padding=(4, 4), foreground='#555',
                  text='Double-click a row to change it. Read-only rows are derived values.'
                  ).pack(anchor='w')
        return f

    def _tab_options(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text='Options')
        self.opt_src = ttk.Label(f, padding=(4, 2), foreground='#555', justify='left')
        self.opt_src.pack(anchor='w', fill='x')
        frame = ttk.Frame(f)
        tv = ttk.Treeview(frame, columns=('#', 'option', 'state', 'what it does'),
                          show='tree headings', selectmode='browse')
        tv.column('#0', width=18, stretch=False)
        for c, w, st in (('#', 52, False), ('option', 270, False), ('state', 170, False),
                         ('what it does', 520, True)):
            tv.heading(c, text=c)
            tv.column(c, width=w, anchor='w', stretch=st)
        tv.tag_configure('group', font=('TkDefaultFont', 9, 'bold'), background='#e8eef4')
        tv.tag_configure('locked', foreground='#666')
        sb = ttk.Scrollbar(frame, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        frame.pack(fill='both', expand=True)
        self.tv_opts = tv
        tv.bind('<Double-1>', self.edit_option)
        tv.bind('<<TreeviewSelect>>', self.show_option_detail)
        self.opt_detail = tk.Text(f, height=5, wrap='word', relief='flat', background='#f6f6f2',
                                  font=('TkDefaultFont', 9), padx=6, pady=4)
        self.opt_detail.pack(fill='x', padx=2, pady=(4, 0))
        self.opt_detail.configure(state='disabled')
        row = ttk.Frame(f, padding=(4, 4))
        row.pack(anchor='w', fill='x')
        ttk.Label(row, foreground='#555',
                  text='Double-click to change. 0 locked off, 1 forced on, '
                       '2/3 operator-selectable (default off / on).').pack(side='left')
        ttk.Button(row, text='All selectable',
                   command=lambda: self.bulk_options(2)).pack(side='right')
        ttk.Button(row, text='All off',
                   command=lambda: self.bulk_options(0)).pack(side='right', padx=6)
        return f

    def _tab_games(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text='Games')
        top = ttk.Frame(f, padding=(4, 2))
        top.pack(anchor='w', fill='x')
        ttk.Label(top, text='Game names from:').pack(side='left')
        self.v_table = tk.StringVar()
        self.cb_table = ttk.Combobox(top, textvariable=self.v_table, state='readonly', width=48)
        self.cb_table.pack(side='left', padx=6)
        self.cb_table.bind('<<ComboboxSelected>>', self.pick_table)
        self.table_note = ttk.Label(top, foreground='#8a5a00')
        self.table_note.pack(side='left', padx=6)
        self.tv_games = self._tree(f, ('id', 'game', 'on', 'price', 'continue', 'notes'),
                                   (60, 300, 50, 70, 70, 260), stretch='notes')
        self.tv_games.bind('<Double-1>', self.edit_game)
        row = ttk.Frame(f, padding=(4, 4))
        row.pack(anchor='w', fill='x')
        self.games_hint = ttk.Label(row, foreground='#555')
        self.games_hint.pack(side='left')
        self.tv_games.bind('<space>', self.toggle_game)
        self.show_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text='also show unnamed slots',
                        variable=self.show_all,
                        command=self.refresh_games).pack(side='right', padx=8)
        return f

    def _tab_raw(self):
        f = ttk.Frame(self.nb)
        self.nb.add(f, text='Raw plaintext')
        self.raw = tk.Text(f, wrap='none', font=('Consolas', 9))
        sb = ttk.Scrollbar(f, orient='vertical', command=self.raw.yview)
        self.raw.configure(yscrollcommand=sb.set)
        self.raw.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        return f

    def set_status(self, text):
        self.status.configure(text=text)

    # ------------------------------------------------------------------ commands

    def cmd_open(self):
        start = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'Key Info & Dumps')
        p = filedialog.askopenfilename(
            title='Open a Megatouch key dump',
            initialdir=start if os.path.isdir(start) else None,
            filetypes=[('Key dumps', '*_full_* *_encrypted_* *.bin *.key'), ('All files', '*')])
        if p:
            self.open_path(p)

    def open_path(self, path):
        """Load a key. On any failure the previously loaded key is left untouched and the
        failure is reported - never silently ignored."""
        if not os.path.isfile(path):
            self.fail('No such file: %s' % path)
            return False
        try:
            key = L.Key.load(path)
        except Exception as first:
            try:
                key = self._open_hard(path, first)
            except Exception as e:
                self.fail('Could not open %s: %s' % (os.path.basename(path), e))
                return False
            if key is None:
                self.fail('Could not open %s: %s' % (os.path.basename(path), first))
                return False
        self.key = key
        self.dirty = False
        self.refresh_all()
        errs = [m for lvl, m in key.serial_report() if lvl == 'error'] if key.has_serial() else []
        self.set_status('Opened %s%s' % (path, ('   - WARNING: ' + errs[0]) if errs else ''))
        return True

    def fail(self, msg):
        """Report a failure loudly and say what is still on screen."""
        if self.key is not None:
            msg += '   (still showing the previously loaded key: %s)' % self.key.summary()
        self.set_status(msg)
        messagebox.showerror('Could not open key', msg)

    def _open_hard(self, path, first):
        """Fallbacks: recover the serial from the cipher, or ask for a version hint."""
        try:
            raw = open(path, 'rb').read()
        except OSError:
            return None     # open_path reports it
        for off in (0, 1024, 2048, 6144):
            if len(raw) >= off + 1024:
                hits = L.recover_gen4_serial(raw[off:off + 1024])
                if hits:
                    ver, ser, dec = hits[0]
                    if messagebox.askyesno(
                            'Serial recovered',
                            'This file carries no button serial, but the cipher reveals one.\n\n'
                            'Version: %s\nSerial:  %s\n\nOpen it with that serial?'
                            % (ver, ser)):
                        k = L.Key(4, ver, 'DS1996' if len(raw) != 2048 else 'DS1995',
                                  ser, dec, path=path)
                        k.memory = bytearray(raw) if len(raw) in (2048, 8192) else None
                        return k
                    return None
        ver = simpledialog.askstring(
            'Which release?',
            'Could not identify this key automatically:\n%s\n\n'
            'If its part number was edited, name the release:\n%s'
            % (first, ', '.join(L.all_versions())), parent=self)
        if not ver:
            return None
        try:
            return L.Key.load(path, version=ver)
        except Exception as e:
            messagebox.showerror('Still cannot open', str(e))
            return None

    def cmd_new(self):
        dlg = NewKeyDialog(self)
        if dlg.result:
            version, serial = dlg.result
            try:
                self.key = L.Key.new(version, serial)
            except Exception as e:
                messagebox.showerror('Cannot generate', str(e))
                return
            self.dirty = True
            self.refresh_all()
            self.set_status('Generated a blank %s key for serial %s' % (version, serial))

    def cmd_save(self):
        if not self.key:
            return
        plain = messagebox.askyesno(
            'Save which form?',
            'Yes  – save the ENCRYPTED button image (what you flash)\n'
            'No   – save the DECRYPTED plaintext instead',
            icon='question', default='yes')
        plaintext = not plain
        name = '%s_%s%s' % (
            self.key.version.replace(' ', ''),
            'plain' if plaintext else 'full',
            '' if plaintext else '_' + (self.key.serial or 'NOSERIAL'))
        p = filedialog.asksaveasfilename(title='Save key', initialfile=name)
        if not p:
            return
        try:
            if not plaintext and self.key.gen == 4 and not self.key.checksum_ok():
                self.key.fix_checksum()
            sha = self.key.save(p, plaintext=plaintext)
            ok = self.key.verify_roundtrip() if not plaintext else True
        except Exception as e:
            messagebox.showerror('Cannot save', str(e))
            return
        self.dirty = False
        self.refresh_all()
        self.set_status('Wrote %s  (sha256 %s…)  round-trip %s'
                        % (p, sha[:16], 'verified' if ok else 'FAILED'))

    def cmd_retarget(self):
        if not self.key:
            return
        dlg = SerialDialog(self, self.key.version, self.key.serial)
        if not dlg.result:
            return
        s = dlg.result
        table = self.key.name_table()
        self.key = self.key.retarget(s)
        self.key.set_name_table(table)
        self.dirty = True
        self.refresh_all()
        bad = [m for lvl, m in L.check_serial(self.key.version, s) if lvl == 'error']
        self.set_status('Re-keyed to button serial %s%s' % (
            s, '  - WARNING: %s would reject this button' % self.key.version if bad else ''))

    def cmd_fix(self):
        if not self.key:
            return
        if self.key.gen != 4:
            messagebox.showinfo('No checksum', 'Only Gen 4 keys (Force/ION 2007+) carry a '
                                               'checksum.')
            return
        self.key.fix_checksum()
        self.dirty = True
        self.refresh_all()
        self.set_status('Checksum recomputed.')

    def cmd_verify(self):
        """Re-encrypt, decrypt again, and report every integrity signal we can check."""
        if not self.key:
            return
        k = self.key
        lines = ['%s, generation %d, %s' % (k.version, k.gen, k.container),
                 'button serial: %s' % (k.serial or '(none)')]
        try:
            lines.append('encrypt/decrypt round-trip: %s'
                         % ('byte-exact' if k.verify_roundtrip() else 'MISMATCH'))
        except Exception as e:
            lines.append('round-trip: failed (%s)' % e)
        if k.gen == 4:
            lines.append('checksum: stored %04X, computed %04X – %s'
                         % (k.stored_checksum(), k.checksum(),
                            'OK' if k.checksum_ok() else 'MISMATCH'))
            sig = bytes(k.plain[0xF5:0xFD]).hex().upper()
            exp = L.GEN4_SIGS.get(L.gen4_code(k.version))
            lines.append('signature: %s%s' % (sig, '' if not exp else
                                              (' – matches %s' % k.version if sig == exp
                                               else ' – expected %s' % exp)))
        else:
            g, cs, ps, sig, pn = L.DS1991_VERSIONS[k.version]
            got = (bytes(k.plain[L.D0 + 0x28:L.D0 + 0x30]) if g == 3
                   else bytes(k.plain[L.D0:L.D0 + 8])).hex().upper()
            lines.append('signature: %s%s' % (got, '' if not sig else
                                              (' – matches %s' % k.version if got == sig
                                               else ' – expected %s' % sig)))
            lines.append('cipher %s, password set %s' % (cs, ps))
            if k.passwords:
                import mtpass
                regen = [bytes(x) for x in mtpass.passwords(k.serial, ps)]
                same = regen == [bytes(x) for x in k.passwords]
                lines.append('stored passwords match the generator: %s'
                             % ('yes' if same else 'no (they will be replaced on save)'))
        lines.append('')
        lines.append('button serial vs %s:' % k.version)
        for lvl, msg in k.serial_report():
            lines.append('  %s %s' % (LEVEL_MARK[lvl], msg))
        lines.append('')
        lines.append('options on/off/selectable: %d / %d / %d'
                     % (sum(1 for _, _, st in k.options() if st == 1),
                        sum(1 for _, _, st in k.options() if st == 0),
                        sum(1 for _, _, st in k.options() if st in (2, 3))))
        lines.append('games enabled: %d of %d slots'
                     % (sum(1 for g, n, on, pr, cc in k.games() if on), k.game_count()))
        messagebox.showinfo('Verify', '\n'.join(lines))

    # ------------------------------------------------------------------ refresh

    def refresh_all(self):
        k = self.key
        if not k:
            return
        mark = ' • modified' if self.dirty else ''
        self.hdr.configure(text=k.summary() + mark)
        self.refresh_fields()
        self.refresh_options()
        self.refresh_games()
        self.refresh_raw()
        nopt = sum(1 for _, _, st in k.options() if st)
        ngame = sum(1 for g, n, on, pr, cc in k.games() if on)
        self.nb.tab(1, text='Options (%d of %d set)' % (nopt, k.option_count()))
        self.nb.tab(2, text='Games (%d on)' % ngame)

    def refresh_fields(self):
        tv = self.tv_fields
        tv.delete(*tv.get_children())
        for f in self.key.fields():
            tv.insert('', 'end', values=(
                f.name, f.value,
                '' if f.offset < 0 else '0x%03X' % f.offset,
                f.note + ('' if f.kind != 'ro' else '  (read-only)')))

    GROUP_ORDER = ('menu', 'key', 'runtime', 'remote', 'unused', 'untraced', 'unknown')

    def refresh_options(self):
        tv = self.tv_opts
        tv.delete(*tv.get_children())
        k = self.key
        src = k.option_class_source()
        if src:
            build, how, text = src
            how_txt = {'own': "this release's own menus", 'same binary': 'same binary as this release',
                       'nearest': 'nearest analysed release - treat as a guide'}[how]
            extra = ('' if not build.startswith('DOS_') else
                     ' DOS: only slots the menus address directly are confirmed; the rest are not traced.')
            self.opt_src.configure(text='Menu vs key-only split from %s (%s). %d option slots on this key.%s'
                                        % (text, how_txt, k.option_count(), extra))
        else:
            self.opt_src.configure(text='%s menus were not traced, so options are not split into menu '
                                        'and key-only. Slot names come from the later Linux/ION builds, '
                                        'which use the same table.' % k.version)
        state_txt = dict((v, t) for t, v in OPT_STATES)
        groups = {}
        for i, label, st in k.options():
            info = k.option_info(i)
            groups.setdefault(info['cls'], []).append((i, label, st, info))
        for cls in self.GROUP_ORDER:
            items = groups.get(cls)
            if not items:
                continue
            gid = 'grp-' + cls
            tv.insert('', 'end', iid=gid, open=True, tags=('group',),
                      values=('', '%s  (%d)' % (L.OPTION_CLASS_LABEL[cls], len(items)), '', ''))
            for i, label, st, info in items:
                tags = ('locked',) if st in (0, 1) else ()
                tv.insert(gid, 'end', iid='opt-%d' % i, tags=tags,
                          values=('0x%02X' % i, label, state_txt.get(st, str(st)),
                                  info['desc'].split('. ')[0].rstrip('.') + '.'))
        self.show_option_detail()

    def show_option_detail(self, _evt=None):
        t = self.opt_detail
        t.configure(state='normal')
        t.delete('1.0', 'end')
        sel = self.tv_opts.selection()
        if sel and sel[0].startswith('opt-') and self.key:
            i = int(sel[0][4:])
            e = self.key.option_info(i)
            t.insert('end', '0x%02X  %s' % (i, e['label']), ('b',))
            t.insert('end', '   [%s]\n' % e['cls_label'])
            t.insert('end', e['desc'] + '\n')
            src = "Merit's operator-menu help text" if e['source'] == 'merit' else \
                'written from the code that reads/writes the slot'
            t.insert('end', 'Description: %s.   Merit name: %s' % (src, e['enum'] or '-'))
            if e.get('crown_note'):
                t.insert('end', '\nNote: ' + e['crown_note'])
        else:
            t.insert('end', 'Select an option to see what it does.')
        t.tag_configure('b', font=('TkDefaultFont', 9, 'bold'))
        t.configure(state='disabled')

    def pick_table(self, _evt=None):
        if not self.key:
            return
        label = self.v_table.get()
        for tid, lab in self.key.name_tables():
            if lab == label:
                self.key.set_name_table(tid)
        self.refresh_games()
        self.set_status('Game names now from %s.' % label)

    def refresh_games(self):
        tv = self.tv_games
        tv.delete(*tv.get_children())
        k = self.key
        tables = k.name_tables()
        self.cb_table.configure(values=[lab for _, lab in tables])
        cur = k.name_table()
        self.v_table.set(next((lab for t, lab in tables if t == cur), 'none'))
        self.table_note.configure(
            text='(nearest available - this release\'s own game table is not in the collection)'
            if k.names_are_nearest() else '')
        lay = k.layout()
        hint = {'dos': 'Value = the key\'s per-game number: 0 = game not on the key; on Diamond-era '
                       'keys it is the price per play.',
                'ruby': 'Unlisted games are on at the default price (Fields tab).',
                'sapphire': 'Games not in the price list cost the default price (Fields tab).',
                'crown': 'Games not in the price list cost the default price (Fields tab).',
                'gen4': 'Price = credits per player, continue = continue cost.'}[lay]
        self.games_hint.configure(text='Double-click to change, Space toggles. ' + hint)
        tv.heading('price', text='value' if lay == 'dos' else 'price')
        every = self.show_all.get()
        for gid, name, on, price, cc in k.games():
            if not every and not on and name.startswith('game 0x'):
                continue
            flags = ', '.join(x.replace('_', ' ') for x in k.game_flags(gid))
            tv.insert('', 'end', values=('0x%02X' % gid, name, 'yes' if on else '',
                                         'default' if price is None else price,
                                         cc if k.gen == 4 else '', flags))

    def refresh_raw(self):
        self.raw.configure(state='normal')
        self.raw.delete('1.0', 'end')
        p = bytes(self.key.plain)
        lines = []
        for o in range(0, len(p), 16):
            chunk = p[o:o + 16]
            lines.append('%04X  %-47s  %s' % (
                o, ' '.join('%02x' % c for c in chunk),
                ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk)))
        self.raw.insert('1.0', '\n'.join(lines))
        self.raw.configure(state='disabled')

    # ------------------------------------------------------------------ editing

    def edit_field(self, _evt):
        sel = self.tv_fields.selection()
        if not sel or not self.key:
            return
        name = self.tv_fields.item(sel[0], 'values')[0]
        field = next((f for f in self.key.fields() if f.name == name), None)
        if field is None:
            return
        if field.kind == 'ro' or field.offset < 0:
            self.set_status('%s is derived, not stored - nothing to edit.' % name)
            return
        if field.kind == 'bool':
            self.key.set(field, not field.value)
        else:
            v = simpledialog.askstring('Edit %s' % name,
                                       '%s\n%s' % (name, field.note or ''),
                                       initialvalue=str(field.value), parent=self)
            if v is None:
                return
            try:
                self.key.set(field, v)
            except Exception as e:
                messagebox.showerror('Cannot set %s' % name, str(e))
                return
        self.dirty = True
        self.refresh_all()
        self.set_status('%s updated.' % name)

    def edit_option(self, _evt):
        sel = self.tv_opts.selection()
        if not sel or not self.key or not sel[0].startswith('opt-'):
            return
        vals = self.tv_opts.item(sel[0], 'values')
        idx = int(sel[0][4:])
        info = self.key.option_info(idx)
        dlg = ChoiceDialog(self, 'Option 0x%02X' % idx,
                           '%s\n\n%s\n\n[%s]' % (info['label'], info['desc'], info['cls_label']),
                           [t for t, _ in OPT_STATES], self.key.option(idx))
        if dlg.result is None:
            return
        self.key.set_option(idx, OPT_STATES[dlg.result][1])
        self.dirty = True
        self.refresh_all()
        self.set_status('Option 0x%02X (%s) set to %d.'
                        % (idx, vals[1], OPT_STATES[dlg.result][1]))

    def bulk_options(self, state):
        if not self.key or not self.key.option_count():
            return
        if not messagebox.askyesno('Set every option',
                                   'Set all %d option slots to %d?'
                                   % (self.key.option_count(), state)):
            return
        for i in range(self.key.option_count()):
            self.key.set_option(i, state)
        self.dirty = True
        self.refresh_all()
        self.set_status('All options set to %d.' % state)

    def toggle_game(self, _evt):
        sel = self.tv_games.selection()
        if not sel or not self.key:
            return
        gid = int(self.tv_games.item(sel[0], 'values')[0], 16)
        on = self.key.game(gid)[0]
        try:
            self.key.set_game(gid, enabled=not on)
        except ValueError as e:
            messagebox.showerror('Cannot change game 0x%02X' % gid, str(e))
            return
        self.dirty = True
        self.refresh_all()
        self.set_status('Game 0x%02X %s.' % (gid, 'disabled' if on else 'enabled'))

    def edit_game(self, _evt):
        sel = self.tv_games.selection()
        if not sel or not self.key:
            return
        vals = self.tv_games.item(sel[0], 'values')
        gid = int(vals[0], 16)
        dlg = GameDialog(self, gid, vals[1], self.key.game(gid), self.key.gen == 4)
        if dlg.result is None:
            return
        on, price, cc = dlg.result
        try:
            self.key.set_game(gid, enabled=on, price=price,
                              continue_cost=cc if self.key.gen == 4 else None)
        except ValueError as e:
            messagebox.showerror('Cannot change game 0x%02X' % gid, str(e))
            return
        self.dirty = True
        self.refresh_all()
        self.set_status('Game 0x%02X (%s) updated.' % (gid, vals[1]))


class ChoiceDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt, choices, initial):
        self.prompt, self.choices, self.initial = prompt, choices, initial
        self.result = None
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text=self.prompt, wraplength=360).pack(anchor='w', pady=(0, 8))
        self.var = tk.IntVar(value=self.initial)
        for i, c in enumerate(self.choices):
            ttk.Radiobutton(master, text=c, value=i, variable=self.var).pack(anchor='w')

    def apply(self):
        self.result = self.var.get()


class GameDialog(simpledialog.Dialog):
    def __init__(self, parent, gid, name, cur, gen4):
        self.gid, self.name, self.cur, self.gen4 = gid, name, cur, gen4
        self.result = None
        super().__init__(parent, 'Game 0x%02X' % gid)

    def body(self, master):
        on, price, cc = self.cur
        ttk.Label(master, text=self.name, wraplength=340,
                  font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=0, columnspan=2,
                                                           sticky='w', pady=(0, 8))
        self.v_on = tk.BooleanVar(value=bool(on))
        ttk.Checkbutton(master, text='enabled on this key',
                        variable=self.v_on).grid(row=1, column=0, columnspan=2, sticky='w')
        ttk.Label(master, text='price per player (0-15, blank = leave)').grid(
            row=2, column=0, sticky='w', pady=(8, 0))
        self.v_price = tk.StringVar(value='' if price is None else str(price))
        ttk.Entry(master, textvariable=self.v_price, width=8).grid(row=2, column=1, sticky='w',
                                                                  pady=(8, 0))
        if self.gen4:
            ttk.Label(master, text='continue cost (0-15)').grid(row=3, column=0, sticky='w')
            self.v_cc = tk.StringVar(value=str(cc))
            ttk.Entry(master, textvariable=self.v_cc, width=8).grid(row=3, column=1,
                                                                    sticky='w')

    def apply(self):
        try:
            p = self.v_price.get().strip()
            price = max(0, min(15, int(p))) if p else None
            cc = max(0, min(15, int(self.v_cc.get()))) if self.gen4 else 0
        except ValueError:
            return
        self.result = (self.v_on.get(), price, cc)


LEVEL_MARK = {'ok': '✓', 'warn': '!', 'error': '✗'}


class SerialDialog(simpledialog.Dialog):
    """Enter a button serial; checks the CRC, the family and the release's laser-serial window
    live, offers to fix the CRC or suggest a serial the release accepts."""

    def __init__(self, parent, version, current):
        self.version, self.current = version, current or ''
        self.result = None
        super().__init__(parent, 'Button serial for %s' % version)

    def body(self, master):
        ttk.Label(master, justify='left', wraplength=520,
                  text='1-Wire serial, 16 hex digits in printed order (CRC first … family last), '
                       'e.g. 0900400002B65782. The key contents are kept; the cipher and the DS1991 '
                       'passwords are regenerated for this serial.').grid(row=0, column=0, columnspan=3,
                                                                          sticky='w')
        self.v = tk.StringVar(value=self.current)
        e = ttk.Entry(master, textvariable=self.v, width=26, font=('Consolas', 11))
        e.grid(row=1, column=0, sticky='w', pady=8)
        ttk.Button(master, text='Fix CRC', command=self.fix).grid(row=1, column=1, padx=6)
        ttk.Button(master, text='Suggest a valid serial', command=self.suggest).grid(row=1, column=2)
        self.out = tk.Text(master, width=72, height=7, wrap='word', relief='flat',
                           background='#f6f6f2', font=('TkDefaultFont', 9))
        self.out.grid(row=2, column=0, columnspan=3, sticky='we')
        self.out.tag_configure('error', foreground='#a00000')
        self.out.tag_configure('warn', foreground='#8a5a00')
        self.out.tag_configure('ok', foreground='#1f6b2a')
        self.v.trace_add('write', lambda *a: self.check())
        self.check()
        return e

    def _clean(self):
        return ''.join(c for c in self.v.get() if c in '0123456789abcdefABCDEF').upper()

    def check(self):
        self.out.configure(state='normal')
        self.out.delete('1.0', 'end')
        for lvl, msg in L.check_serial(self.version, self._clean()):
            self.out.insert('end', '%s %s\n' % (LEVEL_MARK[lvl], msg), (lvl,))
        self.out.configure(state='disabled')

    def fix(self):
        try:
            self.v.set(L.fix_crc(self._clean()))
        except ValueError as e:
            messagebox.showerror('Bad serial', str(e), parent=self)

    def suggest(self):
        self.v.set(L.suggest_serial(self.version))

    def validate(self):
        s = self._clean()
        if len(s) != 16:
            messagebox.showerror('Bad serial', 'Need exactly 16 hex digits.', parent=self)
            return False
        errs = [m for lvl, m in L.check_serial(self.version, s) if lvl == 'error']
        if errs:
            return messagebox.askyesno(
                'This release would reject the button',
                '\n\n'.join(errs) + '\n\nUse this serial anyway? (Only useful for a patched or keyless '
                                    'machine.)', icon='warning', default='no', parent=self)
        return True

    def apply(self):
        self.result = self._clean()


class NewKeyDialog(simpledialog.Dialog):
    def __init__(self, parent):
        self.result = None
        super().__init__(parent, 'Generate a new key')

    def body(self, master):
        ttk.Label(master, text='Release').grid(row=0, column=0, sticky='w')
        self.v_ver = tk.StringVar(value='ION 2014')
        cb = ttk.Combobox(master, textvariable=self.v_ver, width=28, state='readonly',
                          values=L.all_versions())
        cb.grid(row=0, column=1, sticky='w', padx=6)
        ttk.Label(master, text='Button serial (16 hex, printed order)').grid(
            row=1, column=0, sticky='w', pady=(8, 0))
        self.v_ser = tk.StringVar(value=L.suggest_serial('ION 2014'))
        ttk.Entry(master, textvariable=self.v_ser, width=30).grid(row=1, column=1, sticky='w',
                                                                  padx=6, pady=(8, 0))
        ttk.Button(master, text='Suggest', command=self.suggest).grid(row=1, column=2, pady=(8, 0))
        cb.bind('<<ComboboxSelected>>', lambda e: self.suggest())
        ttk.Label(master, foreground='#555', wraplength=420, justify='left',
                  text='Family byte comes last: 0x02 or 0x82 for the DS1991 releases, '
                       '0x0A/0x8C for the DS1995/DS1996 ones (Force/ION 2007+). '
                       'A real DS1991 serial cannot be changed, so a generated serial is '
                       'for an emulator or a 1-Wire emulator only.'
                  ).grid(row=2, column=0, columnspan=3, sticky='w', pady=(10, 0))

    def validate(self):
        s = ''.join(c for c in self.v_ser.get() if c in '0123456789abcdefABCDEF').upper()
        if len(s) != 16:
            messagebox.showerror('Bad serial', 'Need exactly 16 hex digits.', parent=self)
            return False
        errs = [m for lvl, m in L.check_serial(self.v_ver.get(), s) if lvl == 'error']
        if errs:
            return messagebox.askyesno(
                'This release would reject the button',
                '\n\n'.join(errs) + '\n\nUse it anyway? "Suggest" picks one the release accepts.',
                icon='warning', default='no', parent=self)
        return True

    def suggest(self):
        self.v_ser.set(L.suggest_serial(self.v_ver.get()))

    def apply(self):
        s = ''.join(c for c in self.v_ser.get() if c in '0123456789abcdefABCDEF').upper()
        self.result = (self.v_ver.get(), s)


def selftest(out_path, key_path):
    """--selftest OUT KEY: open KEY in the real window, write what the tabs show to OUT (JSON) and
    exit - lets a build check the packaged .exe without anyone clicking."""
    import json
    app = App()
    app.withdraw()
    messagebox.showerror = lambda *a, **k: None
    res = {'opened': bool(app.open_path(key_path)), 'data_loaded': bool(L.OPTION_CATALOG) and
           bool(L.GAME_TABLES)}
    if res['opened']:
        k = app.key
        res.update(version=k.version, options=k.option_count(),
                   groups=list(app.tv_opts.get_children()),
                   games_shown=len(app.tv_games.get_children()),
                   unnamed=sum(1 for i in app.tv_games.get_children()
                               if app.tv_games.item(i, 'values')[1].startswith('game 0x')),
                   serial=[lvl for lvl, _ in k.serial_report()],
                   roundtrip=k.verify_roundtrip())
    app.destroy()
    with open(out_path, 'w') as f:
        json.dump(res, f)
    return 0 if res['opened'] and res['data_loaded'] else 1


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--selftest':
        sys.exit(selftest(sys.argv[2], sys.argv[3]))
    path = sys.argv[1] if len(sys.argv) > 1 else None
    App(path).mainloop()


if __name__ == '__main__':
    main()
