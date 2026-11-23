"""Convert a .dc.html design board into a standalone responsive HTML page.

Usage: python3 build.py <src.dc.html> <out_dir> <title> <link_map_json>
"""
import json, os, re, shutil, sys

src, out_dir, title, link_map = sys.argv[1], sys.argv[2], sys.argv[3], json.loads(sys.argv[4])
s = open(src, encoding='utf-8').read()

BLOBS = {
    '286fd241d1513c8560778f6c9485c849': 'circle_teal', '4d7be258ce6fa8d94b6d1768aaebeb5e': 'circle_black',
    'f1cf50e6bf7f4b398bc5e614741099d7': 'circle_white', 'a83b68c2c7d46f529662f6fa0d03a000': 'stacked_teal',
    '4d9adbc004300b9fc4604dd6a925f168': 'stacked_black', '07c9d793e061f579a5a92c859924b6b7': 'stacked_white',
    'e22635504e2cc0613431952c687e5b78': 'horizontal_teal', '138e37fab588f5c6a71a1ed8c60d6eb1': 'horizontal_black',
    'd47310466b56b68c26993bfe15b03782': 'horizontal_white', '258fa0f8234438e579537e1fb7b23735': 'horizontal_twotone',
    '6f12c517e72f801487c748f7a2f2d215': 'monogram_teal', '28339d4b4bdb9a152407ab109bfb346c': 'monogram_white',
    'f572bf5a328c23dee1ac803b43bac447': 'monogram_black', 'a483dd3382c94b3cd0d6c58ec88eeadf': 'monogram_mark-black',
    'e659d6075006a338350e5f457b232644': 'monogram_mark-teal', 'e2c2fbd8979512fa4dfc07c60b6a53e6': 'lockup_teal',
    '2d8278cbf35c1ea49891145407bc527a': 'lockup_reverse', '86ca783c65dd2777bbf35bccc617e4ea': 'horizontal_teal-white',
    'a89705cd62af3d9be8fb80be1c9c13fa': 'stacked_teal-white',
    '4101017fc2f71668014877efc0e8b3a6': 'stacked_teal-white',
}
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_DIRS = [os.path.join(HERE, 'logos', 'datj-logos2'), os.path.join(HERE, 'logos', 'datj-logos')]

helmet = re.search(r'<helmet>(.*?)</helmet>', s, re.S).group(1)
body = re.search(r'<x-dc>.*?</helmet>(.*)</x-dc>', s, re.S).group(1)
logic = re.search(r'<script type="text/x-dc" data-dc-script[^>]*>(.*?)</script>', s, re.S).group(1)
for _k, _v in link_map.items(): logic = logic.replace("'" + _k, "'" + _v)

used = set()
def blob(m):
    name = BLOBS[m.group(1)]
    used.add(name)
    return f'logos/{name}.svg'
body = re.sub(r'/_blob/([0-9a-f]{32})', blob, body)
helmet = re.sub(r'/_blob/([0-9a-f]{32})', blob, helmet)
for k, v in link_map.items():
    body = body.replace(f'href="{k}#', f'href="{v}#').replace(f'href="{k}"', f'href="{v}"')
body = body.replace('href="index.html#', 'href="index.html#')
_lm = link_map
out_name = sys.argv[5] if len(sys.argv) > 5 else 'index.html'

runtime = r'''
(function(){
  class DCLogic { constructor(props){ this.props = props || {}; this.state = {}; } setState(p){ Object.assign(this.state, p); schedule(); } forceUpdate(){ schedule(); } }
  window.DCLogic = DCLogic;
  __LOGIC__
  const tpl = document.getElementById('dc-template');
  const root = document.getElementById('dc-root');
  const comp = new Component({});
  const holeOnly = /^\s*\{\{\s*([^}]+?)\s*\}\}\s*$/;
  function lookup(path, scope){
    path = path.trim();
    if (path === 'true') return true; if (path === 'false') return false;
    if (/^-?\d+(\.\d+)?$/.test(path)) return Number(path);
    let cur = scope;
    for (const part of path.split('.')) { if (cur == null) return undefined; cur = cur[part]; }
    return cur;
  }
  function interp(str, scope){ return str.replace(/\{\{\s*([^}]+?)\s*\}\}/g, (_, p) => { const v = lookup(p, scope); return v == null ? '' : String(v); }); }
  function renderChildren(srcNode, scope, parent){ srcNode.childNodes.forEach(n => renderNode(n, scope, parent)); }
  function renderNode(n, scope, parent){
    if (n.nodeType === 3) { parent.appendChild(document.createTextNode(interp(n.nodeValue, scope))); return; }
    if (n.nodeType !== 1) return;
    const tag = n.tagName.toLowerCase();
    if (tag === 'sc-for') {
      const list = lookup(holeOnly.exec(n.getAttribute('list'))[1], scope) || [];
      const as = n.getAttribute('as') || 'item';
      list.forEach((item, i) => renderChildren(n, Object.assign({}, scope, { [as]: item, $index: i }), parent));
      return;
    }
    if (tag === 'sc-if') {
      if (lookup(holeOnly.exec(n.getAttribute('value'))[1], scope)) renderChildren(n, scope, parent);
      return;
    }
    const el = document.importNode(n, false);
    for (const a of Array.from(n.attributes)) {
      const name = a.name, val = a.value;
      if (name.startsWith('hint-')) { el.removeAttribute(name); continue; }
      if (!val.includes('{{')) continue;
      const m = holeOnly.exec(val);
      if (/^on[a-z]+$/i.test(name) && m) {
        el.removeAttribute(name);
        const fn = lookup(m[1], scope);
        if (typeof fn === 'function') el.addEventListener(name.slice(2).toLowerCase(), fn);
        continue;
      }
      el.setAttribute(name, interp(val, scope));
    }
    renderChildren(n, scope, el);
    parent.appendChild(el);
  }
  function chipArrows(el) {
    if (el.parentNode && el.parentNode.classList && el.parentNode.classList.contains('h-chipwrap')) return;
    const wrap = document.createElement('div'); wrap.className = 'h-chipwrap'; el.parentNode.insertBefore(wrap, el); wrap.appendChild(el);
    const mk = (dir) => { const b = document.createElement('button'); b.type = 'button'; b.className = 'h-chiparrow h-chiparrow-' + dir; b.setAttribute('aria-label', dir === 'l' ? 'Scroll filters left' : 'More filters'); b.textContent = dir === 'l' ? '‹' : '›';
      b.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); el.scrollBy({ left: (dir === 'l' ? -1 : 1) * Math.max(160, el.clientWidth * 0.7), behavior: 'smooth' }); }); wrap.appendChild(b); return b; };
    const L = mk('l'), R = mk('r');
    const upd = () => { const more = el.scrollWidth - el.clientWidth > 4; wrap.classList.toggle('can-l', more && el.scrollLeft > 4); wrap.classList.toggle('can-r', more && el.scrollLeft < el.scrollWidth - el.clientWidth - 4); };
    el.addEventListener('scroll', upd, { passive: true }); upd(); setTimeout(upd, 300);
  }
  window.addEventListener('resize', () => document.querySelectorAll('.h-chips').forEach(el => el.dispatchEvent(new Event('scroll'))));
  let pending = false;
  function schedule(){ if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; render(); }); } }
  function render(){
    const inputs = Array.from(root.querySelectorAll('input, select, textarea'));
    const fkey = (i) => i.type + '|' + (i.id || i.getAttribute('aria-label') || i.name || i.placeholder || ''); const saved = inputs.map(i => i.value), savedK = inputs.map(fkey);
    const active = inputs.indexOf(document.activeElement);
    const wy = window.scrollY, wx = window.scrollX;
    const sideScroll = Array.from(root.querySelectorAll('.p-week')).map(e => e.scrollLeft);
    const chipScroll = Array.from(root.querySelectorAll('.h-chips')).map(e => e.scrollLeft);
    const keep = {}; root.querySelectorAll('[data-keep-scroll]').forEach(e => { keep[e.getAttribute('data-keep-scroll')] = [e.scrollTop, e.scrollLeft]; });
    const fromFocus = document.activeElement && document.activeElement !== document.body && root.contains(document.activeElement) ? document.activeElement : null;
    const tapped = window.__lastTap && root.contains(window.__lastTap) && (Date.now() - (window.__lastTapAt || 0) < 1500) ? window.__lastTap : null;
    const anchorEl = (tapped || fromFocus) ? (tapped || fromFocus).closest('section[id]') : null;
    const anchorId = anchorEl ? anchorEl.id : null, anchorTop = anchorEl ? anchorEl.getBoundingClientRect().top : 0;
    const vals = comp.renderVals();
    const frag = document.createDocumentFragment();
    renderChildren(tpl.content, vals, frag);
    const live = {}; root.querySelectorAll('[data-keep-node]').forEach(e => { live[e.getAttribute('data-keep-node')] = e; });
    frag.querySelectorAll('[data-keep-node]').forEach(e => { const old = live[e.getAttribute('data-keep-node')]; if (old) e.replaceWith(old); });
    // Safari: hold the page's height while the new copy swaps in, so pictures that are still decoding can't shrink the page and bounce the scroll position
    const holdH = root.offsetHeight; root.style.minHeight = holdH + 'px';
    root.replaceChildren(frag);
    const imgsNow = Array.from(root.querySelectorAll('img')).filter(im => !im.complete);
    const release = () => { root.style.minHeight = ''; };
    if (imgsNow.length) { let left = imgsNow.length; const one = () => { if (--left <= 0) release(); }; imgsNow.forEach(im => { im.addEventListener('load', one, { once: true }); im.addEventListener('error', one, { once: true }); }); setTimeout(release, 2500); }
    else requestAnimationFrame(() => requestAnimationFrame(release));
    root.querySelectorAll('video[autoplay]').forEach(v => {
      if (!v.dataset.ready) { v.dataset.ready = '1'; v.muted = true; v.defaultMuted = true; v.setAttribute('muted', ''); v.setAttribute('playsinline', ''); v.playsInline = true; }
      if (v.paused) { try { const pr = v.play(); if (pr && pr.catch) pr.catch(() => {}); } catch (e) {} }
      if (!v.dataset.watch) { v.dataset.watch = '1';
        const ok = () => { if (v.currentTime > 0 && !v.paused) { v._moving = true; const w = v.closest('.h-vwrap'); if (w) w.classList.remove('needs-tap'); } };
        v.addEventListener('timeupdate', ok); v.addEventListener('playing', ok);
        v.addEventListener('pause', () => { v._moving = false; }); }
    });
    const now = Array.from(root.querySelectorAll('input, select, textarea'));
    if (now.length === saved.length) now.forEach((i, k) => { if (saved[k] && savedK[k] === fkey(i) && i.type !== 'password') i.value = saved[k]; });
    // keep the page where it was: hold the section being used still on screen
    Array.from(root.querySelectorAll('.p-week')).forEach((e, i) => { if (sideScroll[i]) { e.style.scrollBehavior = 'auto'; e.scrollLeft = sideScroll[i]; e.style.scrollBehavior = ''; } });
    root.querySelectorAll('[data-keep-scroll]').forEach(e => { const v = keep[e.getAttribute('data-keep-scroll')]; if (v) { e.scrollTop = v[0]; e.scrollLeft = v[1]; } });
    // filter rows that scroll sideways on phones: keep their position and show ‹ › arrows when there's more
    Array.from(root.querySelectorAll('.h-chips')).forEach((el, i) => { chipArrows(el); const x = chipScroll[i]; if (x) { const put = () => { el.style.scrollBehavior = 'auto'; el.scrollLeft = x; el.style.scrollBehavior = ''; el.dispatchEvent(new Event('scroll')); }; put(); requestAnimationFrame(put); } });
    const again = anchorId && document.getElementById(anchorId);
    if (again) window.scrollTo(wx, window.scrollY + again.getBoundingClientRect().top - anchorTop);
    else window.scrollTo(wx, wy);
    if (active >= 0 && now[active]) { now[active].focus({ preventScroll: true }); try { const l = now[active].value.length; now[active].setSelectionRange(l, l); } catch (e) {} }
  }
  ['pointerdown', 'click', 'touchstart'].forEach(ev => document.addEventListener(ev, (e) => { window.__lastTap = e.target; window.__lastTapAt = Date.now(); }, { capture: true, passive: true }));
  render();
  document.addEventListener('click', (e) => { const b = e.target.closest && (e.target.closest('.h-tapplay') || e.target.closest('.needs-tap')); if (!b) return; const w = b.closest('.h-vwrap'); const v = w && w.querySelector('video'); if (v) { v.muted = true; try { v.load(); } catch (x) {} v.play().catch(() => {}); } });
  let vt0 = Date.now();
  setInterval(() => { document.querySelectorAll('video[autoplay]').forEach(v => { const w = v.closest('.h-vwrap'); if (!w) return;
    const last = v._lastT || 0; const moving = !v.paused && v.currentTime > 0 && v.currentTime !== last; v._lastT = v.currentTime;
    if (moving) v._moving = true; else if (v.paused || Date.now() - vt0 > 2500) v._moving = moving;
    w.classList.toggle('needs-tap', !v._moving && Date.now() - vt0 > 2500); }); }, 800);
  const nudge = () => { document.querySelectorAll('video[autoplay]').forEach(v => { if (v.paused) { try { const pr = v.play(); if (pr && pr.catch) pr.catch(() => {}); } catch (e) {} } }); };
  ['touchstart', 'scroll', 'click'].forEach(ev => window.addEventListener(ev, nudge, { passive: true, once: true }));
  document.addEventListener('visibilitychange', () => { if (!document.hidden) nudge(); });
  // open each page at the top (or at its #section), including inside the artifact viewer
  // once someone has started scrolling or tapping, never move the page for them (a slow load used to jump laptops back to the top)
  let touched = false; ['wheel', 'touchmove', 'keydown', 'pointerdown'].forEach(ev => window.addEventListener(ev, () => { touched = true; }, { passive: true, once: true }));
  function land(force){
    if (touched && force !== true) return;
    const id = decodeURIComponent((location.hash || '').slice(1));
    const el = id && document.getElementById(id);
    if (el) { el.scrollIntoView({ block: 'start' }); }
    else { window.scrollTo(0, 0); try { root.firstElementChild && root.firstElementChild.scrollIntoView({ block: 'start' }); } catch (e) {} }
  }
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  requestAnimationFrame(() => requestAnimationFrame(land));
  window.addEventListener('load', () => setTimeout(land, 60));
  window.addEventListener('hashchange', () => land(true));
})();
'''.replace('__LOGIC__', logic.strip())

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{helmet.strip()}
</head>
<body>
<template id="dc-template">{body}</template>
<div id="dc-root"></div>
<script>{runtime}</script>
{open(os.path.join(HERE, 'dl_snippet.js')).read()} <!-- dl_snippet -->
</body>
</html>
'''
os.makedirs(os.path.join(out_dir, 'logos'), exist_ok=True)
open(os.path.join(out_dir, out_name), 'w', encoding='utf-8').write(page)
for name in used:
    for d in LOGO_DIRS:
        p = os.path.join(d, f'DATJ_{name}.svg')
        if os.path.exists(p):
            shutil.copy(p, os.path.join(out_dir, 'logos', f'{name}.svg'))
            break
    else:
        print('MISSING', name)
print('built', out_dir, out_name, sorted(used))
