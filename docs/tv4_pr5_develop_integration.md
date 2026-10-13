# PR #5 develop integration — 2026-10-13

The owner authorized updating the existing feature/tv4-models branch and PR #5,
including commit/push, but no PR merge. Worktree 44c0 was clean before switching
from feature/tv1-shop-redesign. No existing work was discarded.

Fetched origin/develop at 59c10d1525f3915e8b21fb45f5d7d9099d1e420c
(merged PR #7), into feature/tv4-models at
8c0b44f1058b40dbfa586c5c2d861b43e6a6361d.

## Conflict resolution

Exactly three files conflicted:

- templates/layouts/base_customer.html: keep the compact retail header, real
  search, database categories and account menu from TV1. Add TV4's authenticated
  CUSTOMER link to feedbacks:mine in the navigation, with an active-page state.
- templates/shop/product_detail.html: keep breadcrumb, neutral missing-image
  display, Decimal price, product facts and description from TV1. Add the working
  feedbacks:create link with the product query parameter, using the shop button.
- apps/shop/tests.py: retain TV1 category/brand/visibility/local-asset assertions
  and TV4's real feedback-link assertions. Remove only the obsolete survey
  "Sắp có" text assertion; no test method was removed.

The mobile navigation can wrap, and customer_feedbacks.css uses the storefront
palette under .customer-layout. CRM/Admin styling and feedback business logic,
URL contracts, fields, permissions, models and migrations were not changed by
this conflict resolution. Existing TV4 changes remain on its branch.

All 5 shop, 8 shop UI and 7 layout test methods from develop, and all 7 customer
feedback and 13 handling test methods from the original TV4 HEAD, remain present.
Two regression tests were added for the integrated menu and the complete HTTP
customer submission -> CRM reply -> owner reply visibility/other-customer denial.

## Actual validation

Python: D:/Python312/python.exe, Django 5.2.17, MySQL test_crm_db.

```powershell
python manage.py check --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
python manage.py test apps.shop apps.feedback apps.accounts.tests.test_layouts --settings=config.test_settings --keepdb --noinput
python manage.py test --settings=config.test_settings --keepdb --noinput
```

- Check: 0 issues. Migration dry-run: No changes detected.
- Focused tests: 42/42 passed in 27.035 seconds.
- Full regression: 258/258 passed in 290.497 seconds. Includes TV1, TV4, account,
  customer, catalog, Admin, permissions and existing survey tests.
- Test settings explicitly assert TEST.NAME=test_crm_db. Seed-command messages
  in the suite concern this test database only, never the demo database.
- showmigrations and migrate --plan used a temporary settings module fixing
  DATABASES.default.NAME=test_crm_db: all migrations applied, no planned operations.
  No migrate/seed/reset/restore was run against crm_tv1_demo.
- git diff --check and cached diff --check passed; no unresolved conflict entries.

After the runner completed, browser QA used an isolated server on port 8002,
test_crm_db and separate session/CSRF cookies. Two synthetic accounts, one customer
and catalog fixture were created only for this run. The browser verified:

- Product detail -> feedback form with the correct product preselected.
- Authenticated customer menu, missing-field errors, valid 4-star submission,
  success message and NEW status on the customer's feedback list.
- CRM manager login -> feedback menu/badge -> detail; RESOLVED without a reply
  shows validation error, then saving a reply sets RESOLVED and the handler/time.
- Customer login -> "Phản hồi của tôi" -> correct reply and "Đã xử lý" status.
- Customer form/list/menu at 390px, reply page at 1440px, menu Escape and category
  disclosure. At 390px the reply page has scrollWidth=390 and viewport scale=1.
  Customer reply pages and CRM detail were visually inspected and captured.

Cleanup verified the persisted reply, RESOLVED status, handled_by and resolved_at
before removing only this run's fixtures and authenticated sessions. The QA server
was stopped and temporary settings/scripts/credential JSON removed. No demo data
was read or changed for this QA. No physical-device/all-browser claim.

Screenshots remain outside Git in the task's local visualization directory under
tv4-pr5-qa: customer-reply-1440.png, customer-reply-390.png, crm-replied-1440.png.
No .env, local_settings, credential, log, screenshot or temporary QA file is staged.

PR #5 remains pending owner review; no merge or auto-merge is authorized.
