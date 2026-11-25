# Test environment and admin Publish

Brittany edits on the **test site** first. When she presses Publish there, it goes through a Google Apps Script
backend that checks it's her, saves the version in a Google Sheet, and writes `content.json` to the test repo.
The site reads `content.json`. Nothing reaches production until she approves the test site.

| | Test | Production (later) |
|---|---|---|
| Site | https://leighagrimm-web.github.io/datj-test/ | the studio's domain |
| Admin | …/datj-test/admin.html | …/admin.html |
| Repo Publish writes to | `leighagrimm-web/datj-test` (main) | the production repo |
| Google account (Sheet + script) | Leigha's test account | Brittany's account |
| clasp sign-in name | `datj-test` | `datj-live` |
| Script and deployment IDs | `apps-script/admin/deployments.json` | same file |

## How it fits together

1. **Sign in.** The admin page (on GitHub Pages) shows "Sign in with Google", which opens the script's **signin**
   deployment (Execute as me, Only myself). Google only lets the owner in. The script checks her email against
   `OWNER_EMAIL`, then sends her back to `ADMIN_PAGE_URL` with a signed pass in the address (`#signin=…`) that's
   good for 12 hours. The pass never goes anywhere except that fixed admin address.
2. **Load.** The admin posts `{action: "load", pass}` to the **public** deployment (Execute as me, Anyone). Every
   action checks the pass first. It returns the latest published version from the History tab.
3. **Publish.** The admin posts the whole draft. The server:
   - checks it (expected sections and types, dates, menu pages, staff names, text length, no `javascript:` or
     non-image `data:` links, size limits). It never trusts the page.
   - refuses if another device published since this draft started, and offers "Publish mine anyway".
   - saves a new row on **History**: version, time, who, size, what changed, website result, then the full
     draft in 45,000-character pieces across the columns. The full draft includes Company Central edits, which stay
     in this private Sheet.
   - writes the **public part** to `content.json` in the repo (GitHub API, token in Script Properties). Company
     Central edits (`coEdit`) and the calendar sheet link are left out, because the repo is public.
4. **Site.** Every page fetches `content.json` (cached in the browser for the next visit). `?preview=draft` pages
   lay the admin's unpublished draft on top. The datj-concept prototype has no `content.json`, so it keeps the old
   browser-only behavior.

### Locked details (Company Central and Annual Performance)

Some details are only for families with a password, so they never go into `content.json`:

| What | Locked with | File |
|---|---|---|
| Company Central edits (`coEdit`) and the details of "Company families only" dates (`lock`) | Company password | `company.enc.json` |
| Annual Performance "More details" (`rc[].more`) | Families password | `recital.enc.json` |

When one of these changes, Publish (in the browser) opens the current file with the current password, lays the edits
on top, locks it again (PBKDF2-SHA256 250,000 + AES-GCM, the same format as `company-tools/encrypt.mjs`), opens it
once more to check, and sends only the locked file. The passwords families use now are kept in Script Properties
(`LOCK_PW_COMPANY`, `LOCK_PW_FAMILIES`) and given only to the signed-in owner's admin, so Brittany never types them
when publishing. If one is missing, the admin asks once, checks it opens the current file, and saves it there.
They're never in the repo or `content.json`. The server
strips those details from `content.json` itself, refuses a publish that changes them without the locked file, and
writes `content.json` and the locked files in **one commit**.

**New season passwords.** Company Central and Annual Performance each show the current password with a **Change for
a new season** button. The new password (6–60 characters, different from the other one) waits on that device, marked
"Not live yet", until Publish. Publish then re-locks the file with it, and the server saves it to Script Properties
only after that commit lands, so the saved password always matches the live file. If another device changed it in
the meantime, the admin fetches the current one from the server (`action: "locks"`) before re-locking.

## One-time setup (test)

Do this in a separate browser window (its own Chrome profile or a private window) signed in **only** to the test
Google account. Apps Script gets confused when two accounts are signed in at once.

1. **Apps Script API:** open https://script.google.com/home/usersettings and turn **Google Apps Script API** on.
2. **clasp sign-in:** in a terminal, `clasp login --user datj-test`, and sign in with the test account.
3. **Create the Sheet and script** (Claude runs this): `clasp create --type sheets --title "DATJ Admin – TEST" --user datj-test`.
   The new script ID goes in `deployments.json` → `test.scriptId`.
4. **Deploy** (Claude runs this, after asking): `node tools/deploy-admin.js test "first deploy"`. The first run creates
   both deployments and saves their IDs. Their URLs go into `BACKENDS['/datj-test/']` in `admin-src/admin.html`.
5. **GitHub token:** github.com → Settings → Developer settings → Fine-grained tokens → Generate.
   Resource owner `leighagrimm-web`, **Only select repositories: datj-test**, Permissions → Contents: **Read and write**,
   expiry 90 days. Copy it; don't paste it in chat.
6. **Script Properties:** in the script editor → Project Settings → Script Properties, add:
   `GITHUB_TOKEN` (the token), `GITHUB_REPO` = `leighagrimm-web/datj-test`, `GITHUB_BRANCH` = `main`,
   `ADMIN_PAGE_URL` = `https://leighagrimm-web.github.io/datj-test/admin.html`, `ENVIRONMENT` = `TEST`,
   and the passwords families use now: `LOCK_PW_COMPANY` and `LOCK_PW_FAMILIES`. With these set, Brittany is never
   asked for a password. Without them, the admin asks once when something locked changes (it needs the current
   password to carry over details that are only inside the locked file).
7. **Run `setup`** in the editor (pick it in the function list, click Run, allow the permissions). It records you as
   the owner, makes the sign-in key and the History tab. Then run **`checkGitHub`**: it should log "(can write)".
8. Share the Sheet with nobody else. Never "anyone with the link".

## After setup: test plan

- [ ] Signed out: admin shows only "Sign in with Google". A different Google account opening the sign-in link gets
      Google's no-access page.
- [ ] Sign in → back on the admin, TEST banner showing, "Loading…" then the editor.
- [ ] Change the top banner → Publish shows "Publishing…" with a spinner and can't be clicked twice → "Published
      version 1 (Top banner)". History tab has the row; datj-test has a commit to `content.json`.
- [ ] Within about a minute, the test site shows the new banner in a fresh private window.
- [ ] `content.json` in the repo has no `coEdit` and no Company Central data.
- [ ] Edit on a second device, publish there, then publish from the first → "published from another device"
      notice with both choices working.
- [ ] Locked details: add "More details" to a performance card and details to a "Company families only" date →
      Publish asks for the Families / Company password (or uses the saved one) → one commit with `content.json` +
      the locked files; `content.json` has none of that text; the families page shows it only after the password.
- [ ] Change the Families password → "Not live yet" → Publish → the families page needs the new one, the old one
      fails, and the Families password box shows the new one on another device. Same for the Company password.
- [ ] Bad data is refused by the server (e.g. a calendar date that ends before it starts).
- [ ] Turn the token off in Script Properties → Publish says the website couldn't be updated, and the version is still
      saved. Put it back, publish again.
- [ ] After 12 hours (or Sign out) → asked to sign in again, draft still there.
- [ ] Phone: no sideways scroll at 390px, buttons at least 44px tall.

## Deploying changes

- Backend: `node tools/deploy-admin.js test "what changed"`. Always asked first; LIVE only when Leigha says go.
- Site: build from `src/` (see HANDOFF.md), commit on the `test` branch of datj-concept, then
  `git pull --rebase testsite main` and `git push testsite test:main`. Publish commits `content.json` to datj-test, and
  the nightly schedule bot commits there too, so always pull with rebase first.
