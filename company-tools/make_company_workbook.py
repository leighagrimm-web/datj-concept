"""Company Calendar workbook: one plain row per rehearsal (no month-by-month layout).
Makes this season's filled workbook (private: dancer names) and a blank TEMPLATE for next season.
python3 make_company_workbook.py  -> Company_Calendar_Workbook_2026-27.xlsx + Company_Calendar_TEMPLATE.xlsx"""
import json, re, datetime as dt, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter as L
co = json.load(open('company_plain.json'))
H = Font(bold=True, color='FFFFFF'); F = PatternFill('solid', fgColor='00ADB5'); W = Alignment(wrap_text=True, vertical='top')
TEACHERS = ['Miss Kelly', 'Miss Katie', 'Miss Meghan', 'Mr. Daniel', 'Miss Allie']
TYPES = ['Solo', 'Duet', 'Trio', 'Small group', 'Large group', 'Hip Hop Company', 'Dress rehearsal', 'Performance', 'Windy City Bulls']
def kindOf(w):  # same guess the website makes when Type is empty
    wl = w.lower()
    if 'dress rehearsal' in wl: return 'Dress rehearsal'
    if 'windy city' in wl: return 'Windy City Bulls'
    if 'hip hop company' in wl: return 'Hip Hop Company'
    if 'large group' in wl: return 'Large group'
    if 'solo' in wl or ',' not in wl and '&' not in wl and len(wl.split()) <= 2: return 'Solo'
    return {2: 'Duet', 3: 'Trio'}.get(len(re.split(r',|&', w)), 'Small group')
def times(t):  # "8–10am" -> (time(8,0), time(10,0)); not a time -> None
    p = re.split(r'\s*[–-]\s*', t.replace(' ', ''))
    if len(p) != 2: return None
    hm = lambda x: re.fullmatch(r'(\d{1,2})(?::(\d{2}))?(am|pm)?', x, re.I)
    a, b = hm(p[0]), hm(p[1])
    if not a or not b or not b.group(3): return None
    to = lambda m, ap: (int(m.group(1)) % 12 + (12 if ap.lower() == 'pm' else 0), int(m.group(2) or 0))
    e = to(b, b.group(3)); s = to(a, a.group(3) or b.group(3))
    if not a.group(3) and s > e: s = to(a, 'am')
    return dt.time(*s), dt.time(*e)
def build(name, rows, off, filled):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'How to use'
    for line in ['Company Calendar: how this workbook works', '',
                 'Rehearsals tab: one row per rehearsal. That’s it: no monthly layout, no colors.',
                 '  Date: a real date (type 3/13/2027). Day fills itself in.',
                 '  Start / End: times like 9:00 AM. If there’s no set time yet, leave them empty and write it in Notes (e.g. “Times on your show flyer”).',
                 '  Studio: A, B or C. For somewhere else, type the place (e.g. Wheeling High School). Empty = “Studio TBA”.',
                 '  Teacher: pick from the list. It sets the color dot on the website.',
                 '  Dancers or group: first names with the last initial when two dancers share a first name (Bella M), separated by commas.',
                 '      For a group dance, type its group name exactly as on the Groups tab of the Competition workbook (e.g. Jazz Large Group, Teen Company).',
                 '      That’s how “Find your dancer” and each dancer’s calendar know who is in it.',
                 '  Type: optional. Leave it empty and the website works it out (1 name = Solo, 2 = Duet, 3 = Trio, 4+ = Small group, “Large group”, “Hip Hop Company”, “Dress rehearsal” in the name).',
                 '      Pick one only for shows and performances, or if the guess is wrong.',
                 '  Repeating Saturdays: copy the rows and paste them under the next Saturday’s date.',
                 '',
                 'No rehearsals tab: days off. Teacher = All, or the teachers who are off (Miss Kelly, Miss Meghan).',
                 '',
                 'Studio dates (breaks, events, competitions days, autopay) are on the Studio calendar in the admin, not here.',
                 'Competition schedules and group lineups are in the Competition workbook.',
                 '',
                 'Changes show up in Company Central and in every subscribed dancer calendar on their own (see the admin help).',
                 'Next season: File > Make a copy, rename it for the new season, and delete last season’s rows (keep the header rows).']:
        ws.append([line])
    ws['A1'].font = Font(bold=True, size=14); ws.column_dimensions['A'].width = 120
    def sheet(title, note, head, data, widths):
        ws = wb.create_sheet(title); ws.append([note]); ws['A1'].font = Font(italic=True, color='555555'); ws.append(head)
        for c in ws[2]: c.font = H; c.fill = F
        for r in data: ws.append(r)
        for i, w in enumerate(widths): ws.column_dimensions[L(i + 1)].width = w
        ws.freeze_panes = 'A3'; ws.auto_filter.ref = 'A2:' + L(len(head)) + '2'
        return ws
    ws = sheet('Rehearsals', 'One row per rehearsal. Type is optional. Dancers or group: names separated by commas, or the group name from the Competition workbook’s Groups tab.',
               ['Date', 'Day', 'Start', 'End', 'Studio', 'Teacher', 'Dancers or group', 'Type', 'Notes'], rows, [13, 6, 10, 10, 18, 13, 50, 16, 28])
    last = 1500
    for i in range(3, last + 1):
        ws.cell(i, 2).value = '=IF(A%d="","",TEXT(A%d,"ddd"))' % (i, i)
        ws.cell(i, 1).number_format = 'mmm d, yyyy'; ws.cell(i, 3).number_format = ws.cell(i, 4).number_format = 'h:mm AM/PM'
        for c in (7, 9): ws.cell(i, c).alignment = W
    def dv(col, items, strict):
        v = DataValidation(type='list', formula1='"' + ','.join(items) + '"', allow_blank=True, showErrorMessage=strict); ws.add_data_validation(v); v.add('%s3:%s%d' % (col, col, last))
    dv('E', ['A', 'B', 'C'], False); dv('F', TEACHERS, False); dv('H', TYPES, True)
    ws.auto_filter.ref = 'A2:I%d' % max(3, len(rows) + 2)
    ws2 = sheet('No rehearsals', 'Days with no rehearsals. Teacher = All, or the teachers who are off, separated by commas.', ['Date', 'Day', 'Teacher', 'Reason'], off, [13, 6, 40, 40])
    for i in range(3, 300):
        ws2.cell(i, 2).value = '=IF(A%d="","",TEXT(A%d,"ddd"))' % (i, i); ws2.cell(i, 1).number_format = 'mmm d, yyyy'
    wb.save(name)
if __name__ == '__main__':
    rows = []
    for r in sorted(co['rehearsals'], key=lambda r: (r['date'], times(r['time'])[0] if times(r['time']) else dt.time(23, 59), r['what'])):
        tt = times(r['time']); room = r['room']
        st = room.replace('Studio ', '') if re.fullmatch(r'Studio [ABC]', room) else room
        rows.append([dt.date.fromisoformat(r['date']), None, tt[0] if tt else None, tt[1] if tt else None, st, r['teacher'], r['what'],
                     '' if kindOf(r['what']) == r['kind'] else r['kind'], '' if tt else r['time']])
    off = [[dt.date.fromisoformat(o['date']), None, ', '.join(o['who']), ''] for o in co['off']]
    build('Company_Calendar_Workbook_2026-27.xlsx', rows, off, True)
    EX = [[dt.date(2027, 9, 11), None, dt.time(9), dt.time(10), 'B', 'Miss Kelly', 'Ava S', '', ''],
          [dt.date(2027, 9, 11), None, dt.time(10), dt.time(11), 'B', 'Miss Kelly', 'Ava S, Max T, Lily R', '', ''],
          [dt.date(2027, 9, 11), None, dt.time(11), dt.time(13), 'C', 'Miss Katie', 'Jazz Large Group', '', ''],
          [dt.date(2027, 12, 4), None, None, None, 'Wheeling High School', '', 'Holiday show', 'Performance', 'Schedule ~1 week before']]
    build('Company_Calendar_TEMPLATE.xlsx', EX, [[dt.date(2027, 11, 27), None, 'All', 'Thanksgiving']], False)
    print(len(rows), 'rehearsals,', sum(1 for r in rows if r[7]), 'with a Type typed in,', len(off), 'days off')
