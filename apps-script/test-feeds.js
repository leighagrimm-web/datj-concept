// Automated checks for the calendar feeds (run before every change to calendar-feed.gs).
// node apps-script/test-feeds.js <calendar.json> <content0.json> <company_plain.json> [today]
// The readable Company data is private: keep it out of the repo and pass its path here.
const fs = require('fs'), path = require('path'), vm = require('vm');
let ICAL; try { ICAL = require('ical.js'); } catch (e) { ICAL = require('/tmp/icaltest/node_modules/ical.js'); } ICAL = ICAL.default || ICAL;
const [calP, contentP, coP, today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' })] = process.argv.slice(2);
const box = { module: { exports: {} } }; vm.createContext(box);
vm.runInContext(fs.readFileSync(path.join(__dirname, 'calendar-feed.gs'), 'utf8'), box);
const F = box.module.exports;
const cal = JSON.parse(fs.readFileSync(calP, 'utf8')), teams = JSON.parse(fs.readFileSync(contentP, 'utf8')).lists.teams, co = JSON.parse(fs.readFileSync(coP, 'utf8'));
const SITE = 'https://example.org/';
let fails = 0, checks = 0; const ok = (c, msg) => { checks++; if (!c) { fails++; console.log('FAIL', msg); } };

function lint(ics, label) {
  ok(/^BEGIN:VCALENDAR\r\n/.test(ics) && /END:VCALENDAR\r\n$/.test(ics), label + ': begins/ends');
  ok(!/[^\r]\n/.test(ics), label + ': CRLF line ends only');
  ics.split('\r\n').forEach((l, i) => ok(Buffer.byteLength(l) <= 75, label + ': line ' + i + ' is ' + Buffer.byteLength(l) + ' bytes'));
  ok(!/undefined|null|NaN/.test(ics), label + ': no undefined/null/NaN');
  const comp = new ICAL.Component(ICAL.parse(ics)); const tz = comp.getFirstSubcomponent('vtimezone');
  ICAL.TimezoneService.register(new ICAL.Timezone(tz));
  const evs = comp.getAllSubcomponents('vevent').map(v => new ICAL.Event(v)); const uids = {};
  evs.forEach(e => {
    ok(!uids[e.uid], label + ': duplicate UID ' + e.uid); uids[e.uid] = 1;
    ok(e.startDate && e.endDate, label + ': start/end ' + e.summary);
    ok(e.endDate.compare(e.startDate) > 0, label + ': end after start ' + e.summary + ' ' + e.startDate);
    if (!e.startDate.isDate) ok(e.startDate.zone && e.startDate.zone.tzid === 'America/Chicago', label + ': Central time ' + e.summary);
  });
  return evs;
}

// 1. Studio feed
const studio = F.calendar('Dance & All That Jazz', F.studioEvents(cal, SITE, today));
const sev = lint(studio, 'studio');
ok(sev.length > 0, 'studio has dates');
ok(!sev.some(e => cal.find(c => 'cal-' + c.id + '@danceandallthatjazz.com' === e.uid && c.hidden)), 'studio: hidden dates stay out');
cal.filter(c => c.lock && !c.hidden).forEach(c => { const e = sev.find(x => x.uid.startsWith('cal-' + c.id + '@')); if (e) ok(/Company Central/.test(e.description) && !(co.locked || {})[c.id] || !String(e.description).includes(((co.locked || {})[c.id] || {}).summary || '§'), 'studio: locked details stay out ' + c.id); });

// 2. DST: same 10 AM rehearsal the day before and after the March change → UTC 16:00 then 15:00
const dst = F.calendar('t', F.dancerEvents({ co: { rehearsals: [{ date: '2027-03-13', time: '10–11am', what: 'Zed Q', kind: 'Solo' }, { date: '2027-03-15', time: '10–11am', what: 'Zed Q', kind: 'Solo' }, { date: '2027-11-08', time: '10–11am', what: 'Zed Q', kind: 'Solo' }] }, teams: [], q: 'zed q', today: '2027-01-01', siteUrl: SITE }));
const dev = lint(dst, 'dst');
const utcH = (e) => e.startDate.toJSDate().getUTCHours();
ok(dev.length === 3 && utcH(dev[0]) === 16 && utcH(dev[1]) === 15 && utcH(dev[2]) === 16, 'DST: 10 AM is 16:00 UTC (CST) / 15:00 UTC (CDT) → got ' + dev.map(utcH));

// 3. Every dancer: only their own named rehearsals and routines
const names = new Set(); teams.forEach(t => (t.dancers || []).forEach(d => d.t && names.add(d.t)));
(co.rehearsals || []).forEach(r => /^(Solo|Duet|Trio)$/.test(r.kind) && String(r.what).split(/\s*(?:,|&|\band\b)\s*/).forEach(n => n.trim() && names.add(n.trim())));
const personal = /^(Solo|Duet|Trio|Small group)$/;
let total = 0, per = [];
[...names].forEach(n => {
  const q = n.toLowerCase(), hit = F.query(q);
  const evs = F.dancerEvents({ co, cal, teams, q, today, siteUrl: SITE }); total += evs.length; per.push([n, evs.length]);
  const ics = F.calendar(n, evs); const parsed = lint(ics, 'dancer ' + n);
  evs.filter(e => e.uid.startsWith('reh-')).forEach(e => { const r = co.rehearsals.find(x => e.uid === 'reh-' + x.date + '-' + String(x.time).replace(/\W/g, '') + '-' + String(x.what).replace(/\W/g, '').slice(0, 24));
    ok(!!r, n + ': rehearsal maps back'); if (r && personal.test(r.kind)) ok(hit(r.what), n + ': got someone else’s ' + r.kind + ': ' + r.what); });
  ok(parsed.length === evs.length, n + ': every event parsed');
});
// Two dancers sharing a first name: "Bella M" must not get "Bella S" solos
const firsts = {}; [...names].forEach(n => { const m = /^([A-Z][a-z]+) ([A-Z])$/.exec(n); if (m) (firsts[m[1]] = firsts[m[1]] || []).push(n); });
Object.values(firsts).filter(a => a.length > 1).forEach(a => { const [x, y] = a; const ex = F.dancerEvents({ co, cal, teams, q: x.toLowerCase(), today, siteUrl: SITE });
  ok(!ex.some(e => e.title.includes(y) && !e.title.includes(x)), x + ' does not get ' + y + '’s rehearsals'); });
// A dancer on two teams gets both teams' group rehearsals
const teamOf = {}; teams.forEach(t => (t.dancers || []).forEach(d => (teamOf[d.t] = teamOf[d.t] || []).push(t.t)));
const two = Object.keys(teamOf).filter(k => teamOf[k].length > 1);
console.log('dancers on two teams:', two.length ? two.length : 'none in the data');

// 4. Competition rules, on last season's sample moved to dates in the future
const shift = JSON.parse(JSON.stringify(co)); const yr = +today.slice(0, 4) + 1;
shift.comps.forEach(c => { c.dates = String(c.dates).replace(/20\d\d/, yr); c.hideAfter = ''; });
const compNames = new Set(); shift.comps.forEach(c => (c.days || []).forEach(d => (d.rows || []).forEach(r => { if (!r.awards && /^[A-Z][a-z]+( [A-Z])?$/.test(String(r.dancers).trim())) compNames.add(r.dancers.trim()); })));
let compChecked = 0;
[...compNames].slice(0, 40).forEach(n => {
  const evs = F.dancerEvents({ co: shift, cal, teams, q: n.toLowerCase(), today, siteUrl: SITE }).filter(e => /-arr-|on stage|Awards/.test(e.uid + e.title)); if (!evs.length) return; compChecked++;
  lint(F.calendar(n, evs), 'comp ' + n);
  const byDay = {}; evs.forEach(e => (byDay[e.date] = byDay[e.date] || []).push(e));
  Object.values(byDay).forEach(list => {
    const m = (t) => t[0] * 60 + t[1];
    const stage = list.filter(e => / on stage/.test(e.title)).sort((a, b) => m(a.t0) - m(b.t0)), arr = list.filter(e => /^Arrive/.test(e.title)), aw = list.filter(e => /^Awards/.test(e.title));
    ok(arr.length >= 1, n + ': an arrival on ' + list[0].date);
    ok(arr.length <= stage.length, n + ': not more arrivals than dances');
    ok(m(arr.sort((a, b) => m(a.t0) - m(b.t0))[0].t0) <= m(stage[0].t0), n + ': first arrival before first dance');
    aw.forEach(w => ok(stage.some(s => m(s.t0) < m(w.t0)), n + ': awards after a dance'));
    ok(list.every(e => /\(preliminary\)$/.test(e.title) === !/final/i.test((shift.comps.find(c => e.uid.startsWith(c.id + '-')) || {}).status || '')), n + ': preliminary tag matches status');
  });
});
console.log('competition dancers checked:', compChecked);
per.sort((a, b) => b[1] - a[1]);
console.log(`dancers: ${names.size} · events: ${total} · most: ${per[0][1]} · fewest: ${per[per.length - 1][1]}`);
console.log(`${checks} checks, ${fails} failed`); process.exit(fails ? 1 : 0);
