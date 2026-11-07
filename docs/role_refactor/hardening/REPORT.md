# PR #27 hardening and independent merge-readiness verification — 2026-11-07

Starting commit: `2fe237a0bd132865af38497ebd5056b679d03492`, clean feature/normalize-account-role. Fetch confirmed develop remains at `28eb667fb7e7a56011eff2eb85729d85ad5e2702`; GitHub reported no conflict. Prior evidence was checked against source, schema and new executions rather than assumed.

## Findings and fixes

1. Runtime resolve_account_role used get_or_create, silently repairing missing configuration and permitting a role-table write from account creation. It now validates the code and performs get only, returning controlled ValidationError for missing Roles. Existing initialization/seed/migration code owns creation; new explicit initialize_roles adds only missing standard rows and is idempotent. No post_migrate or request-time auto-repair signal was added.
2. Account.role_code returned CUSTOMER when the FK was absent and save defaulted it again. Default CUSTOMER is now resolved only on construction of a new Account without a specified relation. Loaded/deferred objects do not resolve defaults. Missing/null/orphan relations fail closed; an existing Account with a cleared FK cannot silently change roles on save. create_user resolves using its manager's database alias.
3. Account list exhibited N+1: 5 queries for one row versus 24 for twenty. Explicit Role joins reduce both to **3 queries**. Customer list is covered by a one-query test; authentication and session reload each fetch the current Role in one query. Read guards still reread the database; no cross-request cache was introduced. Paths explicitly taking select_for_update retain their original lock footprint.
4. HTTP seed cleanup used final-demo fixtures despite the pre-existing guard. The harness now migrates a separate disposable database, creates its Manager fixture, seeds 30 customers and actually clears them, checking the main audit clone is unchanged. The production guard is unchanged. Both HTTP/full-suite runners now report a nonzero exit when their recorded tests fail.
5. A baseline Survey fixture subtracting five minutes crossed into yesterday shortly after midnight. The first full hardening run recorded **515 PASS + 1 ERROR**. Unmodified baseline source reproduced this at frozen local 00:02. A calendar-day fixture passes the identical full lifecycle at 00:02 with original assertions intact; no production Survey validation changed. See midnight_fixture.json.
6. Data Dictionary conflated ORM defaults with SQL defaults. It now records the real distinction and the preserved DATETIME precision difference between fresh and imported local schemas. No cosmetic schema migration was added.

Seven new hardening tests verify read-only resolution, missing-role errors, explicit/default construction, invalid relations, initializer idempotence, bounded list queries and fresh authentication/session-role revocation. The three existing TransactionTestCase fixtures explicitly initialize Roles after framework flush, instead of relying on runtime account creation to repair them. All 509 prior tests remain.

## Automated and HTTP results

**516 passed, 0 failed, 0 errors, 0 skipped**, 458.36 seconds, unique MySQL database `test_crm_audit_efcaa6a0f4`. Fresh migrations ran during setup. Per-test outcomes and timing: verified/full_suite.json and verified/suite_summary.json. [Per-module counts](../TEST_RESULTS.md). The failed first run is retained under regression/ and explained above, not concealed.

**HTTP audit 15/15 PASS**, including real CSRF login, Account/Customer lifecycle, role changes and revocation, Feedback, saved Survey audience/answers/statistics, reports reconciled with SQL, API pagination/validation and actual legacy seed cleanup in appropriate disposable fixtures. The prior 14/15 limitation is resolved in the harness; the production data-protection guard remains active. See http/http_flows.json and http/http_isolation.json.

Deterministic clock probes: two PASS, proving baseline rejection and the corrected full lifecycle at 00:02. Django check, makemigrations --check --dry-run and migrate --plan pass with no pending migration. Existing Account migrations 0001–0007 were not edited, and canonical SQL/seed files were not replaced.

## Actual browser E2E

Headless Microsoft Edge with CDP used separate disposable MySQL clones and ports 8027/8019. No live login, form mutation, seed or restore was performed against crm_db. These are actual DOM/native-form submissions, Bootstrap modal events and JavaScript handlers; assertions read database rows after writes.

| Area | Executed browser checks | Result |
| --- | --- | --- |
| ADMIN | Login/dashboard redirect, invalid-password form errors, Account create/detail/role change/lock/unlock/password reset, Customer navigation, actual backup UI, logout | PASS |
| MANAGER | Login/dashboard redirect, Catalog create/edit/delete of a disposable product, Customer/Feedback/Survey navigation, Customer reports, Survey stats/results, logout | PASS |
| CUSTOMER | Registration, default Role, login, profile update, password change preserving session, catalog, NEW Feedback/history, invitations, Survey submit/result, logout | PASS |
| Sessions/security | Three independent portal cookies coexist; each logout removes only its cookie and retains the others; forged CSRF returns 403; Customer denied Admin portal | PASS |
| Responsive UI | Eight checks across Account list, Customer list, Customer reports and profile at 1440/390 CSS pixels; main/forms rendered; no body overflow | PASS |
| Survey/Feedback JS | Create/edit/reorder/add/delete question cards; saved audience publish; Single/Multi/Text/Rating/Matrix inputs; submit; resolve Feedback; five rendered report charts | PASS |

**26 portal cases + 8 Survey/Feedback cases**, with 55 successful portal document responses and zero unexpected HTTP errors. Portal browser has zero JavaScript exceptions and zero failed network loads. Its one network console entry is the deliberate forged-CSRF Fetch returning 403; retained explicitly in evidence rather than claimed as zero total console entries. Survey browser has zero console errors, zero network failures and zero HTTP failures. Specialized Survey Results was checked against its published 8-question scope; the custom questionnaire remains excluded as required.

Evidence: browser_portals/results.json and browser_survey/browser_survey.json. Browser-harness selector/cleanup issues encountered during preparation were fixed in the harness; assertions were rerun successfully. This covers Edge responsive viewports, not every browser/device or a pixel-perfect visual comparison.

## Database and restore

The real local database was used **read-only**. Source snapshot and final checks cover all 22 tables; fingerprints are identical across this task, including Account IDs, email, password hashes, status, profile data, timestamps, Groups/Permissions and all business records. Counts remain 20 Accounts: ADMIN2/MANAGER3/CUSTOMER15. All 25 physical FKs have zero orphans. Codes remain unique with one unique index and the three-code CHECK.

A new full backup was restored to a new disposable database and compared identically across all 22 tables. The old canonical VARCHAR backup was restored independently, migrated with the current code, reversed and migrated again: 20/20 mappings, exact original account/unrelated values retained, no orphan FK. Canonical backup and SQL files were not overwritten. Operational recovery SQL and manifests stay ignored in database/backups/.

Actual Admin restore/recovery E2E was rerun: successful full restore, malformed dump rejection, exact automatic recovery after partial import, fail-closed corrupt recovery media and operator recovery all passed on a disposable database. Evidence: integrity_restore.json, restore/verification.json, schema_contract.json and final_checks.json.

There is **no new model-state migration**, no live migration/seed/restore/reset, and no live schema change in this hardening. Only the development server was restarted to load new code; root/login/OpenAPI GET smoke checks return 200 with fingerprints unchanged.

## API and team rollout

No API route/schema/payload field was changed. Existing tests and actual HTTP keep role strings ADMIN/MANAGER/CUSTOMER, AccountOutput/profile.type, status codes, URLs and validation for valid configuration. Missing Role configuration now fails explicitly without writes. Raw Role IDs remain internal and are never hardcoded.

[TEAM_UPGRADE.md](../TEAM_UPGRADE.md) gives separate safe paths for an existing role_id schema, VARCHAR schema, fresh database and older backup restore. It requires verified restore/clone rehearsal before an old-schema deployment and forbids fake/reset/destructive imports. It identifies the old dated deployment script as environment-specific, not a generic migration recipe.

## Review state and limits

Technical gates: **TECHNICALLY_VERIFIED**. PR preparation: **READY_FOR_REVIEW**. GitHub's develop ruleset requires at least one approving review, blocks branch deletion/non-fast-forward updates, and has no approval on PR #27 at inspection. No approval, merge, force push or bypass was performed. Empty GitHub CI status/workflow results are not represented as a passing CI run; local MySQL/browser evidence is supplied for review.

Shared/production rollout remains a separate coordinated operation. Browser coverage is limited to Edge and the stated viewports. Missing Roles now require explicit operator initialization/investigation; this is intentional fail-closed behavior. Detailed per-file scope: [IMPACT_MATRIX.md](../IMPACT_MATRIX.md).
