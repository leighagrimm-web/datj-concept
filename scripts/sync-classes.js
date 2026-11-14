// Nightly saved copy of the class schedule from Studio Pro -> classes.json
// Run by .github/workflows/sync-classes.yml. Only writes the file if a class actually changed.
const fs = require('fs');
const path = require('path');
const StudioPro = require('./studiopro.js');

(async () => {
  const file = path.join(__dirname, '..', 'classes.json');
  const old = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : { classes: [] };
  const classes = await StudioPro.snapshot(fetch);
  // Safety net: a near-empty answer means the feed hiccuped, not that she cancelled every class
  if (classes.length < Math.max(5, Math.floor((old.classes || []).length / 2))) {
    throw new Error('Only ' + classes.length + ' classes came back (had ' + old.classes.length + '). Keeping the old copy.');
  }
  if (JSON.stringify(classes) === JSON.stringify(old.classes)) { console.log('No changes in Studio Pro.'); return; }
  fs.writeFileSync(file, JSON.stringify({ updated: new Date().toISOString(), source: 'Studio Pro live schedule', classes }, null, 1) + '\n');
  console.log('Saved ' + classes.length + ' classes.');
})().catch((e) => { console.error(e.message); process.exit(1); });
