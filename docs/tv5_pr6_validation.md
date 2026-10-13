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

## Workflow verification and browser limitation

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

PR #6 must remain open for review; browser QA is still outstanding before merge.
