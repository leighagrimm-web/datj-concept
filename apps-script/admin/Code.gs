/**
 * Dance & All That Jazz: admin Publish backend
 *
 * One script, two web app deployments (tools/deploy-admin.js sets both up and keeps their URLs):
 *   signin  : Execute as Me, Only myself. Opening it with the owner's Google account gives the admin a sign-in
 *             pass (good for 12 hours) and sends her back to the admin page. Anyone else gets plain text.
 *   public  : Execute as Me, Anyone. The admin page posts here (text/plain, so no CORS preflight). Every action
 *             checks the sign-in pass first and answers only the owner.
 *
 * Publish: checks the content on the server, saves it as a new version on the History tab (the full draft,
 * including the private Company Central edits, which stay in this Sheet), then writes the public part to
 * content.json in the site's GitHub repo. The website reads content.json.
 *
 * Script Properties (Project Settings → Script Properties), typed by hand:
 *   GITHUB_TOKEN    fine-grained token: only the site repo, Contents read and write
 *   GITHUB_REPO     owner/name, e.g. leighagrimm-web/datj-test
 *   GITHUB_BRANCH   main
 *   ADMIN_PAGE_URL  the admin page, e.g. https://leighagrimm-web.github.io/datj-test/admin.html
 *   ENVIRONMENT     TEST or LIVE
 * Set by setup() (run once from the editor, signed in as the owner):
 *   OWNER_EMAIL     the Google account allowed into the admin
 *   SIGNIN_SECRET   random key that signs the sign-in passes
 */

var HISTORY = 'History';
var HEAD = ['Version', 'Published', 'By', 'Size (KB)', 'What changed', 'Website', 'Data'];
var DATA_COL = 7;          // the content JSON starts here, split into pieces across columns
var CHUNK = 45000;         // a cell holds at most 50,000 characters
var PASS_HOURS = 12;
var MAX_BYTES = 3000000;   // the whole draft
var MAX_PUBLIC_BYTES = 1500000;

// Top-level keys the admin's pick() produces, and their types. Anything else is dropped.
var KEYS = {
  recital: 'boolean', season: 'object', calSheet: 'string', banner: 'object', home: 'object', nav: 'array',
  prices: 'object', photos: 'object', featured: 'array', calendar: 'array', coEdit: 'objectOrNull',
  policies: 'array', rc: 'array', lists: 'object', texts: 'object', teachers: 'object', staffV: 'number', staff: 'array'
};
// What the public website reads. Company Central edits (coEdit) and the calendar sheet link stay private.
var PUBLIC_KEYS = ['recital', 'season', 'banner', 'home', 'nav', 'prices', 'photos', 'featured', 'calendar',
  'policies', 'rc', 'lists', 'texts', 'teachers', 'staffV', 'staff'];
var SECTION_NAMES = {
  recital: 'Annual Performance switch', season: 'Between seasons page', calSheet: 'Calendar sheet link', banner: 'Top banner',
  home: 'Home', nav: 'Menu', prices: 'Sessions & prices', photos: 'Photos', featured: 'Featured events', calendar: 'Studio calendar',
  coEdit: 'Company Central', policies: 'Policies', rc: 'Annual Performance', lists: 'Page cards', texts: 'Page text',
  teachers: 'Teachers', staffV: '', staff: 'Instructors & staff'
};
var NAV_IDS = ['classes', 'pricing', 'company', 'about', 'families', 'shop'];

// ---------------------------------------------------------------- one-time setup (run from the editor)

function setup() {
  var p = PropertiesService.getScriptProperties();
  var me = Session.getEffectiveUser().getEmail();
  p.setProperty('OWNER_EMAIL', String(me).toLowerCase());
  if (!p.getProperty('SIGNIN_SECRET')) p.setProperty('SIGNIN_SECRET', Utilities.getUuid() + Utilities.getUuid());
  historySheet_();
  var need = ['GITHUB_TOKEN', 'GITHUB_REPO', 'GITHUB_BRANCH', 'ADMIN_PAGE_URL', 'ENVIRONMENT'].filter(function (k) { return !p.getProperty(k); });
  console.log('Owner: ' + me + '. History tab ready.' + (need.length ? ' Still to add in Script Properties: ' + need.join(', ') : ' All Script Properties are set.'));
}

// Run from the editor after adding the token: checks the repo can be read with it (writes nothing).
function checkGitHub() {
  var c = gh_();
  var r = UrlFetchApp.fetch('https://api.github.com/repos/' + c.repo, { headers: c.headers, muteHttpExceptions: true });
  var j = JSON.parse(r.getContentText() || '{}');
  if (r.getResponseCode() !== 200) throw new Error('GitHub said ' + r.getResponseCode() + ': ' + (j.message || ''));
  console.log('OK: ' + j.full_name + (j.permissions && j.permissions.push ? ' (can write)' : ' (read only: the token needs Contents read and write)'));
}

// ---------------------------------------------------------------- web apps

// signin deployment (Only myself). The URL holds no return address: the pass only ever goes to ADMIN_PAGE_URL.
function doGet(e) {
  var me = String(Session.getActiveUser().getEmail() || '').toLowerCase();
  if (!me || me !== ownerEmail_()) return text_('Only the studio owner can open the admin.');
  var adminUrl = prop_('ADMIN_PAGE_URL');
  if (!/^https:\/\//.test(adminUrl)) return text_('The admin page address (ADMIN_PAGE_URL) isn’t set up yet.');
  var t = HtmlService.createTemplate(SIGNIN_HTML);
  t.href = adminUrl + '#signin=' + makePass_(me);
  t.email = me;
  t.env = prop_('ENVIRONMENT') || 'TEST';
  return t.evaluate().setTitle('Sign in · Studio admin').addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

// public deployment. Body: {"action": "load" | "publish" | "history", "pass": "...", ...}
function doPost(e) {
  var req;
  try { req = JSON.parse((e && e.postData && e.postData.contents) || '{}'); } catch (err) { return json_({ ok: false, error: 'That request couldn’t be read.' }); }
  var who = checkPass_(req.pass);
  if (!who.ok) return json_({ ok: false, code: 'signin', error: who.error });
  try {
    if (req.action === 'load') return json_(load_(who.email));
    if (req.action === 'publish') return json_(publish_(who.email, req));
    if (req.action === 'history') return json_({ ok: true, versions: history_(20) });
    return json_({ ok: false, error: 'Unknown action.' });
  } catch (err) {
    console.error(req.action, err && err.stack || err);
    return json_({ ok: false, error: 'Something went wrong on the server: ' + (err && err.message || err) });
  }
}

// ---------------------------------------------------------------- owner and sign-in passes

function prop_(k) { return String(PropertiesService.getScriptProperties().getProperty(k) || ''); }
function ownerEmail_() { return prop_('OWNER_EMAIL').toLowerCase(); }

function sign_(s) {
  var key = prop_('SIGNIN_SECRET');
  if (!key) throw new Error('Run setup() once from the editor first.');
  return Utilities.base64EncodeWebSafe(Utilities.computeHmacSha256Signature(s, key)).replace(/=+$/, '');
}
function makePass_(email) {
  var body = Utilities.base64EncodeWebSafe(JSON.stringify({ e: email, x: Date.now() + PASS_HOURS * 3600000 }), Utilities.Charset.UTF_8).replace(/=+$/, '');
  return body + '.' + sign_(body);
}
function checkPass_(pass) {
  var bad = { ok: false, error: 'Please sign in again.' };
  if (typeof pass !== 'string' || pass.length > 600 || pass.indexOf('.') < 0) return bad;
  var parts = pass.split('.');
  if (parts.length !== 2 || !safeEqual_(sign_(parts[0]), parts[1])) return bad;
  var data;
  try { data = JSON.parse(Utilities.newBlob(Utilities.base64DecodeWebSafe(parts[0] + '=='.slice(0, (4 - parts[0].length % 4) % 4))).getDataAsString()); } catch (err) { return bad; }
  if (!data || data.x < Date.now()) return { ok: false, error: 'Your sign-in timed out. Please sign in again. Your changes are still here.' };
  if (String(data.e).toLowerCase() !== ownerEmail_()) return { ok: false, error: 'Only the studio owner can do that.' };
  return { ok: true, email: data.e };
}
function safeEqual_(a, b) {
  if (a.length !== b.length) return false;
  var d = 0; for (var i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

// ---------------------------------------------------------------- load / publish / history

function load_(email) {
  var last = lastVersion_();
  return { ok: true, email: email, env: prop_('ENVIRONMENT') || 'TEST', version: last ? last.version : 0,
    publishedAt: last ? last.at : '', by: last ? last.by : '', content: last ? last.content : null };
}

function publish_(email, req) {
  var check = validate_(req.content);
  if (check.errors.length) return { ok: false, code: 'invalid', error: 'Some things need fixing before this can go live:', errors: check.errors.slice(0, 12) };
  var full = check.content;
  var fullText = JSON.stringify(full);
  if (fullText.length > MAX_BYTES) return { ok: false, error: 'This is too big to publish (' + Math.round(fullText.length / 1024) + ' KB). A photo may be saved inside the text; use a photo link instead.' };

  var lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) return { ok: false, code: 'busy', error: 'Another publish is still running. Try again in a moment.' };
  try {
    var last = lastVersion_();
    var latest = last ? last.version : 0;
    // Published from another device (or another tab) since this draft was opened.
    if (!req.force && Number(req.baseVersion || 0) !== latest) {
      return { ok: false, code: 'stale', latest: latest, publishedAt: last ? last.at : '', by: last ? last.by : '',
        error: 'Version ' + latest + ' was published from another device or tab after you opened the admin.' };
    }
    var changed = last ? changedSections_(last.content, full) : ['First version'];
    if (last && !changed.length) return { ok: true, unchanged: true, version: latest, publishedAt: last.at, content: last.content };

    var version = latest + 1;
    var at = new Date();
    var pub = { _published: { version: version, at: at.toISOString() } };
    PUBLIC_KEYS.forEach(function (k) { if (k in full) pub[k] = full[k]; });
    var pubText = JSON.stringify(pub);
    if (pubText.length > MAX_PUBLIC_BYTES) return { ok: false, error: 'The website part is too big to publish (' + Math.round(pubText.length / 1024) + ' KB).' };

    var sh = historySheet_();
    var row = sh.getLastRow() + 1;
    var chunks = [];
    for (var i = 0; i < fullText.length; i += CHUNK) chunks.push(fullText.slice(i, i + CHUNK));
    sh.getRange(row, 1, 1, DATA_COL - 1 + chunks.length).setValues([[version, at, email, Math.round(fullText.length / 1024), changed.join(', '), 'Sending…'].concat(chunks)]);
    sh.getRange(row, 2).setNumberFormat('yyyy-mm-dd h:mm am/pm');
    SpreadsheetApp.flush();

    var site;
    try { site = ghPut_('content.json', pubText, 'Content v' + version + ' published from the admin (' + changed.join(', ').slice(0, 120) + ')'); }
    catch (err) {
      sh.getRange(row, 6).setValue('Failed: ' + String(err && err.message || err).slice(0, 300));
      return { ok: false, code: 'site', version: version, publishedAt: at.toISOString(), content: full,
        error: 'Saved as version ' + version + ', but the website couldn’t be updated: ' + (err && err.message || err) + '. Press Publish again to retry.' };
    }
    sh.getRange(row, 6).setValue(site.url ? '=HYPERLINK("' + site.url + '","Updated")' : 'Updated');
    return { ok: true, version: version, publishedAt: at.toISOString(), changed: changed, content: full };
  } finally {
    lock.releaseLock();
  }
}

function history_(n) {
  var sh = historySheet_();
  var last = sh.getLastRow();
  if (last < 2) return [];
  var from = Math.max(2, last - n + 1);
  return sh.getRange(from, 1, last - from + 1, 6).getDisplayValues().reverse().map(function (r) {
    return { version: Number(r[0]), at: r[1], by: r[2], kb: Number(r[3]), changed: r[4], site: r[5] };
  });
}

// ---------------------------------------------------------------- the History tab

function historySheet_() {
  var ss = SpreadsheetApp.getActive();
  var sh = ss.getSheetByName(HISTORY);
  if (!sh) { sh = ss.insertSheet(HISTORY); sh.setFrozenRows(1); }
  // Headers: add any missing ones on the end, so older rows never shift.
  var have = sh.getLastColumn() ? sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0] : [];
  if (!have[0]) { sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight('bold'); sh.setColumnWidths(DATA_COL, 1, 120); }
  return sh;
}

function lastVersion_() {
  var sh = historySheet_();
  var row = sh.getLastRow();
  if (row < 2) return null;
  var width = Math.max(DATA_COL, sh.getLastColumn());
  var r = sh.getRange(row, 1, 1, width).getValues()[0];
  var text = r.slice(DATA_COL - 1).join('');
  var content = null;
  try { content = JSON.parse(text); } catch (err) { throw new Error('The last saved version (row ' + row + ') couldn’t be read.'); }
  var at = r[1] instanceof Date ? r[1].toISOString() : String(r[1]);
  return { version: Number(r[0]) || 0, at: at, by: String(r[2]), content: content };
}

function changedSections_(a, b) {
  var out = [];
  Object.keys(KEYS).forEach(function (k) {
    if (JSON.stringify(a ? a[k] : undefined) !== JSON.stringify(b[k]) && SECTION_NAMES[k]) out.push(SECTION_NAMES[k]);
  });
  return out;
}

// ---------------------------------------------------------------- server-side checks (never trust the page)

function validate_(c) {
  var errors = [];
  if (!c || typeof c !== 'object' || Array.isArray(c)) return { errors: ['Nothing to publish.'], content: null };
  var out = {};
  Object.keys(KEYS).forEach(function (k) {
    if (!(k in c)) return;
    var v = c[k], t = KEYS[k];
    var ok = t === 'array' ? Array.isArray(v) : t === 'objectOrNull' ? (v === null || (typeof v === 'object' && !Array.isArray(v)))
      : t === 'object' ? (v && typeof v === 'object' && !Array.isArray(v)) : typeof v === t;
    if (!ok) { errors.push((SECTION_NAMES[k] || k) + ': not in the expected format.'); return; }
    out[k] = v;
  });
  // Every string, anywhere: length limit and no script links.
  walk_(out, '', 0, errors);
  (out.calendar || []).forEach(function (e, i) {
    var name = '“' + String(e && e.title || 'Date ' + (i + 1)) + '”';
    if (!e || typeof e !== 'object') { errors.push('Studio calendar: item ' + (i + 1) + ' is empty.'); return; }
    if (e.start && !/^\d{4}-\d{2}-\d{2}$/.test(e.start)) errors.push('Studio calendar ' + name + ': the start date isn’t a date.');
    if (e.end && !/^\d{4}-\d{2}-\d{2}$/.test(e.end)) errors.push('Studio calendar ' + name + ': the end date isn’t a date.');
    if (e.start && e.end && e.end < e.start) errors.push('Studio calendar ' + name + ': ends before it starts.');
  });
  (out.nav || []).forEach(function (n) { if (!n || NAV_IDS.indexOf(n.id) < 0) errors.push('Menu: an item isn’t one of the site’s pages.'); });
  (out.staff || []).forEach(function (s, i) { if (!s || !String(s.name || '').trim()) errors.push('Instructors & staff: person ' + (i + 1) + ' needs a name.'); });
  return { errors: errors, content: out };
}

function walk_(v, path, depth, errors) {
  if (errors.length > 30) return;
  if (depth > 12) { errors.push(path + ': nested too deeply.'); return; }
  if (typeof v === 'string') {
    if (v.length > 30000) errors.push(label_(path) + ': text is too long (' + v.length + ' characters).');
    var s = v.replace(/[\s\u0000-\u001f]+/g, '').toLowerCase();
    if (/^(javascript|vbscript):/.test(s) || (/^data:/.test(s) && !/^data:image\/(png|jpe?g|webp|gif);/.test(s))) errors.push(label_(path) + ': that link type isn’t allowed.');
    return;
  }
  if (v === null || typeof v === 'number' || typeof v === 'boolean') return;
  if (Array.isArray(v)) {
    if (v.length > 3000) { errors.push(label_(path) + ': too many items.'); return; }
    v.forEach(function (x, i) { walk_(x, path + '[' + i + ']', depth + 1, errors); });
    return;
  }
  if (typeof v === 'object') { Object.keys(v).forEach(function (k) { walk_(v[k], path ? path + '.' + k : k, depth + 1, errors); }); return; }
  errors.push(label_(path) + ': unexpected value.');
}
function label_(path) { var top = String(path).split(/[.[]/)[0]; return (SECTION_NAMES[top] || top) + (path !== top ? ' (' + path + ')' : ''); }

// ---------------------------------------------------------------- GitHub

function gh_() {
  var token = prop_('GITHUB_TOKEN'), repo = prop_('GITHUB_REPO');
  if (!token || !/^[\w.-]+\/[\w.-]+$/.test(repo)) throw new Error('GITHUB_TOKEN and GITHUB_REPO aren’t set up in Script Properties');
  return { repo: repo, branch: prop_('GITHUB_BRANCH') || 'main',
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28' } };
}

function ghPut_(path, text, message) {
  var c = gh_();
  var api = 'https://api.github.com/repos/' + c.repo + '/contents/' + path;
  for (var attempt = 0; attempt < 2; attempt++) {
    var sha = null;
    var g = UrlFetchApp.fetch(api + '?ref=' + encodeURIComponent(c.branch), { headers: c.headers, muteHttpExceptions: true });
    if (g.getResponseCode() === 200) sha = JSON.parse(g.getContentText()).sha;
    else if (g.getResponseCode() !== 404) throw new Error('GitHub said ' + g.getResponseCode() + ' when reading ' + path);
    var body = { message: message, content: Utilities.base64Encode(Utilities.newBlob(text).getBytes()), branch: c.branch };
    if (sha) body.sha = sha;
    var r = UrlFetchApp.fetch(api, { method: 'put', contentType: 'application/json', headers: c.headers, payload: JSON.stringify(body), muteHttpExceptions: true });
    var code = r.getResponseCode();
    if (code === 200 || code === 201) { var j = JSON.parse(r.getContentText()); return { url: j.commit && j.commit.html_url, sha: j.content && j.content.sha }; }
    if (code !== 409 && code !== 422) throw new Error('GitHub said ' + code + ': ' + (JSON.parse(r.getContentText() || '{}').message || ''));
    // 409/422: the file changed between the read and the write (e.g. the nightly schedule bot). Read again once.
  }
  throw new Error('GitHub kept reporting a conflict');
}

// ---------------------------------------------------------------- replies

function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function text_(s) { return ContentService.createTextOutput(s).setMimeType(ContentService.MimeType.TEXT); }

var SIGNIN_HTML = '<!doctype html><html><head><base target="_top"><meta charset="utf-8">'
  + '<style>body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#F5F6F5;color:#111}'
  + '.c{max-width:420px;margin:12vh auto;padding:28px 24px;background:#fff;border:1px solid #E2E4E3;border-top:4px solid #00ADB5}'
  + 'h1{font-size:22px;margin:0 0 8px}p{color:#5C6360;line-height:1.5;margin:0 0 20px}'
  + 'a.b{display:flex;align-items:center;justify-content:center;min-height:48px;background:#00ADB5;color:#000;font-weight:700;'
  + 'letter-spacing:.12em;text-transform:uppercase;font-size:13px;text-decoration:none}a.b:focus-visible{outline:3px solid #111;outline-offset:2px}'
  + '.t{display:inline-block;background:#FFE08A;padding:2px 8px;font-size:12px;font-weight:700;margin-bottom:12px}</style></head><body>'
  + '<div class="c"><? if (env !== "LIVE") { ?><span class="t">TEST</span><? } ?><h1>You’re signed in</h1>'
  + '<p>Signed in as <b><?= email ?></b>. This keeps you signed in on this device for 12 hours.</p>'
  + '<a class="b" href="<?= href ?>">Continue to the admin</a></div></body></html>';
