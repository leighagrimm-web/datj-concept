// Reads Brittany's public Studio Pro "live schedule" feed (the one Studio Pro offers for websites).
// Shared by the website (in the browser) and the nightly GitHub job (in Node), so both read classes the same way.
(function (root) {
  const FEED_URL = 'https://app.gostudiopro.com/apps/api_classes_resp-ajax.php';
  const FEED_ID = 'zaqlxajd29jd260a7a4e0ac31309jasdklj21dx60a7a4e0ac353';
  const DAY = { monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu', friday: 'Fri', saturday: 'Sat', sunday: 'Sun' };

  const decode = (s) => s.replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&#0?39;|&apos;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#(\d+);/g, (m, n) => String.fromCharCode(+n));
  const lines = (html) => decode(html.replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '')).split('\n').map((x) => x.replace(/\s+/g, ' ').trim()).filter(Boolean);
  const toMin = (t) => { const m = /(\d{1,2}):(\d{2})\s*([AP]M)/i.exec(t || ''); if (!m) return null; let h = +m[1] % 12; if (/p/i.test(m[3])) h += 12; return h * 60 + +m[2]; };

  // feed HTML -> [{ key, season, name, note, day, time, start, end, mins, studio, location }]
  function parse(html) {
    const out = [];
    let season = '';
    const re = /<h2[^>]*>([\s\S]*?)<\/h2>|<div class=["']row-fluid([^"']*)["'][^>]*>([\s\S]*?)(?=<div class=["']row-fluid|<h2|$)/g;
    let m;
    while ((m = re.exec(html))) {
      if (m[1] !== undefined) { season = lines(m[1]).join(' '); continue; }
      if (/hidden-phone/.test(m[2])) continue; // column headings
      const cells = m[3].split(/<div class=["'][^"']*table_cell[^"']*["']>/).slice(1);
      if (cells.length < 3) continue;
      const smallAt = cells[0].search(/<small/i);
      const name = lines(smallAt >= 0 ? cells[0].slice(0, smallAt) : cells[0]).join(' ');
      const note = smallAt >= 0 ? lines(cells[0].slice(smallAt)).join('\n') : '';
      const when = lines(cells[1]);
      const where = lines(cells[2]);
      for (let i = 0; i < when.length; i++) {
        const day = DAY[when[i].toLowerCase()];
        if (!day) continue;
        const span = /(\d{1,2}:\d{2}\s*[AP]M)\s*to\s*(\d{1,2}:\d{2}\s*[AP]M)/i.exec(when[i + 1] || '');
        const start = span ? toMin(span[1]) : null, end = span ? toMin(span[2]) : null;
        out.push({ key: name + '|' + day + '|' + (span ? span[1] : ''), season, name, note, day,
          time: span ? span[1].replace(/\s*[AP]M/i, '') : '', start, end, mins: start != null && end != null ? end - start : null,
          studio: where[0] || '', location: where[1] || '' });
      }
    }
    return out;
  }

  // f_age asks Studio Pro which classes a dancer of that age can take (her own age rules)
  async function fetchClasses(fetchFn, age) {
    const body = new URLSearchParams({ action: 'get_classes', id: FEED_ID, l: '0', s: '0', tsearch: '', f_wday: '', f_age: age == null ? '' : String(age), f_loc: '', f_type: '' });
    const r = await fetchFn(FEED_URL, { method: 'POST', body: body.toString(), headers: { 'Content-Type': 'application/x-www-form-urlencoded' } });
    if (!r.ok) throw new Error('Studio Pro feed answered ' + r.status);
    return parse(await r.text());
  }

  // Full saved copy: every class plus the age range Studio Pro allows for it
  async function snapshot(fetchFn) {
    const all = await fetchClasses(fetchFn);
    if (!all.length) throw new Error('Studio Pro feed came back empty');
    const AGES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 25];
    const seen = {};
    for (const a of AGES) for (const c of await fetchClasses(fetchFn, a)) (seen[c.key] = seen[c.key] || []).push(a);
    return all.map((c) => { const s = seen[c.key] || []; return Object.assign({}, c, s.length ? { lo: s[0], hi: s.includes(25) ? 99 : s[s.length - 1] } : { lo: null, hi: null }); });
  }

  const api = { FEED_URL, FEED_ID, parse, fetchClasses, snapshot };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.StudioPro = api;
})(typeof window !== 'undefined' ? window : globalThis);
