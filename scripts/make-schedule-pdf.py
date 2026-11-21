"""Build DATJ_Class_Schedule.pdf (2 landscape pages, site branding) from classes.json.
Runs nightly after the Studio Pro sync, so Brittany never has to make the PDF by hand.
Usage: python3 scripts/make-schedule-pdf.py  (needs: pip install playwright && playwright install chromium)"""
import json, re, html, os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, 'classes.json')))
# Teachers: the same list the website uses (kept in classes.html until Studio Pro sends it)
m = re.search(r'const TEACHER_BY_CLASS = (\{.*?\});', open(os.path.join(ROOT, 'classes.html')).read())
TEACH = json.loads(m.group(1)) if m else {}
COLORS = {'Kelly': '#0ED1E3', 'Katie': '#CC91FC', 'Meghan': '#FF85FF', 'Daniel': '#93C47D', 'Dillon': '#F6A54A',
          'Lauren': '#F7D154', 'Akanksha': '#F06292', 'Shetal': '#FF8A65', 'The Breaking Program': '#E5484D', 'Brittany': '#00ADB5'}
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
FULL = dict(zip(DAYS, ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']))
e = lambda s: html.escape(str(s or ''))

def clock(mins, ampm=True):
    h, mm = divmod(int(mins), 60); t = f'{(h + 11) % 12 + 1}:{mm:02d}'
    return t + (' ' + ('PM' if h >= 12 else 'AM') if ampm else '')
def span(c):
    if c.get('start') is None: return e(c.get('time'))
    s, en = c['start'], c.get('end') or c['start']
    same = (s >= 720) == (en >= 720)
    return clock(s, not same) + '–' + clock(en)
def ages(c):
    lo, hi = c.get('lo'), c.get('hi')
    if lo is None: return 'All ages'
    return f'Ages {lo}+' if (hi is None or hi >= 99) else f'Ages {lo}–{hi}'
def clean(n): return re.sub(r'\s+(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)$', '', n)

classes = [c for c in data['classes'] if not c.get('season') or re.search(r'session|summer|intensive|camp', c['season'], re.I)]
season = next((c['season'] for c in classes if c.get('season')), '')
upd = data.get('updated', '')[:10]
try: updTxt = datetime.date.fromisoformat(upd).strftime('%b %-d, %Y')
except Exception: updTxt = upd

def cell(c):
    t = TEACH.get(c['key'], '')
    col = COLORS.get(t, '#BBBBBB')
    note = (c.get('note') or '').split('\n')[0]
    return (f'<div class="cl" style="border-left-color: {col};"><div class="tm">{span(c)}</div><div class="nm">{e(clean(c["name"])).replace("/", "/&#8203;")}</div>'
            f'<div class="ag">{ages(c)}</div>' + (f'<div class="nt">{e(note)}</div>' if note else '')
            + (f'<div class="tc"><i style="background: {col};"></i>{e(t)}</div>' if t else '') + '</div>')

def day_block(d):
    cs = sorted([c for c in classes if c['day'] == d], key=lambda c: c.get('start') or 0)
    studios = sorted({c.get('studio') or 'Studio' for c in cs})
    if not studios: return '', 0
    cols = ''.join(f'<div class="st"><div class="sh">{e(s)}</div>' + ''.join(cell(c) for c in cs if (c.get('studio') or 'Studio') == s) + '</div>' for s in studios)
    return f'<div class="day" style="flex: {len(studios)};"><div class="dh">{FULL[d]}</div><div class="sts">{cols}</div></div>', len(studios)

used = sorted({TEACH.get(c['key'], '') for c in classes} - {''}, key=lambda t: (t == 'The Breaking Program', t))
legend = ''.join(f'<span><i style="background: {COLORS.get(t, "#BBBBBB")};"></i>{e(t)}</span>' for t in used)
LOGO = 'file://' + os.path.join(ROOT, 'logos', 'circle_teal.svg')
def page(days, n):
    blocks = ''.join(day_block(d)[0] for d in days)
    return f'''<section class="pg">
  <header><img src="{LOGO}" alt=""><div class="ttl"><div class="eye">Dance &amp; All That Jazz · {e(season)}</div><h1>2026–27 Class <em>Schedule.</em></h1></div>
  <div class="ad">844 N Elmhurst Rd, Prospect Heights, IL 60070<br>(847) 947-8464 · team@danceandallthatjazz.com<br><b>Page {n} of 2</b></div></header>
  <div class="grid">{blocks}</div>
  <footer><div class="lg"><b>Teachers</b>{legend}</div><div class="fn">Instructors place each dancer in the right level; ages are a guide. Classes may be cancelled based on enrollment. No refunds once enrolled. Your first class is free.<br><b>From Studio Pro · updated {e(updTxt)}</b> · Always current at danceandallthatjazz.com/classes</div></footer>
</section>'''

CSS = '''@page { size: 11in 8.5in; margin: 0; }
* { box-sizing: border-box; } body { margin: 0; font-family: Arial, Helvetica, sans-serif; color: #111111; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.pg { width: 11in; height: 8.5in; padding: 0.32in 0.36in 0.28in; display: flex; flex-direction: column; page-break-after: always; overflow: hidden; }
.pg:last-child { page-break-after: auto; }
header { display: flex; align-items: center; gap: 14px; background: #000000; color: #FFFFFF; padding: 10px 16px; border-bottom: 5px solid #00ADB5; }
header img { width: 46px; height: 46px; } .ttl { flex: 1; }
.eye { font-size: 8.5px; letter-spacing: 0.22em; text-transform: uppercase; font-weight: 700; color: #00ADB5; }
h1 { margin: 2px 0 0; font-size: 26px; letter-spacing: -0.045em; font-weight: 800; text-transform: uppercase; line-height: 1; }
h1 em { font-family: Georgia, serif; font-style: italic; font-weight: 400; text-transform: none; color: #00ADB5; letter-spacing: -0.03em; }
.ad { font-size: 9px; line-height: 1.5; color: #CBD2CF; text-align: right; } .ad b { color: #FFFFFF; letter-spacing: 0.14em; text-transform: uppercase; font-size: 8px; }
.grid { flex: 1; display: flex; gap: 10px; margin-top: 10px; min-height: 0; }
.day { display: flex; flex-direction: column; min-width: 0; }
.dh { font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; font-weight: 800; padding: 0 0 4px; border-bottom: 2px solid #111111; }
.sts { display: flex; gap: 5px; flex: 1; }
.st { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.sh { font-size: 7.5px; letter-spacing: 0.16em; text-transform: uppercase; font-weight: 700; color: #555555; padding: 4px 0 2px; }
.cl { background: #F2F2F2; border-left: 4px solid #BBBBBB; padding: 4px 5px 5px; }
.tm { font-size: 8.5px; font-weight: 800; white-space: nowrap; }
.nm { overflow: hidden; font-size: 9.5px; font-weight: 700; letter-spacing: -0.01em; line-height: 1.15; margin: 2px 0 1px; overflow-wrap: normal; word-break: normal; hyphens: none; }
.ag { font-size: 8px; color: #333333; } .nt { font-size: 7px; color: #007A80; line-height: 1.2; margin-top: 1px; }
.tc { font-size: 8px; font-weight: 700; margin-top: 2px; } .tc i, .lg i { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 3px; vertical-align: 0; }
footer { margin-top: 8px; padding-top: 6px; border-top: 1px solid #DDDDDD; display: flex; justify-content: space-between; gap: 18px; font-size: 8px; color: #555555; line-height: 1.45; }
.lg { display: flex; flex-wrap: wrap; gap: 3px 10px; max-width: 48%; } .lg b { color: #111111; letter-spacing: 0.14em; text-transform: uppercase; font-size: 7.5px; margin-right: 2px; } .lg span { white-space: nowrap; }
.fn { text-align: right; max-width: 52%; } .fn b { color: #111111; }'''

doc = f'<!doctype html><html><head><meta charset="utf-8"><title>Dance &amp; All That Jazz — Class Schedule</title><style>{CSS}</style></head><body>{page(DAYS[:3], 1)}{page(DAYS[3:], 2)}</body></html>'
out_html = os.path.join(ROOT, 'scripts', '_schedule.html'); open(out_html, 'w').write(doc)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto('file://' + out_html); pg.wait_for_timeout(300)
    # Grow the text to fill the page, or shrink it if a day is too tall: always exactly 2 pages
    fits = lambda: not pg.evaluate("() => [...document.querySelectorAll('.grid')].some(g => g.scrollHeight > g.clientHeight + 1 || g.scrollWidth > g.clientWidth + 1)")
    setz = lambda z: pg.evaluate("(z) => document.querySelectorAll('.grid').forEach(g => g.style.zoom = z)", z)
    z = 1.0
    while z < 1.7 and fits(): z += 0.04; setz(z)
    while z > 0.6 and not fits(): z -= 0.02; setz(z)
    # A long word (Contemporary) never splits: shrink just that class name until it fits its box
    pg.evaluate("() => document.querySelectorAll('.nm, .tc, .nt, .tm').forEach(el => { let f = parseFloat(getComputedStyle(el).fontSize); while (el.scrollWidth > el.clientWidth + 0.5 && f > 6) { f -= 0.25; el.style.fontSize = f + 'px'; } })")
    while z > 0.6 and not fits(): z -= 0.02; setz(z)
    pg.pdf(path=os.path.join(ROOT, 'DATJ_Class_Schedule.pdf'), width='11in', height='8.5in', print_background=True)
    b.close()
os.remove(out_html)
print('DATJ_Class_Schedule.pdf ·', len(classes), 'classes')
