"""Read the Company Calendar workbook back into the site's rehearsal data (what the nightly sync / Apps Script does).
python3 read_company_workbook.py Company_Calendar_Workbook_2026-27.xlsx out.json"""
import openpyxl, json, sys, re, datetime as dt
from make_company_workbook import kindOf
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
def rows(name):
    ws = wb[name]; head = [str(c.value or '').strip() for c in ws[2]]
    for r in ws.iter_rows(min_row=3, values_only=True):
        d = dict(zip(head, r))
        if d.get('Date') not in (None, ''): yield d
iso = lambda v: v.date().isoformat() if isinstance(v, dt.datetime) else (v.isoformat() if isinstance(v, dt.date) else str(v or '').strip())
def clock(v):
    if isinstance(v, dt.datetime): v = v.time()
    if isinstance(v, dt.time): return v.hour, v.minute
    m = re.fullmatch(r'\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*', str(v or ''), re.I)
    return (int(m.group(1)) % 12 + (12 if m.group(3).lower() == 'pm' else 0), int(m.group(2) or 0)) if m else None
def label(h, m): return str(h % 12 or 12) + (':%02d' % m if m else '')
def span(s, e):  # same short style as before: 8–10am, 10am–12pm, 2:30–4pm
    a, b = clock(s), clock(e)
    if not a: return ''
    ap = lambda h: 'am' if h < 12 else 'pm'
    if not b: return label(*a) + ap(a[0])
    return label(*a) + ('' if ap(a[0]) == ap(b[0]) else ap(a[0])) + '–' + label(*b) + ap(b[0])
reh = []
for r in rows('Rehearsals'):
    st = str(r.get('Studio') or '').strip(); what = str(r.get('Dancers or group') or '').strip()
    reh.append({'date': iso(r['Date']), 'time': span(r.get('Start'), r.get('End')) or str(r.get('Notes') or '').strip() or 'Time TBA',
                'room': ('Studio ' + st.upper()) if st.upper() in ('A', 'B', 'C') else st, 'what': what,
                'teacher': str(r.get('Teacher') or '').strip(), 'kind': str(r.get('Type') or '').strip() or kindOf(what)})
off = [{'date': iso(r['Date']), 'who': [x.strip() for x in str(r.get('Teacher') or 'All').split(',') if x.strip()]} for r in rows('No rehearsals')]
json.dump({'rehearsals': reh, 'off': off}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(reh), 'rehearsals,', len(off), 'days off')
