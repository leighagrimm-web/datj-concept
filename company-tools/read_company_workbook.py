"""Read the plain Company Calendar workbook back into the site's rehearsal + event data (what the nightly sync will do)."""
import openpyxl, json, sys, datetime as dt
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
def rows(name):
    ws = wb[name]; head = [str(c.value or '').strip() for c in ws[2]]
    for r in ws.iter_rows(min_row=3, values_only=True):
        if any(v not in (None, '') for v in r): yield dict(zip(head, r))
iso = lambda v: v.date().isoformat() if isinstance(v, dt.datetime) else (v.isoformat() if isinstance(v, dt.date) else str(v or ''))
short = lambda t: str(t or '').replace(':00', '').replace(' AM', 'am').replace(' PM', 'pm')
def span(s, e):
    s, e = short(s), short(e)
    if s and e and s[-2:] == e[-2:]: s = s[:-2]
    return (s + '–' + e) if s and e else (s or '')
reh = []
for r in rows('Rehearsals'):
    st = r.get('Studio') or ''
    reh.append({'date': iso(r['Date']), 'time': span(r.get('Start'), r.get('End')) or (r.get('Notes') or 'Time TBA'), 'room': ('Studio ' + st) if st else '', 'what': r.get('Routine / dancers') or '', 'teacher': r.get('Teacher') or '', 'kind': r.get('Type') or ''})
tmpl = list(rows('Weekly Saturdays'))
for d in rows('Weekly dates'):
    for t in tmpl:
        st = t.get('Studio') or ''
        reh.append({'date': iso(d['Date']), 'time': span(t.get('Start'), t.get('End')), 'room': ('Studio ' + st) if st else '', 'what': t.get('Routine / dancers') or '', 'teacher': t.get('Teacher') or '', 'kind': ''})
off = [{'date': iso(r['Date']), 'who': [x.strip() for x in str(r.get('Teacher') or 'All').split(',')]} for r in rows('No rehearsals')]
ev = []
for r in rows('Events'):
    secs, cur = [], None
    for line in str(r.get('Details') or '').split('\n'):
        line = line.strip()
        if line.startswith('## '): cur = {'h': line[3:], 'items': []}; secs.append(cur)
        elif line.startswith('- '):
            if not cur: cur = {'h': '', 'items': []}; secs.append(cur)
            cur['items'].append(line[2:])
    who = r.get('Who sees details') or 'Public'
    links = [{'label': r[k], 'url': r.get(k + ' link') or ''} for k in ('Button 1', 'Button 2') if r.get(k)]
    ev.append({'title': r['What'], 'start': iso(r['Start']), 'end': iso(r.get('End')) if r.get('End') else '', 'where': r.get('Where (short)') or '', 'type': r.get('Type') or 'Event',
               'lock': who != 'Public', 'hidden': who == 'Company Central only', 'info': {'when': r.get('Time') or '', 'where': r.get('Address') or '', 'summary': r.get('Summary (one or two sentences)') or '', 'sections': secs, 'links': links}})
json.dump({'rehearsals': reh, 'off': off, 'events': ev}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(reh), 'rehearsals,', len(off), 'days off,', len(ev), 'events')
