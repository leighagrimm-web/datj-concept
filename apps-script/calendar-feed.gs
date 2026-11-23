/**
 * Dance & All That Jazz: calendar subscribe feeds
 *
 * Two feeds:
 *  1. Studio calendar (public): every public date on the studio calendar.
 *     Built into studio.ics by the website build (scripts/make-studio-ics.js uses the same code below),
 *     so it needs no Apps Script at all.
 *  2. A dancer's Company calendar (private): their rehearsals, their competition times
 *     (arrival / on stage / awards), Company-only dates and payment due dates.
 *     Served by this Apps Script web app: https://script.google.com/.../exec?c=CODE
 *
 * How a family gets their dancer link:
 *  Company Central (after the Company password) → Find your dancer → Subscribe.
 *  The page sends the dancer search ("Bella M") plus a proof that it knows the feed key
 *  (the key lives inside the encrypted Company bundle, so only families with the password have it).
 *  This script saves a random code for that search on the "Calendar links" tab and returns it.
 *  The link holds only the code, never the dancer's name.
 *
 * Turning off a link that got shared: on the "Calendar links" tab, untick Active (or delete the row).
 * The family subscribes again from Company Central to get a new code.
 *
 * Setup (one time, from Brittany's Google account):
 *  1. In the sign-ups spreadsheet: Extensions > Apps Script > add a file, paste this file.
 *  2. Project Settings > Script properties:
 *       FEED_KEY     the same feed key that is inside the Company bundle (Leigha sets both)
 *       COMPANY_FILE Drive file id of the readable Company data (company_plain.json)
 *       CONTENT_URL  https://<site>/content.json (studio calendar + team rosters)
 *       SITE_URL     https://<site>/
 *  3. Deploy > New deployment > Web app. Execute as: Me. Who has access: Anyone.
 *  4. Put the Web app URL in the website (FEED_URL).
 */

var FEED = (function () {
  var TZID = 'America/Chicago';
  var VTZ = ['BEGIN:VTIMEZONE', 'TZID:America/Chicago',
    'BEGIN:STANDARD', 'DTSTART:19701101T020000', 'RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU', 'TZOFFSETFROM:-0500', 'TZOFFSETTO:-0600', 'TZNAME:CST', 'END:STANDARD',
    'BEGIN:DAYLIGHT', 'DTSTART:19700308T020000', 'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU', 'TZOFFSETFROM:-0600', 'TZOFFSETTO:-0500', 'TZNAME:CDT', 'END:DAYLIGHT',
    'END:VTIMEZONE'];
  var STUDIO = 'Dance & All That Jazz, 844 N Elmhurst Rd, Prospect Heights, IL';
  var MONS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'];

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function hm(t, suf) {
    var m = /^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/i.exec(String(t).trim()); if (!m) return null;
    var h = +m[1] % 12; var ap = (m[3] || suf || '').toLowerCase(); if (ap === 'pm') h += 12; return [h, +(m[2] || 0), ap];
  }
  // "8–10am", "10am–12pm", "2:30–4:30 PM" -> [[h,m],[h,m]]
  function span(txt) {
    var p = String(txt || '').replace(/\u2060/g, '').split(/\s*[–-]\s*/); if (p.length !== 2) return null;
    var b = hm(p[1]); if (!b) return null; var a = hm(p[0], b[2]); if (!a) return null;
    if (!/am|pm/i.test(p[0]) && a[0] * 60 + a[1] > b[0] * 60 + b[1]) a = hm(p[0], 'am');
    return [a, b];
  }
  function clock(t) { var m = /^(\d{1,2}):(\d{2})\s*(AM|PM)$/i.exec(String(t || '').trim()); if (!m) return null; var h = +m[1] % 12; if (/pm/i.test(m[3])) h += 12; return [h, +m[2]]; }
  function mins(t) { var k = clock(t); return k ? k[0] * 60 + k[1] : null; }
  function later(t, n) { var x = t[0] * 60 + t[1] + n; return [Math.min(23, Math.floor(x / 60)), x >= 1440 ? 59 : x % 60]; }
  function addDay(iso, n) { var a = iso.split('-').map(Number); var t = new Date(Date.UTC(a[0], a[1] - 1, a[2] + n)); return t.getUTCFullYear() + '-' + pad(t.getUTCMonth() + 1) + '-' + pad(t.getUTCDate()); }
  function esc(x) { return String(x || '').replace(/\\/g, '\\\\').replace(/;/g, '\\;').replace(/,/g, '\\,').replace(/\r?\n/g, '\\n'); }
  // Fold long lines at 75 bytes (UTF-8), never inside a character
  function fold(line) {
    var out = [], cur = '', bytes = 0, limit = 75;
    for (var i = 0; i < line.length; i++) {
      var ch = line.charAt(i), code = line.charCodeAt(i);
      if (code >= 0xD800 && code <= 0xDBFF && i + 1 < line.length) { ch += line.charAt(++i); }
      var b = encodeURIComponent(ch).replace(/%[0-9A-F]{2}/g, 'x').length;
      if (bytes + b > limit) { out.push(cur); cur = ' '; bytes = 1; limit = 75; }
      cur += ch; bytes += b;
    }
    out.push(cur); return out.join('\r\n');
  }
  function stamp(iso, t) { return iso.replace(/-/g, '') + 'T' + pad(t[0]) + pad(t[1]) + '00'; }
  function vevent(e, now) {
    var L = ['BEGIN:VEVENT', 'UID:' + String(e.uid).replace(/[^\w.-]/g, '') + '@danceandallthatjazz.com', 'DTSTAMP:' + now];
    if (e.t0) {
      var t1 = e.t1 || later(e.t0, 60);
      if (t1[0] * 60 + t1[1] <= e.t0[0] * 60 + e.t0[1]) t1 = later(e.t0, 30);
      L.push('DTSTART;TZID=' + TZID + ':' + stamp(e.date, e.t0), 'DTEND;TZID=' + TZID + ':' + stamp(e.date, t1));
    } else {
      L.push('DTSTART;VALUE=DATE:' + e.date.replace(/-/g, ''), 'DTEND;VALUE=DATE:' + addDay(e.end && e.end > e.date ? e.end : e.date, 1).replace(/-/g, ''));
      L.push('TRANSP:TRANSPARENT');
    }
    L.push('SUMMARY:' + esc(e.title));
    if (e.where) L.push('LOCATION:' + esc(e.where));
    if (e.desc) L.push('DESCRIPTION:' + esc(e.desc));
    if (e.url) L.push('URL:' + e.url);
    L.push('END:VEVENT');
    return L.map(fold).join('\r\n');
  }
  // name: what the calendar is called in the family's calendar app
  function calendar(name, events, nowDate) {
    var now = (nowDate || new Date()).toISOString().replace(/[-:]/g, '').slice(0, 15) + 'Z';
    var head = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Dance & All That Jazz//Calendar feed//EN', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
      'X-WR-CALNAME:' + esc(name), 'X-WR-TIMEZONE:' + TZID,
      // Ask calendar apps to check every hour (Apple and Outlook listen; Google Calendar picks its own schedule)
      'REFRESH-INTERVAL;VALUE=DURATION:PT1H', 'X-PUBLISHED-TTL:PT1H'].map(fold).concat(VTZ);
    var seen = {};
    var body = events.filter(function (e) { if (!e || !e.date || seen[e.uid]) return false; seen[e.uid] = 1; return true; })
      .sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; })
      .map(function (e) { return vevent(e, now); });
    return head.concat(body).concat(['END:VCALENDAR']).join('\r\n') + '\r\n';
  }
  function infoText(e) {
    var i = e.info || {}, out = [];
    if (i.when) out.push(i.when);
    if (i.summary) out.push(i.summary);
    (i.sections || []).forEach(function (s) { out.push(''); if (s.h) out.push(s.h); (s.items || []).forEach(function (x) { out.push('• ' + x); }); });
    return out.join('\n').trim();
  }

  // ---------- Feed 1: studio calendar (public) ----------
  // cal: the studio calendar list (same as the website). Hidden dates (Company Central only) stay out.
  // "Company families only" dates show their title and day; their details stay behind the Company password.
  function studioEvents(cal, siteUrl, today) {
    var from = addDay(today, -60);
    return (cal || []).filter(function (e) { return e.start && !e.hidden && (e.end || e.start) >= from; }).map(function (e, i) {
      var sp = e.info && e.info.when && !e.end ? timeIn(e.info.when) : null;
      var desc = e.lock ? 'Company families: details are in Company Central (Company password).\n' + siteUrl + 'company-families.html'
        : (infoText(e) + '\n\nStudio calendar: ' + siteUrl + 'families.html#calendar').trim();
      return { uid: 'cal-' + (e.id || ('c' + i)), date: e.start, end: e.end || '', t0: sp && sp[0], t1: sp && sp[1], title: e.title, where: e.where || '', desc: desc };
    });
  }
  // Pull a time out of text like "Wednesday, Nov 18 · 7:00 PM" or "2:30–4:30 PM"
  function timeIn(txt) {
    var s = String(txt || ''), m = /(\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*[–-]\s*\d{1,2}(?::\d{2})?\s*(?:am|pm))/i.exec(s);
    if (m) { var sp = span(m[1].replace(/\s+/g, '')); if (sp) return [sp[0], sp[1]]; }
    m = /(\d{1,2}:\d{2}\s*(?:AM|PM))/i.exec(s); if (m) { var c = clock(m[1].replace(/\s+/g, ' ')); if (c) return [c, later(c, 60)]; }
    return null;
  }

  // ---------- Feed 2: one dancer's Company calendar (private) ----------
  // Same rules as Company Central's "Add to my calendar":
  //  - rehearsals with the dancer's name, plus the group rehearsals they are in (team rosters + the competition Groups tab)
  //  - competition times: arrival for the first dance of the day (and again only when there are 2+ hours
  //    between the last awards and the next arrival), on stage, and awards (the first awards after the dance on its stage)
  //  - Company dates hidden from the public calendar, and Company payment due dates
  function query(q) {
    q = String(q || '').trim().toLowerCase();
    var qG = q.split(/\s*(?:,|&|\+|\band\b)\s*/).map(function (x) { return x.split(/[^a-z]+/).filter(Boolean); }).filter(function (g) { return g.length; });
    return function (txt) {
      var T = String(txt || '').toLowerCase().split(/[^a-z]+/).filter(Boolean);
      return qG.some(function (g) { return T.some(function (_, i) { return g.every(function (w, j) { return T[i + j] && T[i + j].indexOf(w) === 0; }); }); });
    };
  }
  function dancerEvents(o) {
    var co = o.co || {}, teams = o.teams || [], hitQ = query(o.q), today = o.today, siteUrl = o.siteUrl || '';
    var cc = siteUrl + 'company-families.html', from = addDay(today, -60);
    if (!String(o.q || '').trim()) return [];
    var nameHit = function (r) { return hitQ(r.what); };
    var GROUPK = { 'Large group': 1, 'Hip Hop Company': 1, 'Dress rehearsal': 1, 'Windy City Bulls': 1, 'Performance': 1 };
    var isShow = function (r) { return r.kind === 'Performance' || r.kind === 'Windy City Bulls'; };
    var GG = {};
    teams.forEach(function (t) { var n = (t.dancers || []).map(function (d) { return d.t; }).filter(Boolean); if (n.length) GG[(t.t + ' company').toLowerCase()] = n; });
    (co.comps || []).forEach(function (c) { Object.keys(c.groups || {}).forEach(function (g) { if ((c.groups[g] || []).length) GG[g.toLowerCase()] = c.groups[g]; }); });
    var onTeam = function (t) { return (t.dancers || []).some(function (d) { return hitQ(d.t); }); };
    var inIt = function (r) {
      if (nameHit(r)) return true;
      if (r.kind === 'Dress rehearsal' || isShow(r)) {
        var named = teams.filter(function (t) { return new RegExp('\\b' + t.t + '\\b', 'i').test(r.what || ''); });
        return !named.length || named.some(onTeam);
      }
      var g = GG[String(r.what || '').replace(/\s*\(.*\)$/, '').trim().toLowerCase()];
      return g ? g.some(function (n) { return hitQ(n); }) : true;
    };
    var out = [];
    (co.rehearsals || []).filter(function (r) { return r.date >= from && (nameHit(r) || GROUPK[r.kind]) && inIt(r); }).forEach(function (r) {
      var sp = span(r.time);
      out.push({ uid: 'reh-' + r.date + '-' + String(r.time).replace(/\W/g, '') + '-' + String(r.what).replace(/\W/g, '').slice(0, 24), date: r.date, t0: sp && sp[0], t1: sp && sp[1],
        title: (isShow(r) || /rehearsal/i.test(r.what) ? '' : 'Rehearsal: ') + r.what,
        where: isShow(r) ? (r.room || '') : STUDIO + (r.room ? ' (' + r.room + ')' : ''),
        desc: [r.room, r.teacher].filter(Boolean).join(' · ') + (sp ? '' : (r.time ? '\n' + r.time : '')) + '\nCompany Central: ' + cc });
    });
    (co.comps || []).filter(function (c) { return c.show !== false && (!c.hideAfter || c.hideAfter >= today) && (c.days || []).length; }).forEach(function (c) {
      var yr = (/(20\d\d)/.exec(c.dates || '') || [])[1]; if (!yr) return;
      var prelim = !/final/i.test(c.status || ''), tag = prelim ? ' (preliminary)' : '';
      var G = {}; teams.forEach(function (t) { var n = (t.dancers || []).map(function (d) { return d.t; }).filter(Boolean); if (n.length) G[(t.t + ' company').toLowerCase()] = n; });
      Object.keys(c.groups || {}).forEach(function (g) { if ((c.groups[g] || []).length) G[g.toLowerCase()] = c.groups[g]; });
      var where = [c.venue, c.address].filter(Boolean).join(', ');
      var foot = (prelim ? '\nPRELIMINARY schedule: times can change. This calendar updates on its own when the final schedule is posted.' : '') + '\nSchedule: ' + cc + '#competitions';
      (c.days || []).forEach(function (d) {
        var m = /(\d{1,2})\/(\d{1,2})/.exec(d.day || ''); if (!m) return;
        var iso = yr + '-' + pad(+m[1]) + '-' + pad(+m[2]); if (iso < from) return;
        var rows = d.rows || [];
        var awards = rows.filter(function (r) { return r.awards && mins(r.perf) != null; });
        var mine = rows.filter(function (r) { return !r.awards && mins(r.perf) != null; }).filter(function (r) {
          var g = G[String(r.dancers || '').trim().toLowerCase()]; return hitQ(r.dancers) || (g && g.some(hitQ));
        }).sort(function (x, y) { return mins(x.perf) - mins(y.perf); });
        var awardFor = function (r) {
          return awards.filter(function (w) { return mins(w.perf) > mins(r.perf) && (!w.stage || !r.stage || w.stage === r.stage); })
            .sort(function (x, y) { return mins(x.perf) - mins(y.perf); })[0] || null;
        };
        var seenW = {}, freeAt = null;
        mine.forEach(function (r) {
          var aw = awardFor(r), a = mins(r.arrive), pf = mins(r.perf);
          if (a != null && (freeAt == null || a - freeAt >= 120))
            out.push({ uid: c.id + '-' + iso + '-arr-' + r.num, date: iso, t0: clock(r.arrive), t1: clock(r.perf), title: 'Arrive: ' + c.name + tag, where: where,
              desc: 'Arrive ' + r.arrive + ' for #' + r.num + ' ' + r.song + ' (on stage ~' + r.perf + ')\n' + r.dancers + (r.stage ? ' · ' + r.stage : '') + foot });
          out.push({ uid: c.id + '-' + iso + '-' + r.num, date: iso, t0: clock(r.perf), t1: later(clock(r.perf), 5), title: '#' + r.num + ' ' + r.song + ' on stage' + tag, where: where,
            desc: r.dancers + (r.stage ? ' · ' + r.stage : '') + (r.note ? '\n' + r.note : '') + foot });
          if (aw) {
            var k = aw.perf + (aw.stage || '');
            if (!seenW[k]) {
              seenW[k] = 1; var dur = +((/(\d+)\s*min/.exec(aw.note || '') || [])[1] || 30);
              out.push({ uid: c.id + '-' + iso + '-awards-' + String(aw.perf).replace(/\W/g, '') + (aw.stage ? '-' + String(aw.stage).replace(/\W/g, '') : ''), date: iso, t0: clock(aw.perf), t1: later(clock(aw.perf), dur),
                title: 'Awards: ' + c.name + tag, where: where, desc: 'Awards' + (aw.stage ? ' · ' + aw.stage : '') + (aw.note ? ' (' + aw.note + ')' : '') + foot });
            }
          }
          freeAt = Math.max(freeAt || 0, aw ? mins(aw.perf) + 30 : pf + 5);
        });
      });
    });
    // Company dates that only show in Company Central (the public studio feed leaves them out), with their details
    (o.cal || []).filter(function (e) { return e.hidden && e.start && (e.end || e.start) >= from; }).forEach(function (e, i) {
      var lk = (co.locked || {})[e.id] || {};
      out.push({ uid: 'cal-' + (e.id || 'h' + i), date: e.start, end: e.end || '', title: e.title, where: lk.where || e.where || '',
        desc: [lk.when, lk.summary, infoText(e)].filter(Boolean).join('\n') + '\nCompany Central: ' + cc });
    });
    (co.due || []).filter(function (d) { return d.date >= from; }).forEach(function (d) {
      var dup = (o.cal || []).some(function (e) { return e.start === d.date && String(e.title).toLowerCase() === String(d.t).toLowerCase(); });
      if (!dup) out.push({ uid: 'due-' + d.date + '-' + String(d.t).replace(/\W/g, '').slice(0, 24), date: d.date, title: 'Due: ' + d.t, where: '', desc: 'Company Central: ' + cc });
    });
    return out;
  }
  function dancerName(q) { return String(q || '').trim().replace(/\s+/g, ' ').replace(/\b\w/g, function (c) { return c.toUpperCase(); }); }

  return { calendar: calendar, studioEvents: studioEvents, dancerEvents: dancerEvents, dancerName: dancerName, query: query, span: span, timeIn: timeIn };
})();

// ================= Apps Script web app (runs in Brittany's Google account) =================
var LINKS_TAB = 'Calendar links';

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.feed === 'studio') return ics_(FEED.calendar('Dance & All That Jazz', FEED.studioEvents(content_().calendar, prop_('SITE_URL'), todayChicago_())));
  var row = findCode_(p.c);
  if (!row) return ContentService.createTextOutput('This calendar link is turned off. Subscribe again from Company Central.').setMimeType(ContentService.MimeType.TEXT);
  var c = content_();
  var events = FEED.dancerEvents({ co: company_(), cal: c.calendar, teams: (c.lists || {}).teams || [], q: row.q, today: todayChicago_(), siteUrl: prop_('SITE_URL') });
  touch_(row);
  return ics_(FEED.calendar(FEED.dancerName(row.q) + ' · D&ATJ Company', events));
}

// Company Central asks for a link: { action: 'subscribe', q: 'bella m', proof: HMAC-SHA256(FEED_KEY, q) as hex }
function doPost(e) {
  var data = {}; try { data = JSON.parse((e && e.postData && e.postData.contents) || '{}'); } catch (x) {}
  if (data.action !== 'subscribe') return json_({ ok: false });
  var q = normQ_(data.q);
  if (!q || q.length > 80) return json_({ ok: false, error: 'Type your dancer’s name first.' });
  if (String(data.proof || '') !== hmacHex_(q)) return json_({ ok: false, error: 'Unlock Company Central again, then try once more.' });
  var lock = LockService.getScriptLock(); lock.waitLock(20000);
  try {
    var sh = linksSheet_(), vals = sh.getDataRange().getValues();
    for (var i = 1; i < vals.length; i++) if (vals[i][1] === q && vals[i][5] === true) return json_({ ok: true, code: vals[i][0] });
    var code = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
    sh.appendRow([code, q, new Date(), '', 0, true]);
    return json_({ ok: true, code: code });
  } finally { lock.releaseLock(); }
}

function normQ_(q) { return String(q || '').trim().toLowerCase().replace(/\s+/g, ' '); }
function hmacHex_(q) {
  return Utilities.computeHmacSha256Signature(q, prop_('FEED_KEY')).map(function (b) { return ('0' + (b & 255).toString(16)).slice(-2); }).join('');
}
function linksSheet_() {
  var ss = SpreadsheetApp.getActive(), sh = ss.getSheetByName(LINKS_TAB);
  if (!sh) { sh = ss.insertSheet(LINKS_TAB); sh.appendRow(['Code', 'Dancer search', 'Created', 'Last checked by a calendar app', 'Times checked', 'Active']); sh.setFrozenRows(1); }
  return sh;
}
function findCode_(code) {
  if (!code || !/^[a-f0-9]{20}$/.test(code)) return null;
  var cache = CacheService.getScriptCache(), hit = cache.get('code:' + code);
  if (hit) return JSON.parse(hit);
  var sh = linksSheet_(), vals = sh.getDataRange().getValues();
  for (var i = 1; i < vals.length; i++) if (vals[i][0] === code) {
    if (vals[i][5] !== true) return null;
    var row = { r: i + 1, q: vals[i][1] }; cache.put('code:' + code, JSON.stringify(row), 300); return row;
  }
  return null;
}
function touch_(row) {
  try { var sh = linksSheet_(); sh.getRange(row.r, 4).setValue(new Date()); var n = sh.getRange(row.r, 5); n.setValue((+n.getValue() || 0) + 1); } catch (e) {}
}
function content_() {
  var cache = CacheService.getScriptCache(), hit = cache.get('content');
  if (hit) return JSON.parse(hit);
  var j = JSON.parse(UrlFetchApp.fetch(prop_('CONTENT_URL')).getContentText());
  try { cache.put('content', JSON.stringify(j), 600); } catch (e) {}
  return j;
}
function company_() {
  var cache = CacheService.getScriptCache(), hit = cache.get('company');
  if (hit) return JSON.parse(hit);
  var j = JSON.parse(DriveApp.getFileById(prop_('COMPANY_FILE')).getBlob().getDataAsString());
  try { cache.put('company', JSON.stringify(j), 600); } catch (e) {}
  return j;
}
function todayChicago_() { return Utilities.formatDate(new Date(), 'America/Chicago', 'yyyy-MM-dd'); }
function prop_(k) { return PropertiesService.getScriptProperties().getProperty(k) || ''; }
function ics_(s) { return ContentService.createTextOutput(s).setMimeType(ContentService.MimeType.ICAL); }
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }

// Node (website build + tests) can load the feed code too
if (typeof module !== 'undefined') module.exports = FEED;
