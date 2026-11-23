#!/bin/bash
# Build the site into src/site3 (then copy site3/* to the repo root to publish)
set -e
cd "$(dirname "$0")"
OUT=site3; mkdir -p $OUT
MAP='{"HomeH.dc.html":"index.html","H-Classes.dc.html":"classes.html","H-Pricing.dc.html":"pricing.html","H-Company.dc.html":"company.html","H-About.dc.html":"about.html","H-Families.dc.html":"families.html","H-Shop.dc.html":"shop.html","H-Terms.dc.html":"terms.html","H-Privacy.dc.html":"privacy.html","H-CompanyHub.dc.html":"company-families.html","H-Scholarship.dc.html":"scholarship.html"}'
P=$(pwd)/project
T="Dance &amp; All That Jazz"
python3 build.py $P/HomeH.dc.html $OUT "$T — create. inspire. dance." "$MAP" index.html
for pg in Classes Pricing Company About Families Shop Terms Privacy CompanyHub Scholarship; do
  if [ -f $P/H-$pg.dc.html ]; then N=$(echo $pg | tr A-Z a-z); [ "$pg" = CompanyHub ] && N=company-families; python3 build.py $P/H-$pg.dc.html $OUT "$T — $pg" "$MAP" $N.html; fi
done
# keep the prototype out of search engines
for f in $OUT/*.html; do grep -q 'name="robots"' "$f" || sed -i '0,/<head>/s//<head>\n<meta name="robots" content="noindex, nofollow">/' "$f"; done
# Studio Pro schedule: embed the current saved copy (instant first paint) and the shared reader
R=$(cd .. && pwd)
python3 - "$OUT" "$R/classes.json" <<'PY'
import sys, glob, json
out, cj = sys.argv[1], sys.argv[2]
data = json.dumps(json.load(open(cj)), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
tag = '<script>window.DATJ_CLASSES=' + data + ';</script>\n<script src="scripts/studiopro.js"></script>\n'
for f in glob.glob(out + '/*.html'):
    s = open(f).read()
    if 'window.DATJ_CLASSES=' in s: continue
    s = s.replace('<head>\n', '<head>\n' + tag, 1)
    open(f, 'w').write(s)
PY
mkdir -p $OUT/scripts/vendor && cp $R/scripts/studiopro.js $OUT/scripts/ && cp $R/scripts/vendor/*.js $OUT/scripts/vendor/ && cp $R/classes.json $OUT/ && cp $R/company.enc.json $R/recital.enc.json $R/Competition_Workbook_TEMPLATE.xlsx $R/Studio_Calendar_TEMPLATE.xlsx $R/Company_Calendar_TEMPLATE.xlsx $OUT/
# Admin prototype: same schedule + teacher data as the site
python3 - "$OUT" "$R/classes.json" "$P/HomeH.dc.html" <<'PY'
import sys, json, re
out, cj, shell = sys.argv[1:4]
s = open('../admin-src/admin.html').read()
cls = json.dumps(json.load(open(cj)), ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
m = re.search(r'const TEACHER_BY_CLASS = (\{.*?\});', open(shell).read())
sh = open(shell).read(); m = re.search(r'const TEACHER_BY_CLASS = (\{.*?\});', sh); c0 = re.search(r'const CONTENT0 = (\{.*?\});\n', sh)
tag = '<script>window.DATJ_CLASSES=' + cls + ';window.DATJ_TEACHERS=' + (m.group(1) if m else '{}') + ';window.DATJ_CONTENT0=' + (c0.group(1).replace('</', '<\\/') if c0 else '{"lists":{},"texts":{}}') + ';window.DATJ_CAL0=' + (re.search(r'const CAL0 = (\[.*?\]);', sh).group(1).replace('</', '<\\/')) + ';</script>\n'
open(out + '/admin.html', 'w').write(s.replace('<head>\n', '<head>\n' + tag, 1))
PY
# Calendar subscribe feed: studio.ics from the studio calendar (same code as the Apps Script feed)
python3 - "$OUT" "$P/HomeH.dc.html" <<'PY'
import sys, re, json, subprocess
out, shell = sys.argv[1:3]
sh = open(shell).read()
js = re.search(r'const CAL0 = (\[.*?\]);', sh).group(1)
cal = json.loads(subprocess.run(['node', '-e', 'process.stdout.write(JSON.stringify(eval(require("fs").readFileSync(0,"utf8"))))'], input=js, capture_output=True, text=True, check=True).stdout)
json.dump(cal, open(out + '/calendar.json', 'w'), ensure_ascii=False, indent=1)
PY
[ -f $R/studio.ics ] && cp $R/studio.ics $OUT/studio.ics
node $R/scripts/make-studio-ics.js $OUT/calendar.json $OUT/studio.ics https://leighagrimm-web.github.io/datj-concept/
