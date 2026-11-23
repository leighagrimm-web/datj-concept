# Dance & All That Jazz site: handoff for Claude Code (Nov 22, 2026)

Prototype site for Dance & All That Jazz (owner Brittany Brady), built by Leigha with Claude.
Live prototype: https://leighagrimm-web.github.io/datj-concept/ (admin: `admin.html`).
Planning notes live in the claude.ai Project "Website Design Business" (`claude/dance-all-that-jazz-dsp-notes.md`, `claude/datj-old-site-audit.md` = hold list, `claude/datj-changes-nov22.md`, `claude/datj-year-over-year.md`, `claude/datj-competitions-and-emails.md`, plus Leigha's client standards `security.md` and `Business Brief`).

## Goal of the next phase
Get Britt on a **test site with a working admin** (real Publish, not browser-only) so her edits carry over to production.

## Repo layout
- Root `*.html`, `studio.ics`, `calendar.json`, `classes.json`, `*.enc.json`: the **built site** (what GitHub Pages serves). Don't hand-edit; rebuild from `src/`.
- `src/`: **build sources**
  - `project/HomeH.dc.html`: the homepage shell. It holds the page logic plus `CONTENT0` (default texts/lists), `CAL0` (studio calendar), `TEACHER_BY_CLASS`, the `ICS`, `SUB` (subscribe), `DEV`, `CUT` helpers.
  - `gen_pages.py`: regenerates `project/H-*.dc.html` (the other pages) from HomeH. Run after editing HomeH.
  - `build.py` + `build_site3.sh`: build everything into `src/site3/` (pages, admin with injected defaults, `calendar.json`, `studio.ics`). Then copy `src/site3/*` to the repo root.
  - `logos/`, `dl_snippet.js`, `scripts/*.py` (content/text update helpers).
- `admin-src/admin.html`: admin source (the root `admin.html` is built from it with defaults injected).
- `apps-script/`: `signups.gs` (trial/audition sign-ups), `calendar-feed.gs` (dancer calendar feed + studio feed), `test-feeds.js` (automated feed checks; needs the private Company data file passed in).
- `scripts/`: `studiopro.js` (Studio Pro schedule reader, browser + Node), `sync-classes.js`, `make-schedule-pdf.py`, `make-studio-ics.js`, `vendor/`.
- `company-tools/`: Company bundle encryption and the Company Calendar workbook maker/reader.
- `.github/workflows/sync-classes.yml`: nightly Studio Pro refresh (classes.json + schedule PDF). It commits to main, so always `git pull --rebase` before pushing.

## Build
```
cd src && python3 gen_pages.py && bash build_site3.sh && cp site3/*.html site3/studio.ics site3/calendar.json ..
```
(Verified Nov 22: building from `src/` gives byte-identical pages to what's published.)

## Rules (keep)
- **Never** put the real Company password, the Families password, the feed key, tokens or readable Company data (dancer schedules) in the repo. The repo is public. `*.xlsx` is git-ignored except the TEMPLATE files.
- Prototype passwords appear only as admin hints for testing; the real ones are new each season, chosen by Britt.
- Company Central and Annual Performance details are published encrypted (`company.enc.json`, `recital.enc.json`; PBKDF2 + AES-GCM, `company-tools/encrypt.mjs`).

## What's real vs prototype today
- Real: the site, the nightly Studio Pro sync, the schedule PDF, the studio calendar subscribe feed (`studio.ics`), add-to-calendar, device-aware Parent Portal links.
- Prototype only: **the admin saves to localStorage in that one browser** (Preview / Publish only affect that browser). Sign-up forms, the dancer calendar feed and email sending aren't connected yet.

## To build next (test site first)
1. **Test environment:** test Google Sheet + Apps Script project + test repo/branch and Pages URL. Britt's Google account owns the production ones (client owns every account).
2. **Admin Publish backend (Apps Script):** Google sign-in check (owner only), server-side validation, save to the Sheet (with version history), write `content.json` (same shape the admin's `pick()` produces) to the repo with a GitHub token kept in Script Properties; the site reads `content.json` instead of localStorage. Photos: shrink in browser, save into the repo. Re-encrypt `company.enc.json` / `recital.enc.json` on publish with the current passwords.
3. **Deploy `signups.gs`** and set `SIGNUP_URL` in the site.
4. **Deploy `calendar-feed.gs`** (see the setup steps at the top of the file), set `SUB.FEED_URL` in HomeH, then test on real devices (hold list item 5).
5. **"Refresh from Studio Pro now"** for everyone: Apps Script triggers the GitHub workflow (token in Script Properties).
6. **Year-over-year:** Start new season button + review screen, monthly email to Britt, health checks (`claude/datj-year-over-year.md`).
7. Later: admin help guide, chat help, Cloudflare Pages + domain move off Wix.

## Open items needing Britt/Leigha
Audition Google Form link · Families password · technique-only class list · 2027 summer details · paid events as Studio Pro classes with a Lead Trial Fee (works; Bollywood class in its own season doesn't show on the landing page yet) · teacher assignments now set in admin → Classes → Teachers.
