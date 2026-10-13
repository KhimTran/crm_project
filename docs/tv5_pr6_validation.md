# PR #6 corrections and develop integration — 2026-10-13

Owner authorized correcting feature/tv5-surveys-v2, integrating latest develop,
committing/pushing the existing PR #6, but no PR merge or demo-data changes.
Worktree 44c0 was clean before switching from feature/tv4-models.

Fetched develop c6a053ed5deb3cf850f58b23912325b11b28138f (merged PR #5 and
PR #7) into TV5 head 29b56706a878be2a81964c6727122795df4743b6.
The two conflicts were base_customer.html and base_crm.html. Retained the current
retail layout, real search/category/account menus, TV4 feedback menu/badge/report
routes, customer CSS links, CRM password-change/logout actions. Added customer
and CRM survey menus. Restored Categories/Brands in Admin while keeping Surveys.

## Backend corrections

- JSON answers must be a list of objects with positive signed-INT question IDs.
- Supplied TEXT answers must be strings, nonempty after strip; trimmed copies are
  stored without mutating the caller's payload. Optional questions may be omitted.
- RATING accepts only integer values 1–5; rejects booleans, floats, numeric strings,
  out-of-range and missing values.
- SINGLE_CHOICE/MULTI_CHOICE accept only integer option IDs belonging to their
  question. Duplicate choice selection and duplicate non-MULTI answers are rejected.
- Each answer has exactly question_id and its type's one answer field. Wrong,
  mixed, unknown or null extra fields are rejected with ValidationError/HTTP 400.
- All validation occurs before answer writes inside the existing transaction.
  Required-question, ownership, closed-survey and single-submission protections stay.
- Statistics bar widths use unlocalize to render decimal dots, retaining normal
  localized numbers for human-readable text. Customer survey buttons use TV1 colors.
- No model, migration, SQL schema, demo seed/reset or permission change.

## Tests and database checks actually run

Python D:/Python312/python.exe; Django 5.2.17; MySQL test_crm_db.

```powershell
python manage.py check --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py test apps.surveys apps.accounts.tests.test_layouts apps.feedback apps.shop --settings=config.test_settings --keepdb --noinput
python manage.py test --settings=config.test_settings --keepdb --noinput
```

- Check: 0 issues; migration dry-run: No changes detected.
- Focused suite: 72/72 passed in 42.924 seconds.
- Initial full run: 284 tests in 303.223 seconds, two errors/one failure in TV5's
  open-survey fixture. MySQL columns have DATETIME_PRECISION=0; a read-only CAST
  confirmed 00:00:00.800000 rounds to 00:00:01. Fixture start_at=now could therefore
  briefly be in the future. Fixed the fixture to start one minute earlier; kept
  tests/assertions and production opening/closing validation unchanged.
- Final full run: **284/284 passed in 320.845 seconds** on test_crm_db.
- All existing TV1/TV4/TV5 test methods remain. Twelve new regression methods cover
  type/mixed-field validation, atomic rollback, HTTP errors, optional/required answers,
  duplicate/closed submissions, navigation and localized statistical CSS.
- showmigrations/migrate --plan used temporary settings fixing default.NAME to
  test_crm_db: all migrations applied, no planned operations. No migrate was run.
- git diff and cached diff --check passed; no unresolved conflict entries.
- Seed messages during regression tests refer only to the runner's test database.

## Initial workflow verification and browser limitation

Browser automation could not initialize: `failed to write kernel assets` with
Windows path error 3, repeatedly after reset. The shared Node runtime failed too.
Direct browser testing and new screenshots were **not performed**; visual/mobile
layout, JavaScript answer serialization and confirmation dialogs remain unverified
in this run. Do not treat the following HTTP checks as browser evidence.

After the runner finished, a Client(enforce_csrf_checks=True) workflow on
test_crm_db passed **40 checks**, with actual login, form GET/POST and CSRF tokens:

- Manager created a survey and all four question types using management forms.
- Audience preview and sending combined age, level and preference filters:
  exactly four selected customers received it, a fifth was excluded.
- Three customers submitted TEXT/RATING/SINGLE_CHOICE/MULTI_CHOICE answers.
  Repeated POSTs retained exactly five answer rows per completed response.
- Statistics: sent=4, completed=3, pending=1, response rate=75%, rating average=4;
  single-choice proportion=66.7%; multi-choice counts three distinct respondents.
  Rendered Vietnamese statistics CSS contains width:66.7%, never width:66,7%.
- Manager closed the survey; a fourth customer's already-open valid form then
  received HTTP 400 on POST, with no added answers. Its survey list shows closed.
- Customer feedback/survey menus and retail CSS, CRM feedback/survey/logout routes,
  Admin Categories/Brands pages and both sidebar links rendered successfully.

Persisted CLOSED status, three submitted responses, four recipients and fifteen
answer rows were verified before deleting only this run's synthetic fixture IDs
and authenticated sessions. Temporary scripts/settings/credential JSON removed.
Non-sensitive HTTP audit results remain outside Git. No demo data was modified.

This limitation applied to the initial integration run. The dedicated browser QA
below supersedes it. PR #6 remains open for the owner's final review.

## Dedicated browser QA — 2026-10-13

Verified clean branch feature/tv5-surveys-v2 at 23f2b2a and fetched origin;
develop c6a053e was already an ancestor. Initial fresh full run passed 284/284
in 332.231 seconds. Browser QA began only after that runner finished.

The in-app browser again failed before initialization with `failed to write
kernel assets: The system cannot find the path specified. (os error 3)`.
Resetting and testing the alternate Node tool produced the same error. Bundled
Playwright could run through the shell; its default Chromium binary was absent,
so QA used the installed Microsoft Edge **155.0.4283.45** (Chromium engine),
headless, with actual rendered pages, JavaScript, clicks, form submissions and
native JavaScript dialogs. These results are browser evidence, not Django Client
or HTTP-only substitutes. No extra runtime/package was installed.

Server: 127.0.0.1:8002, temporary external settings with database NAME explicitly
fixed to **test_crm_db**, unique QA session/CSRF cookie names. Synthetic accounts
used example.test addresses and generated passwords kept outside Git. No commands
or browser requests targeted crm_tv1_demo. No migrate, shared seed or reset ran.

Browser checks performed:

- CRM created draft surveys and all four types plus an optional TEXT question.
  Edited TEXT, deleted a disposable question, moved its order, inspected detail.
- Actual audience radio/checkbox forms selected age 25–34, BEGINNER and a unique
  QA category preference. Preview showed four recipients. Send confirmation
  created exactly those four; three accounts outside age/level/preference saw no
  survey. The matching LOCKED account was excluded. ORM independently verified IDs.
- Three customer sessions opened their own list/form and submitted with JS
  serialization and confirm dialogs. Required empty/whitespace TEXT produced the
  real alert; optional TEXT was omitted. Canceling confirmation sent no POST.
  Saved answers matched selected options, ratings 3/4/5 and stripped text exactly:
  5 + 5 + 4 answer rows, three submitted responses. Reopening redirected to result.
- A fourth customer held a filled form while CRM closed the survey. Its actual
  form POST returned 400, with no answers/submission persisted. Closed GET returned
  400; list moved the survey to closed. A sent survey opening tomorrow offered no
  take button; direct take returned 400, and no response was created.
- Another customer's take/result returned 403. Plain customer could not enter
  survey creation. A session locked after login lost access (take 403, profile
  redirected to login); a pre-locked account's real login form rejected login.
  Backend regression tests additionally cover POST ownership, duplicate POST and
  the unopened survey's POST path, which has no usable browser form.
- Statistics showed sent=4, done=3, pending=1, rate=75%, rating average=4;
  single-choice counts 2/1, multi-choice 3/2/0, correct text and optional zero.
  Actual rendered 66.7% bars measured approximately 66.7% of their tracks.
- Clicked Print, rendered print media and a two-page A4 PDF, and visually inspected
  both rasterized PDF pages. This validates browser print layout; the operating
  system printer chooser and physical printing were not exercised.
- Desktop 1440 and mobile 390 at scale 1: survey detail, audience, take, customer
  lists, stats, menus/forms/buttons and bars inspected/screenshotted. Shop home,
  list, detail, profile, account/category menus and TV4 reply views had no document
  overflow. Admin mobile menu worked; wide Admin tables retain their existing
  internal scrolling.
- Shop real search returned 14 QA products; next-page link preserved q. Category,
  brand and price form returned three; empty and invalid filter states rendered.
  Customer saved profile through its form. TV4 customer feedback -> CRM RESOLVED
  reply -> customer reading reply passed with persisted status/note checked.
  CRM overview/customers/feedback/surveys loaded; Admin Categories/Brands links
  navigated to both pages on desktop and Categories via the mobile menu.

### Bugs found and corrected

1. Print CSS hid the sidebar without removing its 240px grid column. The report
   became a narrow column, losing its header title. Survey-only print CSS now
   switches the shell to block, removes main padding, keeps a four-column KPI row,
   preserves bar colors and prints an escaped survey title. Browser measured
   workspace=1440px, shell=1440px; the A4 report has no clipped cards/bars.
2. CRM survey list overflowed the 390px document by 3px. A labeled, focusable
   table region now scrolls internally while its readable table keeps 620px
   minimum width. ArrowRight was exercised with actual keyboard focus; document
   scrollWidth stayed 390px. No global CRM/Admin CSS change.

Added three Django regressions for held-form close, future GET/POST rejection
without writes and printable title escaping. Added optional
`scripts/qa_survey_layout.cjs`, which checks actual list keyboard scrolling,
390/1440 document width, statistical bars and full-width print layout using an
existing Playwright installation. It runs only against a local QA URL on 8002
with an external synthetic manager storage-state file; no credentials are tracked.

Example browser regression command (private state/output stay outside repository):

```powershell
$env:PLAYWRIGHT_MODULE = '<existing Playwright package directory>'
node scripts/qa_survey_layout.cjs --base-url http://127.0.0.1:8002 --survey-id <qa-survey-id> --storage-state <external-private-state.json> --output <external-evidence-directory>
```

Only this run's synthetic IDs and nine authenticated sessions were removed after
checking persistence. QA server stopped and private credentials/storage-state
JSON and server logs deleted before the final test runner started. Browser
contexts closed. Non-sensitive screenshots, PDF previews and JSON audits remain
outside Git; no account credentials, tokens, demo data or local settings commit.

Final checks: `check` found 0 issues; `makemigrations --check --dry-run` reported
No changes detected; the complete suite passed **287/287 in 337.570 seconds** on
test_crm_db. No browser writes occurred during either test run. Node syntax check
and the actual browser regression script passed. No model/config/migration changes
relative to develop; all prior test methods remain.

After the runner finished, a fresh synthetic draft was used to confirm edit and
delete operations separately for **each** of SINGLE_CHOICE, MULTI_CHOICE, RATING
and TEXT. Both choice types rejected a single option through the real form,
accepted corrected options and replaced them on edit. Required flags changed to
optional; up/down controls produced the correct question order. Four individual
delete confirmations removed all questions; Send was disabled with the no-question
error. Empty list and question form were inspected; 1366/390 layouts had no document
overflow. No further code changes were needed. This second fixture and its one
manager session were removed, server stopped and private state/logs deleted.

Outcome: no remaining functional blocker found in the tested scope. Browser QA
used Edge's Chromium engine and desktop/mobile viewport emulation; native OS
printer selection/physical printing and other browser engines remain outside
this check. PR #6 is ready for the owner's final review; no merge or auto-merge.
