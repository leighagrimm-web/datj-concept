/**
 * Dance & All That Jazz: website sign-ups
 *
 * Receives free trial requests and audition sign-ups from the website,
 * adds each one as a new row in this spreadsheet, and emails the address
 * on the Settings tab (cell B2).
 *
 * Setup (one time):
 * 1. In the spreadsheet: Extensions > Apps Script. Delete what's there and paste this file.
 * 2. Click Save, then Deploy > New deployment > Select type: Web app.
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 3. Click Deploy, allow the permissions, and copy the Web app URL.
 * 4. Put that URL in the website (SIGNUP_URL).
 * 5. Type the front desk email in Settings!B2.
 */

var TABS = {
  trial: 'Trial requests',
  audition: 'Audition sign-ups'
};

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var data = JSON.parse((e && e.postData && e.postData.contents) || '{}');

    // Bots fill in the hidden "website" field; people never see it.
    if (data.website) return reply_({ ok: true });

    var type = data.type === 'audition' ? 'audition' : 'trial';
    var ss = SpreadsheetApp.getActive();
    var sheet = ss.getSheetByName(TABS[type]);

    var row = type === 'audition'
      ? [new Date(), data.first, data.last, data.age, data.currentClass, data.parent, data.email, data.phone, false, '', '']
      : [new Date(), data.first, data.last, data.age, data.className, data.dayTime, data.teacher, data.studio, data.parent, data.email, data.phone, false, '', ''];

    row = row.map(clean_);
    sheet.getRange(nextRow_(sheet), 1, 1, row.length).setValues([row]);

    notify_(ss, type, data);
    return reply_({ ok: true });
  } catch (err) {
    return reply_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

// First empty row, judged by column A (the checkbox column always has a value).
function nextRow_(sheet) {
  var colA = sheet.getRange('A:A').getValues();
  for (var i = colA.length - 1; i >= 0; i--) {
    if (colA[i][0] !== '') return i + 2;
  }
  return 2;
}

// Text only, trimmed, and never treated as a formula.
function clean_(v) {
  if (v === null || v === undefined) return '';
  if (typeof v !== 'string') return v;
  v = v.trim().slice(0, 500);
  return /^[=+\-@]/.test(v) ? "'" + v : v;
}

function notify_(ss, type, d) {
  var to = String(ss.getSheetByName('Settings').getRange('B2').getValue() || '').trim();
  if (!to) return;
  var who = [d.first, d.last].filter(Boolean).join(' ');
  var lines = type === 'audition'
    ? ['New audition sign-up from the website', '',
       'Dancer: ' + who, 'Age: ' + (d.age || ''), 'Current class or team: ' + (d.currentClass || ''), '',
       'Parent / guardian: ' + (d.parent || ''), 'Email: ' + (d.email || ''), 'Mobile: ' + (d.phone || '')]
    : ['New free trial request from the website', '',
       'Dancer: ' + who, 'Age: ' + (d.age || ''),
       'Class: ' + (d.className || '') + (d.dayTime ? ', ' + d.dayTime : '') + (d.teacher ? ' with ' + d.teacher : ''), '',
       'Parent / guardian: ' + (d.parent || ''), 'Email: ' + (d.email || ''), 'Mobile: ' + (d.phone || ''), '',
       'Next step: add the trial in Studio Pro, then check the box in the sheet.'];
  lines.push('', 'Sheet: ' + ss.getUrl());
  var subject = (type === 'audition' ? 'Audition sign-up: ' : 'Free trial request: ') + who;
  var opts = { to: to, subject: subject, body: lines.join('\n') };
  if (d.email && /@/.test(d.email)) opts.replyTo = d.email;
  MailApp.sendEmail(opts);
}

function reply_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
