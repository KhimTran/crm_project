# Impact matrix

| File | Reason / risk | Verification |
| --- | --- | --- |
| `.gitattributes` | Document schema or preserve dump bytes | Diff review and source/schema comparison |
| `AGENTS.md` | Document schema or preserve dump bytes | Diff review and source/schema comparison |
| `apps/accounts/api_auth.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/customer_views.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/decorators.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/forms.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/managers.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/middleware.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/migrations/0005_expand_role_foreign_key.py` | Expand/backfill/verify/contract and unique-index cleanup; HIGH | Fresh MySQL suite, restored clone, forward/reverse rehearsal, value/FK checks |
| `apps/accounts/migrations/0006_contract_role_foreign_key.py` | Expand/backfill/verify/contract and unique-index cleanup; HIGH | Fresh MySQL suite, restored clone, forward/reverse rehearsal, value/FK checks |
| `apps/accounts/migrations/0007_remove_duplicate_role_index.py` | Expand/backfill/verify/contract and unique-index cleanup; HIGH | Fresh MySQL suite, restored clone, forward/reverse rehearsal, value/FK checks |
| `apps/accounts/models.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/permissions.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/provisioning.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/selectors.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/services.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/accounts/tests/test_api.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_birth_dates.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_customer_auth.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_decorators.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_models.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_portal_sessions.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_post_refactor_verification.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_role_foreign_key.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/accounts/tests/test_views.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/admin_portal/test_staff_login.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/admin_portal/tests.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/admin_portal/views.py` | Account/auth/session/RBAC consumes explicit role code; HIGH | Accounts, real portal POST/CSRF, revocation, Groups, API and HTTP flows |
| `apps/catalog/management/commands/seed_demo.py` | Document schema or preserve dump bytes | Diff review and source/schema comparison |
| `apps/customers/context_processors.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/management/commands/repair_customer_profiles.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/models.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/portal_text.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/provisioning.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/services.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/customers/test_profile_views.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/test_self_services.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/tests/test_account_lifecycle.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/tests/test_admin_customer_sync.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/tests/test_create_customer.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/tests/test_save_customer.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/tests/test_seed_demo.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/customers/views.py` | Customer proxy and guards filter through Role; HIGH | Customer CRUD, preferences, registration, reports, role revocation |
| `apps/feedback/views.py` | Customer ownership guard reads code; HIGH | Customer feedback and handling lifecycle, real HTTP |
| `apps/surveys/management/commands/seed_survey_report_demo.py` | Recipient selection and survey guards join Role; HIGH | Survey lifecycle, audiences, ownership, answers and reports |
| `apps/surveys/services.py` | Recipient selection and survey guards join Role; HIGH | Survey lifecycle, audiences, ownership, answers and reports |
| `apps/surveys/test_new_recipients.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `apps/surveys/test_survey_report.py` | Use explicit business code or FK schema; assertions retain business expectations | Full MySQL regression and five new FK integrity tests |
| `database/crm_db.sql` | Fresh, synthetic demo exports use normalized schema; HIGH | Verified full import/restore, repeated seed and data-only import |
| `database/seed_survey_report.sql` | Fresh, synthetic demo exports use normalized schema; HIGH | Verified full import/restore, repeated seed and data-only import |
| `docs/database_schema.md` | Document schema or preserve dump bytes | Diff review and source/schema comparison |
| `plans.md` | Document schema or preserve dump bytes | Diff review and source/schema comparison |
| `scripts/audit_crm_flows.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/audit_report_browser.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/check_feedback_layout.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/check_survey_list_layout.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/deploy_role_normalization.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/export_demo_sql.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `scripts/verify_role_integrity.py` | Role-aware audit/export/deployment/integrity support; MEDIUM | Actual execution on disposable MySQL sources |
| `templates/admin/portal/profile.html` | Account object role display/guards read code; MEDIUM | Template rendering, navigation and real HTTP |
| `templates/layouts/base_crm.html` | Account object role display/guards read code; MEDIUM | Template rendering, navigation and real HTTP |
| `templates/layouts/base_customer.html` | Account object role display/guards read code; MEDIUM | Template rendering, navigation and real HTTP |
| `templates/manager/profile.html` | Account object role display/guards read code; MEDIUM | Template rendering, navigation and real HTTP |
