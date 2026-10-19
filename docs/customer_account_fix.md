# Customer account creation and deletion — 2026-10-18

## Causes and changes

- Manager creation created both `Account` and `Customer`. Admin HTML/API creation
  called `accounts.services.create_account`, which created only `Account`.
  CRM lists query `Customer`; own-profile access queries the authenticated
  account's active `Customer`. Thus the same missing profile caused both the
  missing CRM row and the profile 403. Admin CUSTOMER creation now provisions
  the OneToOne profile within the account transaction. The initial full name is
  the email truncated to the existing 150-character limit; the customer can
  supply their name in their own profile. No personal information is invented.
- Admin Account deletion rejected every `customers.account_id` reference.
  Customer management already supported soft deletion and account locking.
  The owner explicitly approved applying that behavior to admin Account UI/API
  deletion for role CUSTOMER with a profile. It retains the account, preferences,
  feedback, surveys and technical references. Repeated deletion is harmless.
  The existing hard-delete protection remains for other accounts.
- There is no `createdBy` or manager-owner filter in the Customer list, nor a
  manager/branch ownership column in the current schema. Existing CRM role/group
  authorization and the current shared CRM scope are retained. No new scope or
  permission bypass was introduced. Profile lookup still uses the authenticated
  account ID; supplied account/customer IDs cannot select another profile.
- Customer creation now requires the supplied password, uses Django's existing
  validators and `AccountManager.create_user` hashing, and returns only Customer.
  No generated password is returned or included in Django messages. The form
  no longer contains or submits `play_styles`/`brands`; unsolicited values are
  ignored by its field whitelist. Existing preferences, model columns, filtering
  and other preference consumers remain intact.

## UI and affected code

Customer creation opens on a separate page, matching Catalog's existing create
page: `portal-section-intro`, `portal-panel`, full-width stacked inputs and
Bootstrap Save/Cancel buttons at the bottom. The same Manager/Admin layout and
shared portal styles are reused without changing Catalog or shared style rules.
Legacy CRM group users retain the CRM layout. Password visibility, configured
password help, field errors, submit progress, keyboard focus and internal table
scrolling are scoped to Customers. Admin
Account deletion confirmation/message now describes soft deletion explicitly.

`POST /crm/customers/new/` accepts the existing form-encoded fields and CSRF
token. With `Accept: application/json`, it returns 201 with the Customer ID and
the freshly rendered list; invalid fields return 400, a duplicate caught by the
service returns 409, and database failures return a sanitized 503. The same
authorization decorators and form/service handle HTML and JSON submissions.
No additional account-creation workflow or widened API permission is introduced.

The browser submits using `fetch` with a pending guard and disabled Save button.
On 201, it resets/removes the form, displays the success message and replaces
the Customers content with the server-rendered list without a document reload.
On validation, duplicate, server, session or network errors, it preserves input
and re-enables Save. Passwords are never included in responses or messages.
The response list is rendered inside the save transaction, so a database failure
while rendering also rolls back account/profile creation. A lost network response
cannot prove whether a commit occurred; the UI explains that uncertainty and
does not retry automatically. The existing unique email constraint prevents a
retry from creating another account.

Implementation: `apps/accounts/services.py`, `apps/accounts/views.py`,
`apps/customers/{forms,services,views,portal_text,provisioning}.py`,
`apps/customers/management/commands/repair_customer_profiles.py`,
`templates/customers/{customer_form,customer_list,_customer_list}.html`,
`static/css/crm_customers.css`, `static/js/{customer_create,admin_portal}.js`.
Tests include `apps/customers/tests/{test_account_lifecycle,test_save_customer}.py`, the existing
Customer/Account suites, and password-fixture adaptations in two Feedback test
files. Feedback production logic is unchanged.

Changed test files: `apps/accounts/tests/{test_api,test_services}.py`;
`apps/customers/tests/{test_admin_access,test_create_customer,test_customer_detail,
test_customer_report,test_filter_customers,test_lock_delete_customer,
test_account_lifecycle,test_save_customer}.py`;
`apps/feedback/tests/{test_customer_feedback,test_handle_feedback}.py`.
The management command package also adds its two `__init__.py` files.
Documentation: this file and `plans.md`. The pre-existing `.env.example` change
belongs to the user's work and was preserved.

## Repair existing accounts

No schema migration is required. Existing missing profiles need an explicit
maintenance command using the **same settings/database as the running server**:

```powershell
python manage.py repair_customer_profiles
python manage.py repair_customer_profiles --apply
```

The first command only previews the database name and candidate account IDs.
Review them before applying; optionally add `--account-id 123` (repeatable) to
both commands. Append the server's `--settings=...` argument when it uses custom
settings. The command was tested only on the dedicated test database; it has not
been applied to the user's development/demo data.

Only CUSTOMER accounts without any Customer row are candidates. CRM_MANAGER and
CUSTOMER_SERVICE group members are excluded. Existing and deleted profiles are
never overwritten or revived. Locked accounts stay locked; passwords, groups,
IDs and saved preferences remain unchanged. Transactions, account row locks and
the existing OneToOne unique constraint make repeated runs safe.

A missing profile continues to return the existing controlled 403 until repaired;
GET profile requests do not create database rows. The command cannot recover
personal information that was never saved; repaired customers complete it later.

## Verification

- Focused lifecycle/Save suite: 14/14 passed (36.598s).
- Full Django suite: 347/347 passed (499.287s), using
  `python manage.py test --settings=config.test_settings --keepdb --noinput`
  on MySQL `test_crm_db`. Includes existing Account, Customer, Feedback, Catalog,
  Survey, login/profile, permission and database-tool regressions.
- Django system check: 0 issues; `makemigrations --check --dry-run`: no changes;
  Python compilation, both changed JavaScript syntax checks and diff whitespace
  checks passed. Static collection dry-run passed with an isolated temporary
  `STATIC_ROOT`; the repository does not configure a deployment `STATIC_ROOT`.
- Interactive browser on separate MySQL `test_customer_save_01a14afb`: actual
  MANAGER login; Catalog/create style comparison; Customers creation; required,
  weak-password/invalid-phone and duplicate errors; password toggle; deliberate
  API disconnection with input retained and no false success; retry; disabled
  Saving state and rapid Save/Enter; one POST 201 and one persisted profile.
  The list updated without a GET/document reload, and the row survived a manual
  reload. Reopening Create showed an empty form.
- Both manager-created and admin-created CUSTOMER accounts logged in and opened
  their own profile. Manager saw the admin-created customer. Admin deleted the
  manager-created customer from Accounts; database verification confirmed
  Customer DELETED and Account LOCKED, and the row disappeared from Customers.
- Desktop 1440px and mobile 390px checked. Catalog and Customer form panel/input
  computed styles matched. Mobile document width was 390px; every input/button
  stayed inside the viewport and Save/Cancel were reachable by scrolling. Saved
  screenshots document the full form on desktop/mobile and resulting lists.

All four browser accounts, both profiles and their authenticated sessions were
removed from the dedicated disposable UI database after verification; the QA
server was stopped. No development/demo account was
used for deletion testing, and no schema migration, seed, reset or profile repair
was run against development/demo data. Real deployment configuration/data remain
unverified; run the preview/apply maintenance command above for old missing profiles.
