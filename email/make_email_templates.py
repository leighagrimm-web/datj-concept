"""D&ATJ email template: one header + footer, reusable blocks. Writes the Mailchimp (Company) and Studio Pro versions + a preview page."""
import html, json
BASE = 'https://leighagrimm-web.github.io/datj-concept/'   # move to her domain at launch
LOGO = BASE + 'email/logo_stacked_520.png'; CIRCLE = BASE + 'email/logo_circle_160.png'
TEAL, DARK, INK, MUT, LINE, SOFT = '#00ADB5', '#007A80', '#111111', '#555555', '#E5E5E5', '#F2F2F2'
FONT = "Arial, Helvetica, sans-serif"
e = html.escape
def preheader(t): return f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;mso-hide:all;">{e(t)}&#8199;&#65279;&#847;&#8199;&#65279;&#847;&#8199;&#65279;&#847;</div>'
def header(label):
    return f'''<tr><td style="background:#000000;padding:22px 28px;" bgcolor="#000000">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td align="left" valign="middle"><a href="{BASE}" target="_blank" style="text-decoration:none;"><img src="{LOGO}" width="170" alt="Dance &amp; All That Jazz" style="display:block;border:0;width:170px;max-width:170px;height:auto;"></a></td>
    <td align="right" valign="middle" style="font-family:{FONT};font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{TEAL};font-weight:bold;">{e(label)}</td>
  </tr></table></td></tr>
<tr><td style="background:{TEAL};height:5px;line-height:5px;font-size:5px;" bgcolor="{TEAL}">&nbsp;</td></tr>'''
def title(h, intro):
    return f'''<tr><td style="padding:30px 28px 6px;font-family:{FONT};color:{INK};">
  <h1 style="margin:0 0 12px;font-size:28px;line-height:32px;letter-spacing:-0.5px;font-weight:800;color:{INK};">{e(h)}</h1>
  <p style="margin:0;font-size:16px;line-height:24px;color:#333333;">{intro}</p></td></tr>'''
def dates(items, heading='Key dates'):
    rows = ''.join(f'''<tr><td width="74" valign="top" style="padding:10px 0;border-top:1px solid {LINE};"><div style="font-family:{FONT};background:{INK};color:#FFFFFF;text-align:center;width:62px;padding:6px 0;"><div style="font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:{TEAL};font-weight:bold;">{e(m)}</div><div style="font-size:20px;line-height:22px;font-weight:800;">{e(d)}</div></div></td>
      <td valign="top" style="padding:12px 0 10px;border-top:1px solid {LINE};font-family:{FONT};font-size:15px;line-height:21px;color:{INK};"><b>{e(t)}</b>{('<br><span style="color:'+MUT+';font-size:13px;">'+e(s)+'</span>') if s else ''}</td></tr>''' for m, d, t, s in items)
    return f'''<tr><td style="padding:22px 28px 4px;">{section_label(heading)}<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table></td></tr>'''
def section_label(t): return f'<div style="font-family:{FONT};font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;color:{DARK};padding-bottom:6px;border-bottom:2px solid {TEAL};margin-bottom:6px;">{e(t)}</div>'
def bullets(heading, items):
    li = ''.join(f'<tr><td width="18" valign="top" style="padding:7px 0;font-family:{FONT};color:{TEAL};font-size:14px;line-height:21px;">&#9632;</td><td valign="top" style="padding:7px 0;font-family:{FONT};font-size:15px;line-height:21px;color:{INK};">{i}</td></tr>' for i in items)
    return f'<tr><td style="padding:22px 28px 4px;">{section_label(heading)}<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{li}</table></td></tr>'
def callout(heading, text):
    return f'''<tr><td style="padding:22px 28px 4px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="background:{TEAL};padding:18px 20px;font-family:{FONT};color:#000000;" bgcolor="{TEAL}">
  <div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;font-weight:bold;margin-bottom:6px;">{e(heading)}</div><div style="font-size:15px;line-height:22px;">{text}</div></td></tr></table></td></tr>'''
def button(label, url, primary=True):
    bg, fg, bd = (TEAL, '#000000', TEAL) if primary else ('#FFFFFF', INK, INK)
    return f'''<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 10px;"><tr><td align="center" style="background:{bg};border:2px solid {bd};" bgcolor="{bg}">
  <a href="{url}" target="_blank" style="display:block;padding:15px 18px;font-family:{FONT};font-size:13px;letter-spacing:1.5px;text-transform:uppercase;font-weight:bold;color:{fg};text-decoration:none;">{e(label)} &rarr;</a></td></tr></table>'''
def buttons(items): return '<tr><td style="padding:24px 28px 6px;">' + ''.join(button(l, u, i == 0) for i, (l, u) in enumerate(items)) + '</td></tr>'
def signoff(t='Thank you!<br>Brittany &amp; the D&amp;ATJ team'): return f'<tr><td style="padding:16px 28px 26px;font-family:{FONT};font-size:15px;line-height:22px;color:{INK};">{t}</td></tr>'
def footer(kind):
    links = [('Studio calendar', BASE + 'families.html#calendar'), ('Parent Portal', 'https://dancestudio-pro.com/online/index.php?account_id=20951'), ('Class schedule', BASE + 'classes.html')]
    if kind == 'company': links.insert(1, ('Company Central', BASE + 'company-families.html'))
    ql = ' &nbsp;&middot;&nbsp; '.join(f'<a href="{u}" target="_blank" style="color:#FFFFFF;text-decoration:none;font-weight:bold;">{e(l)}</a>' for l, u in links)
    legal = ('<p style="margin:14px 0 0;font-size:11px;line-height:17px;color:#8A8A8A;">You’re getting this because you’re part of the D&amp;ATJ Company family. *|LIST:ADDRESSLINE|*<br>'
             '<a href="*|UPDATE_PROFILE|*" style="color:#8A8A8A;text-decoration:underline;">Update preferences</a> &nbsp;&middot;&nbsp; <a href="*|UNSUB|*" style="color:#8A8A8A;text-decoration:underline;">Unsubscribe</a></p>') if kind == 'company' else \
            '<p style="margin:14px 0 0;font-size:11px;line-height:17px;color:#8A8A8A;">You’re getting this because your family is enrolled at Dance &amp; All That Jazz.</p>'
    return f'''<tr><td style="background:{INK};padding:28px;font-family:{FONT};color:#AEB8B3;" bgcolor="{INK}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
    <td width="70" valign="top"><img src="{CIRCLE}" width="56" height="56" alt="" style="display:block;border:0;"></td>
    <td valign="top" style="font-family:{FONT};"><div style="font-size:18px;font-weight:800;color:#FFFFFF;letter-spacing:-0.3px;">create. inspire. <i style="color:{TEAL};font-family:Georgia,serif;font-weight:normal;">dance.</i></div>
      <div style="font-size:13px;line-height:20px;margin-top:6px;">844 N Elmhurst Rd, Prospect Heights, IL 60070<br><a href="tel:8479478464" style="color:#AEB8B3;text-decoration:none;">(847) 947-8464</a> &nbsp;&middot;&nbsp; <a href="mailto:team@danceandallthatjazz.com" style="color:#AEB8B3;text-decoration:none;">team@danceandallthatjazz.com</a></div></td></tr></table>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:20px 0 0;"><tr><td style="background:{TEAL};padding:14px 16px;font-family:{FONT};font-size:14px;line-height:20px;color:#000000;" bgcolor="{TEAL}"><b>Missing class?</b> Report an absence in the Parent Portal. No need to email. &nbsp;<a href="https://dancestudio-pro.com/online/index.php?account_id=20951" target="_blank" style="color:#000000;font-weight:bold;text-decoration:underline;white-space:nowrap;">Report an absence &rarr;</a></td></tr></table>
  <div style="border-top:1px solid #333333;margin:18px 0 14px;"></div>
  <div style="font-size:12px;line-height:20px;">{ql}</div>
  <div style="font-size:12px;line-height:20px;margin-top:6px;"><a href="https://instagram.com/danceandallthatjazz" style="color:{TEAL};text-decoration:none;font-weight:bold;">Instagram</a> &nbsp;&middot;&nbsp; <a href="https://www.facebook.com/DanceandAllThatJazz" style="color:{TEAL};text-decoration:none;font-weight:bold;">Facebook</a></div>
  {legal}</td></tr>'''
def page(kind, subject, pre, body):
    label = 'Company' if kind == 'company' else 'Studio news'
    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><meta name="color-scheme" content="light only"><title>{e(subject)}</title>
<style>@media (max-width:620px){{.wrap{{width:100% !important}}h1{{font-size:24px !important;line-height:28px !important}}}}</style></head>
<body style="margin:0;padding:0;background:{SOFT};" bgcolor="{SOFT}">{preheader(pre)}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{SOFT}" style="background:{SOFT};"><tr><td align="center" style="padding:24px 10px;">
<table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#FFFFFF;" bgcolor="#FFFFFF">
{header(label)}
{body}
{footer(kind)}
</table></td></tr></table></body></html>'''
company = page('company', 'Company: Walk-A-Thon Sunday + what’s due in September', 'Walk-A-Thon Sun 9/13, fees due 9/15, dance films 9/27 & 10/4',
  title('Walk-A-Thon Sunday + what’s due in September', 'Hi Company families! The short version is below. Everything else is on Company Central.')
  + dates([('Sep', '13', 'Walk-A-Thon · 8–10 AM', 'Heritage Park Performance Pavilion, Wheeling · team tie-dye tee'), ('Sep', '15', 'Additional routine & costume fees due', ''), ('Sep', '27', 'Dance films: Hip Hop, Senior, Junior', 'Williams-Sonoma, Lake Forest'), ('Oct', '4', 'Dance films: Petite, Teen, Intermediate', 'Williams-Sonoma, Lake Forest')], 'This month')
  + callout('To do', 'Walk-A-Thon donations are due <b>Sep 9</b>, and we still need <b>4 parent volunteers</b>. Need a new jacket, backpack or earrings? $105 / $90 / $24, or $219 for all three.')
  + bullets('Coming up', ['<b>Oct 17</b> · Feed My Starving Children', '<b>Nov 14</b> · Windy City Bulls'])
  + buttons([('Open Company Central', BASE + 'company-families.html'), ('Dance film looks (printable)', BASE + 'company-families.html#handbook'), ('Volunteer sign-up', '#')])
  + signoff())
studio = page('studio', 'November at D&ATJ', 'Observation week, food drive, fall break and Annual Performance info',
  title('November at D&ATJ', 'Hello D&amp;ATJ families! A quick look at the month. Tap any date on the website calendar for details.')
  + dates([('Nov', '15', 'Class Observation & Dance Family Appreciation Week', 'Through Nov 21 · coffee, tea & treats in the lobby'), ('Nov', '18', 'New Family Info Call: Annual Performance', '7:00 PM on Google Meet'), ('Nov', '19', 'Last day of the Studio Food Drive', 'Box in Studio A'), ('Nov', '22', 'Popcorn Fundraiser ends', ''), ('Nov', '24', 'Fall Break: studio closed', 'Classes resume Monday, Nov 30')], 'This month')
  + callout('14th Annual Performance', '<b>May 22–23</b> at Wheeling High School. Commitment forms are coming in the next couple of weeks.')
  + buttons([('See the studio calendar', BASE + 'families.html#calendar'), ('Annual Performance info', BASE + 'families.html#recital')])
  + signoff('Thank you!<br>Dance &amp; All That Jazz'))
blank = page('company', '*|MC:SUBJECT|*', 'One line that shows next to the subject in the inbox',
  title('Headline', 'One or two sentences. Point people to the website for details.')
  + dates([('Mon', '00', 'What’s happening', 'Where · what to bring')], 'Key dates') + bullets('Section', ['One short point', 'Another short point'])
  + callout('Important', 'The one thing people can’t miss.') + buttons([('Main button', BASE), ('Second button', BASE)]) + signoff())
open('email-company-mailchimp.html', 'w').write(company); open('email-studio-studiopro.html', 'w').write(studio); open('email-blank-template.html', 'w').write(blank)
# preview page
P = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex, nofollow"><title>D&amp;ATJ email templates</title>
<style>body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#111111;color:#FFFFFF}header{padding:28px 5vw 10px}h1{margin:0;font-size:34px;letter-spacing:-1px}p{color:#AEB8B3;max-width:760px;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:22px;padding:10px 5vw 50px}.card{background:#1C1C1C;padding:16px}.card h2{margin:0 0 4px;font-size:18px}.card small{color:#AEB8B3}
iframe{width:100%;height:1250px;border:0;background:#F2F2F2;margin-top:12px}button{margin-top:10px;padding:12px 14px;background:#00ADB5;border:0;font-weight:bold;letter-spacing:1px;text-transform:uppercase;font-size:11px;cursor:pointer}a{color:#00ADB5}</style></head><body>
<header><h1>Email templates</h1><p>One header and footer for every email, plus building blocks: headline, key dates, short sections, a teal callout and big buttons. <b>Company</b> emails go through Mailchimp (with its unsubscribe and address tags). <b>Studio</b> emails get pasted into Studio Pro. The admin’s Emails screen fills these in for her.</p></header>
<div class="grid">''' + ''.join(f'''<div class="card"><h2>{t}</h2><small>{s}</small><br><button type="button" onclick="copyHtml('{f}', this)">Copy HTML</button> &nbsp;<a href="email/{f}" target="_blank">Open on its own</a><iframe src="email/{f}" title="{t}"></iframe></div>'''
  for t, s, f in [('Company · Mailchimp', 'Her Sep 8 Company Updates, rewritten', 'email-company-mailchimp.html'), ('Studio · Studio Pro', 'Her November Updates, rewritten', 'email-studio-studiopro.html'), ('Blank template', 'To start a new one', 'email-blank-template.html')]) + '''</div>
<script>function copyHtml(f,b){fetch('email/'+f).then(r=>r.text()).then(t=>navigator.clipboard.writeText(t)).then(()=>{b.textContent='Copied ✓';setTimeout(()=>b.textContent='Copy HTML',1600)}).catch(()=>{b.textContent='Open it and copy instead'})}</script></body></html>'''
open('email-templates.html', 'w').write(P)
print('ok', len(company), len(studio))
