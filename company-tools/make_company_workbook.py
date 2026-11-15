"""Company Calendar workbook in plain rows: what Brittany would type into from now on."""
import json, re, datetime as dt, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
co = json.load(open('company_plain.json')); cal = json.load(open('cal0.json'))
H = Font(bold=True, color='FFFFFF'); F = PatternFill('solid', fgColor='00ADB5'); W = Alignment(wrap_text=True, vertical='top')
wb = openpyxl.Workbook()
def sheet(ws, note, head, rows, widths):
    ws.append([note]); ws['A1'].font = Font(italic=True, color='555555'); ws.append(head)
    for c in ws[2]: c.font = H; c.fill = F
    for r in rows: ws.append(r)
    for i, w in enumerate(widths): ws.column_dimensions[openpyxl.utils.get_column_letter(i + 1)].width = w
    for row in ws.iter_rows(min_row=3):
        for c in row: c.alignment = W
    ws.freeze_panes = 'A3'; ws.auto_filter.ref = 'A2:' + openpyxl.utils.get_column_letter(len(head)) + str(max(2, ws.max_row))
def split_time(t):
    m = re.match(r'^(\d[\d:]*)\s*(am|pm)?\s*[–-]\s*(\d[\d:]*)\s*(am|pm)$', t.replace(' ', ''), re.I)
    if not m: return t, ''
    a, ap, b, bp = m.groups(); ap = ap or bp
    if not m.group(2):  # "12–2pm", "8–10am", "11am–1pm"
        h1 = int(a.split(':')[0]); h2 = int(b.split(':')[0])
        if bp.lower() == 'pm' and (h1 > h2 and h1 != 12): ap = 'am'
    fix = lambda x, p: (x if ':' in x else x + ':00') + ' ' + p.upper()
    return fix(a, ap), fix(b, bp)
D = lambda s: dt.date.fromisoformat(s)
weekly_dates = sorted({r['date'] for r in co['rehearsals'] if r['date'] >= '2027-01-09' and r['kind'] not in ('Performance', 'Dress rehearsal') and not r['room']})
# --- Rehearsals: every dated rehearsal except the repeating Jan–May Saturdays ---
rows = []
for r in co['rehearsals']:
    if r['date'] in weekly_dates and r['kind'] not in ('Performance', 'Dress rehearsal'): continue
    s, e = split_time(r['time']); note = ''
    if not e: s, note = '', r['time']
    room = r['room'].replace('Studio ', '')
    if room not in ('A', 'B', 'C', ''): note = (note + ' · ' if note else '') + room; room = ''
    rows.append([D(r['date']), D(r['date']).strftime('%a'), s, e, room, r['teacher'], r['what'], r['kind'], note])
ws = wb.active; ws.title = 'Rehearsals'
sheet(ws, 'One row per rehearsal. Studio = A, B or C. Type is optional (Solo, Duet, Trio, Small group, Large group, Hip Hop Company, Dress rehearsal, Performance). Dancer names go in Routine.',
      ['Date', 'Day', 'Start', 'End', 'Studio', 'Teacher', 'Routine / dancers', 'Type', 'Notes'], rows, [12, 6, 10, 10, 8, 14, 52, 16, 30])
for row in ws.iter_rows(min_row=3, max_col=1):
    for c in row: c.number_format = 'mmm d, yyyy'
dv = DataValidation(type='list', formula1='"A,B,C"', allow_blank=True); ws.add_data_validation(dv); dv.add('E3:E2000')
dv2 = DataValidation(type='list', formula1='"Miss Kelly,Miss Katie,Miss Meghan,Mr. Daniel,Miss Allie"', allow_blank=True); ws.add_data_validation(dv2); dv2.add('F3:F2000')
# --- Weekly Saturdays Jan–May: a template + the dates it runs ---
seen, tmpl = set(), []
for r in co['rehearsals']:
    if r['date'] == weekly_dates[0] and r['kind'] not in ('Performance', 'Dress rehearsal'):
        s, e = split_time(r['time']); tmpl.append(['', s, e, '', r['teacher'], r['what']])
ws = wb.create_sheet('Weekly Saturdays')
sheet(ws, 'The Saturday rehearsals that repeat every week from January. Fill in the Studio column. Change a routine once here instead of on every Saturday.',
      ['', 'Start', 'End', 'Studio', 'Teacher', 'Routine / dancers'], tmpl, [2, 10, 10, 8, 14, 52])
ws.delete_cols(1)
ws2 = wb.create_sheet('Weekly dates')
sheet(ws2, 'Every Saturday the weekly rehearsals happen. Delete a date to skip it (competition weekends are already left out).', ['Date', 'Note'], [[D(d), ''] for d in weekly_dates], [14, 40])
for row in ws2.iter_rows(min_row=3, max_col=1):
    for c in row: c.number_format = 'ddd mmm d, yyyy'
# --- No rehearsals ---
ws = wb.create_sheet('No rehearsals')
sheet(ws, 'Days with no rehearsals. Teacher = All, or the teachers whose rehearsals are off.', ['Date', 'Teacher', 'Reason'],
      [[D(o['date']), ', '.join(o['who']), ''] for o in co['off']], [14, 40, 40])
# --- Company events (and studio dates) ---
SHOW = {True: 'Company details locked', False: 'Public'}
erows = []
for e in cal:
    info = e.get('info') or co['locked'].get(e['id']) or {}
    body = []
    for s in info.get('sections', []):
        body.append(('## ' + s['h'] + '\n' if s.get('h') else '') + '\n'.join('- ' + i for i in s['items']))
    links = info.get('links', [])
    erows.append([e['title'], D(e['start']), D(e['end']) if e.get('end') else None, info.get('when', ''), e.get('where', ''), info.get('where', ''), e['type'],
                  'Company Central only' if e.get('hidden') else SHOW[bool(e.get('lock'))], info.get('summary', ''), '\n\n'.join(body),
                  links[0]['label'] if links else '', links[0]['url'] if links else '', links[1]['label'] if len(links) > 1 else '', links[1]['url'] if len(links) > 1 else ''])
ws = wb.create_sheet('Events')
sheet(ws, 'Every date for the calendar: Company events, competitions, breaks, autopay. Details: “## Heading” on its own line, then “- ” for each point. Leave End empty for one-day events.',
      ['What', 'Start', 'End', 'Time', 'Where (short)', 'Address', 'Type', 'Who sees details', 'Summary (one or two sentences)', 'Details', 'Button 1', 'Button 1 link', 'Button 2', 'Button 2 link'],
      erows, [34, 12, 12, 30, 20, 34, 11, 22, 44, 60, 22, 30, 22, 30])
for row in ws.iter_rows(min_row=3, min_col=2, max_col=3):
    for c in row: c.number_format = 'mmm d, yyyy'
dv3 = DataValidation(type='list', formula1='"Event,Company,Closure,Session,Recital"', allow_blank=True); ws.add_data_validation(dv3); dv3.add('G3:G500')
dv4 = DataValidation(type='list', formula1='"Public,Company details locked,Company Central only"', allow_blank=True); ws.add_data_validation(dv4); dv4.add('H3:H500')
ws = wb.create_sheet('How to use')
for line in ['How this workbook works', '', 'Rehearsals: one row per rehearsal (fall choreography Saturdays, weekday extras, dress rehearsals, shows).',
             'Weekly Saturdays + Weekly dates: the January–May Saturday schedule, typed once. The site repeats it on every date listed.',
             'No rehearsals: days off, all teachers or some.', 'Events: everything that goes on the calendar. “Who sees details” decides what’s behind the Company password.',
             '', 'Tips: one thing per cell, real dates (not “Sat 3/14”), times like 9:00 AM, leave a cell empty instead of “--”.',
             'Colors and formatting don’t matter: the website does the design.']:
    ws.append([line])
ws['A1'].font = Font(bold=True, size=14); ws.column_dimensions['A'].width = 110
wb.move_sheet('How to use', offset=-len(wb.sheetnames) + 1)
wb.save('Company_Calendar_Workbook_2026-27.xlsx')
print(len(rows), 'rehearsal rows,', len(tmpl), 'weekly slots x', len(weekly_dates), 'Saturdays,', len(co['off']), 'days off,', len(erows), 'events')
