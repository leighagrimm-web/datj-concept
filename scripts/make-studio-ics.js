// Builds studio.ics (the public "Subscribe to the studio calendar" feed) from calendar.json.
// Same code as the Apps Script feed (apps-script/calendar-feed.gs), so both always agree.
// Usage: node scripts/make-studio-ics.js calendar.json studio.ics https://site/
const fs = require('fs'), path = require('path'), vm = require('vm');
const [cal = 'calendar.json', out = 'studio.ics', site = 'https://leighagrimm-web.github.io/datj-concept/'] = process.argv.slice(2);
const box = { module: { exports: {} } }; vm.createContext(box);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'apps-script', 'calendar-feed.gs'), 'utf8'), box);
const FEED = box.module.exports;
const today = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Chicago' });
const list = JSON.parse(fs.readFileSync(cal, 'utf8'));
const ics = FEED.calendar('Dance & All That Jazz', FEED.studioEvents(list, site, today));
// Keep the file unchanged when only the timestamp would change (no pointless commits)
const strip = (s) => s.replace(/^DTSTAMP:.*$/mg, '');
if (fs.existsSync(out) && strip(fs.readFileSync(out, 'utf8')) === strip(ics)) { console.log('studio.ics unchanged'); process.exit(0); }
fs.writeFileSync(out, ics); console.log('studio.ics:', (ics.match(/BEGIN:VEVENT/g) || []).length, 'dates');
