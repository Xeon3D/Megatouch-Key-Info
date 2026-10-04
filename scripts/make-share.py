"""make-share.py - build standalone, shareable HTML files (open in any browser, no claude.ai needed).

usage: make-share.py <published page .html> <keyinfo-human.md> <out_dir>
  1. <out_dir>/megatouch-security-keys.html : the "Megatouch Security Keys" page wrapped as a full document
  2. <out_dir>/megatouch-keys-guide.html    : keyinfo-human.md rendered with the same stylesheet
Fonts load from Google Fonts when online and fall back to system fonts offline.
"""
import sys, os, re, html

page_src, md_src, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
page = open(page_src, encoding='utf-8').read()

RESET = ('<style>*,*::before,*::after{box-sizing:border-box}body{margin:0}img{max-width:100%}'
         '[hidden]{display:none!important}@media print{nav.toc{display:none}.tbl{overflow:visible}}</style>\n')
def document(head_and_body):
    """Split '<title>/<link>/<style>' head material from body markup and wrap it."""
    i = head_and_body.index('</style>') + len('</style>')
    head, body = head_and_body[:i], head_and_body[i:]
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            + RESET + head + '\n</head>\n<body>\n' + body.strip() + '\n</body>\n</html>\n')

_page_out = document(page)
open(os.path.join(out, 'megatouch-security-keys.html'), 'w', encoding='utf-8').write(_page_out)

# ---- minimal Markdown -> HTML for keyinfo-human.md (headings, paragraphs, nested lists, tables, code) ----
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*]+)\*(?!\*)', r'<em>\1</em>', t)
    return t

def slug(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

lines = open(md_src, encoding='utf-8').read().splitlines()
title = lines[0].lstrip('# ').strip()
body, toc, i, intro = [], [], 1, []
# intro paragraph(s) before the first '---' become the lede
while i < len(lines) and lines[i].strip() != '---':
    if lines[i].strip(): intro.append(lines[i].strip())
    i += 1

def parse_list(i, indent):
    out = []; tag = None
    while i < len(lines):
        l = lines[i]
        m = re.match(r'^( *)([-*]|\d+\.) (.*)$', l)
        if not m or len(m.group(1)) < indent: break
        if len(m.group(1)) > indent:
            sub, i = parse_list(i, len(m.group(1)))
            out[-1] = out[-1][:-5] + sub + '</li>'; continue
        tag = tag or ('ol' if m.group(2)[0].isdigit() else 'ul')
        text = m.group(3); i += 1
        while i < len(lines) and lines[i].strip() and lines[i].startswith(' ' * (indent + 2)) \
                and not re.match(r'^ *([-*]|\d+\.) ', lines[i]):
            text += ' ' + lines[i].strip(); i += 1
        out.append(f'<li>{inline(text)}</li>')
    return f'<{tag} class="plain">' + ''.join(out) + f'</{tag}>', i

open_section = False
while i < len(lines):
    l = lines[i]
    if not l.strip() or l.strip() == '---': i += 1; continue
    if l.startswith('## '):
        h = l[3:].strip(); sid = slug(re.sub(r'^\d+\.\s*', '', h))
        if open_section: body.append('</section>')
        body.append(f'<section id="{sid}">\n<div class="sec-head"><h2>{inline(h)}</h2></div>')
        toc.append((sid, re.sub(r'^\d+\.\s*', '', h))); open_section = True; i += 1; continue
    if l.startswith('### '):
        body.append(f'<h3>{inline(l[4:].strip())}</h3>'); i += 1; continue
    if l.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
        head, rest = rows[0], [r for r in rows[2:]]
        t = '<div class="tbl"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
        t += ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rest)
        body.append(t + '</tbody></table></div>'); continue
    if re.match(r'^([-*]|\d+\.) ', l):
        lst, i = parse_list(i, 0); body.append(lst); continue
    para = [l.strip()]; i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||[-*] |\d+\. |---)', lines[i]):
        para.append(lines[i].strip()); i += 1
    body.append(f'<p>{inline(" ".join(para))}</p>')
if open_section: body.append('</section>')

i0 = page.index('<link rel="preconnect"')
# the source page may already carry an earlier reset <style> block, so look for the
# closing tag AFTER the font links rather than the first one in the file
style = page[i0: page.index('</style>', i0) + len('</style>')]
style = style.replace('</style>', 'section h3 { margin-top: 6px; }\nol.plain { padding-left: 1.6em; }\nul.plain ul.plain, ul.plain ol.plain { margin-top: 6px; }\np code, li code { overflow-wrap: anywhere; }\n</style>')
guide = (f'<title>{html.escape(title)}</title>\n' + style + '\n<div class="wrap">\n<header class="top">\n'
         '<div class="eyebrow">A guide for collectors, operators and preservationists</div>\n'
         f'<h1>{inline(title)}</h1>\n<p class="lede">{inline(" ".join(intro))}</p>\n'
         '<div class="meta"><span>XL R1 (1997) to ION 2014</span><span>Maxx / XL and Force / ION</span><span>October 2026</span></div>\n</header>\n'
         '<nav class="toc">' + ''.join(f'<a href="#{s}">{html.escape(t)}</a>' for s, t in toc) + '</nav>\n'
         + '\n'.join(body) +
         '\n<footer><p>Based on static analysis of the original Megatouch software, decryption of keyflasher dumps, and '
         'tests in the MegaPPBox emulator. Builds on Nicholas Navaroli\'s keyflasher and keyless patches.</p></footer>\n</div>')
_out = document(guide)
open(os.path.join(out, 'megatouch-keys-guide.html'), 'w', encoding='utf-8').write(_out)
for f in ('megatouch-security-keys.html', 'megatouch-keys-guide.html'):
    p = os.path.join(out, f); print(f, os.path.getsize(p), 'bytes')
