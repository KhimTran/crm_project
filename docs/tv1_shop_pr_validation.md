# TV1 shop redesign — PR validation, 2026-10-13

## Approved scope and Git state

The owner approved the compact retail design and explicitly authorized committing,
fetching/integrating origin/develop, pushing feature/tv1-shop-redesign and opening a
PR targeting develop. The PR must remain open for final owner review; no merge or
auto-merge is authorized.

Worktree: C:/Users/Khiem/.codex/worktrees/44c0/crm_project.
The approved retail revision was committed as ed06697, following the first redesign
commit d22c43f. Only the 19 known storefront/source/test/documentation/asset paths
were staged. .env and config/local_settings.py remain ignored and untracked by Git;
no credentials, QA scripts, screenshots, logs or temporary files were staged.

Fetch succeeded. origin/develop is 6dc43723c0d2a53c5e81e6b27df7403cd1353471,
already an ancestor of the feature branch. Running git merge --no-edit origin/develop
returned Already up to date; no conflict resolution or integration merge commit was
needed. A final ls-remote check confirmed the same develop SHA after verification.

## TV4/TV5 integration state

At the fetched develop revision:
- Customer CRM list/create/lock/unlock/delete and profile routes exist.
- Feedback views are scaffold; no feedback URL configuration or customer feedback
  menu exists.
- Surveys has send/send-result and recipient take/submit/result routes. It has no
  customer survey-list route/menu; base_customer only contained a planned survey
  placeholder in the pre-redesign version.
- base_crm still shows planned feedback/survey menu placeholders. It and Admin
  templates/CSS were not changed by this branch.

No unmerged TV4/TV5 feature branch was brought into this PR. The existing survey
service/routes/templates remain intact. No fake feedback/survey navigation was
added. Later functional menus should be integrated when those modules reach develop.

## Checks and actual results

Source revision tested: ed06697 (later commits contain documentation only).
Runtime: Windows CPython 3.12, Django 5.2.17 and existing MySQL.

Commands:
```powershell
D:/Python312/python.exe manage.py check --settings=config.local_settings
D:/Python312/python.exe manage.py makemigrations --check --dry-run --settings=config.local_settings
D:/Python312/python.exe manage.py test --settings=config.test_settings --keepdb --noinput
git -c core.safecrlf=false diff --check
```

- System check: 0 issues.
- Migration dry-run: No changes detected. No migration/model/config file is changed
  relative to origin/develop.
- Full suite: **212 tests passed in 214.456s** on **test_crm_db**.
  TEST.NAME was printed and asserted before the runner. No tests used crm_tv1_demo.
- The runner's seed-command test output refers to its isolated test database; no
  seed/reset/migrate/restore was run against the demo database.

## Browser regression

Public storefront read-only checks used preview8001/config.local_settings:
- Fresh home, actual GET search Demo Racket 13 returns one product, detail shows
  1.300.000 ₫, full category/brand/name preserved.
- At 390px combined Demo Rackets/Demo Brand/100000–1500000 filters and page2 retain
  parameters and show Demo Racket 13/14; mobile filters collapse normally.
- Login/register layouts preserve field names and show no horizontal overflow.
- Home at 1440×900 and zoom100% (Ctrl+0, visualViewport.scale=1) has no horizontal
  overflow; viewport override was reset after QA.

Authentication and write checks used a temporary server8002 pointing to test_crm_db,
with separate session/CSRF cookie names. Fixtures were created only after the full
test runner finished:
- Customer login, account-menu profile navigation, phone save and success message.
- Existing survey recipient page, single-choice radio submission and completion
  message; database assertion confirms one response and one answer.
- CRM_MANAGER login lands at /crm/; customer list opens with crm.css and
  crm_customers.css, without customer storefront styles.
- Admin login/accounts/product list opens with admin_portal.css and no storefront
  CSS. Existing Admin CDN dependency was preserved; this PR does not modify Admin.
- QA cleanup verified the profile phone and completed recipient, then removed only
  this run's three Account fixtures, Customer/preferences, Category, Survey and its
  dependent objects, newly created Group, and authenticated sessions. The QA server
  was stopped and temporary settings/credential scripts removed.

There is no feedback UI on the fetched develop revision to exercise. Survey-list
menus were not tested because no such route exists there. These checks used a
desktop browser with responsive viewports, not a physical phone or every browser.

Screenshots are outside the repository in the chat visualization directory:
pr-ready-shop-1440.jpg, pr-ready-crm.jpg and pr-ready-admin.jpg.
The main checkout was not switched or modified.
