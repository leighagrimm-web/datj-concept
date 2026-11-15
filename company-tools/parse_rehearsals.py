"""Turn Brittany's month-grid Company Rehearsal Calendar (.xlsx) into a list of entries."""
import openpyxl, re, json, sys, datetime as dt
SRC = sys.argv[1]; OUT = sys.argv[2]
wb = openpyxl.load_workbook(SRC)
COLOR = {'FF0ED1E3': 'Miss Kelly', 'FFCC91FC': 'Miss Katie', 'FFFF85FF': 'Miss Meghan', 'FF93C47D': 'Mr. Daniel'}
INSTR = {'Miss Kelly', 'Miss Katie', 'Miss Meghan', 'Mr Daniel', 'Mr. Daniel'}
COLS = 'ABCDEFGH'
TIME = re.compile(r'^\s*([\d:]+\s*(?:am|pm)?\s*-\s*[\d:]+\s*(?:am|pm))\s*-\s*([ABC])\s*$', re.I)
def fill(c):
    f = c.fill
    return f.fgColor.rgb if f and f.fill_type and f.fgColor.type == 'rgb' else ''
def clean(v): return re.sub(r'\s+', ' ', str(v).replace('\n', ' ')).strip()
out = []
for ws in wb.worksheets:
    if ws.title == 'Weekly Rehearsals': continue
    first = ws['A1'].value; y, m = first.year, first.month
    merged = {}
    for r in ws.merged_cells.ranges: merged[(r.min_row, r.min_col)] = r
    # date rows
    drows = []
    for row in ws.iter_rows(min_row=2, max_row=60):
        nums = {c.column: int(c.value) for c in row if isinstance(c.value, (int, float)) and 1 <= c.value <= 31}
        if len(nums) >= 1 and all(isinstance(c.value, (int, float)) or c.value in (None, '', ' ') for c in row if c.column <= 8):
            drows.append((row[0].row, nums))
    for bi, (r0, nums) in enumerate(drows):
        r1 = drows[bi + 1][0] if bi + 1 < len(drows) else 60
        # Saturday number may sit in G or H
        def day_for(col):
            if col in (7, 8): return nums.get(7) or nums.get(8)
            return nums.get(col)
        def date_for(col):
            d = day_for(col)
            return dt.date(y, m, d) if d else None
        used = set()
        for r in range(r0 + 1, r1):
            g = ws.cell(r, 7); h = ws.cell(r, 8)
            gv = clean(g.value) if g.value not in (None, '', ' ') else ''
            hv = clean(h.value) if h.value not in (None, '', ' ') else ''
            sat = date_for(7)
            mt = TIME.match(gv) if gv else None
            if mt and hv and sat:
                out.append({'date': sat.isoformat(), 'kind': 'rehearsal', 'time': mt.group(1).replace(' ', ''), 'room': mt.group(2).upper(), 'what': hv, 'teacher': COLOR.get(fill(g)) or COLOR.get(fill(h), '')})
                used |= {(r, 7), (r, 8)}
        # everything else: group consecutive cells in a column into one item
        for col in range(1, 9):
            r = r0 + 1
            while r < r1:
                c = ws.cell(r, col)
                v = clean(c.value) if c.value not in (None, '', ' ') else ''
                if not v or (r, col) in used or v in INSTR or isinstance(c.value, (int, float)):
                    r += 1; continue
                parts = [v]; rr = r + 1
                while rr < r1 and col <= 6:
                    v2 = ws.cell(rr, col).value
                    if v2 in (None, '', ' ') or (rr, col) in used: break
                    parts.append(clean(v2)); rr += 1
                d = date_for(col)
                if not d: r = rr; continue
                mr = merged.get((r, col)); end = None
                if mr and mr.max_col > mr.min_col:
                    ec = mr.max_col; end = date_for(ec) or (date_for(ec - 1) if ec == 8 else None)
                    if end == d: end = None
                out.append({'date': d.isoformat(), 'end': end.isoformat() if end else '', 'kind': 'note', 'text': ' · '.join(parts), 'teacher': COLOR.get(fill(c), ''), 'col': col})
                r = rr
# Weekly Rehearsals tab (Saturdays Jan–May)
ws = wb['Weekly Rehearsals']; heads = {c.column: clean(c.value) for c in ws[1] if c.value}
weekly = []
for row in ws.iter_rows(min_row=2):
    t = clean(row[0].value) if row[0].value else ''
    for c in row[1:]:
        if c.value:
            hd = heads.get(c.column, ''); mm = re.match(r'^(.*?)\s*[-–(]\s*(?:Studio\s*)?([ABC])\)?\s*$', hd)
            weekly.append({'time': t, 'what': clean(c.value), 'teacher': (mm.group(1) if mm else hd).replace('Mr Daniel', 'Mr. Daniel'), 'room': ('Studio ' + mm.group(2)) if mm else ''})
json.dump({'entries': out, 'weekly': weekly}, open(OUT, 'w'), indent=1)
print(len(out), 'entries,', len(weekly), 'weekly slots')
