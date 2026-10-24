# Eight-question questionnaire — 2026-10-18

## Completed behavior

The three requested entry points were traced before changes: Surveys management
at `/surveys/manage/`, assigned customer surveys at `/surveys/mine/` and
`/surveys/recipients/<recipient_id>/`, and Customer Report at
`/crm/reports/customers/`. Existing survey statistics live at
`/surveys/manage/<survey_id>/stats/`. There is no existing NPS calculation.

- Creating a Survey through its unchanged create form now atomically creates
  a separate DRAFT snapshot of the eight questions and three sections.
  `BADMINTON_SHOP_EXPERIENCE_V1` identifies this version; question keys/settings
  are stored rather than inferred from text, order or old IDs. Existing surveys
  are not upgraded or overwritten. New versions use distinct Survey/Question IDs.
- Configuration retains the existing question edit form. Required flags 1–7
  are editable; question 8 remains optional. This version keeps eight questions,
  their order, choice/criterion counts, max-three constraint, Other position,
  sections and score ranges. Draft question text/options and hints can be edited.
  Surveys with recipients or answers cannot have options rebuilt. Legacy/custom
  drafts retain their existing add/move/delete controls.
- Customer answering keeps the same page, fieldsets, checkbox/radio/rating and
  textarea components. The matrix adds four selectors using existing form styles.
  Each criterion stores either a 1–5 score or explicit NOT_USED text with NULL
  rating; no row represents unanswered. Other requires up to 200 characters when
  selected, is cleared/disabled when unselected, and stale text is rejected by
  the server. Question 5 accepts one to three selections, question 7 only integral
  1–10, and question 8 can be omitted or blank. Existing legacy ratings stay 1–5.
- The existing submission route/form-encoded JSON contract is reused. Browser
  fetch submissions request JSON; validation/database/network errors preserve
  the form. Existing confirmation and result navigation remain. A pending guard,
  disabled submit button, recipient lock and unique response prevent duplicate
  saves. Success is displayed only after saving or confirming an existing
  completed submission.
- Survey statistics and Customer Report use the same `build_stats` results and
  a shared template scoped to these pages. Current cards/tables/bars are reused;
  shared styles, typography, colors and navigation are unchanged. Customer Report
  keeps its existing demographic/preference/feedback sections and adds a survey
  selector/results in the same report components. Its Survey results follow the
  existing Survey manager permissions; CUSTOMER_SERVICE gains no new survey-data
  access while retaining demographic reports.
- All counts are per selected Survey ID. Choice percentages use distinct valid
  respondents to that question, with an explicit multi-choice denominator note.
  Matrix distributions use scored respondents, means exclude NOT_USED/unanswered,
  and both states have separate counts. Unanswered counts refer to submitted
  responses that omitted the question/criterion; unfinished assignments remain
  in the existing Pending KPI. Other/comments are escaped and shown
  using existing text lists (up to the existing 200-row display limit). Question
  7 shows its ten-point distribution without an assumed NPS/summary calculation.
  Empty results have zero counts/percentages and no fabricated mean.

## Schema and deployment

The owner approved the proposal in `survey_questionnaire_proposal.md` before
model/migration edits. Migration `surveys/0003_questionnaire_configuration` adds
nullable `Survey.template_key`, `SurveyQuestion.config` (default `{}`), and widens
only the survey rating CHECK to 1–10. No old migration is edited and no business
table is added. Existing surveys remain unversioned with empty settings and the
old application behavior. MySQL DDL runs outside transactions as required.

Actual survey FK relationships were inspected: answers → response/question use
CASCADE; answers → option uses SET NULL; options → question, questions → survey,
recipients → survey and response → recipient use CASCADE; recipient → customer
and survey → creator use RESTRICT. No relationship or delete action changes.

The running development/demo database is **not migrated** by this task. Before
using this code there, review and run with the same settings as that server:

```powershell
venv\Scripts\python.exe manage.py migrate --plan
venv\Scripts\python.exe manage.py migrate surveys
```

Use normal database backup/deployment precautions; this is an additive migration
with no answer conversion. Do not restore the older SQL dump over existing data.
The repository SQL dump is unchanged and therefore needs migration 0003 after
import. There is no automatic rewrite of active/answered surveys: create a new
Survey to distribute this questionnaire, retaining old results separately.

Reverse migration refuses to narrow when 6–10 scores exist, and refuses to drop
settings while configured answers depend on them. It never deletes/coerces
answers to make reversal succeed.

## Changed files for this task

- `apps/surveys/models.py`, `constants.py`, `configuration.py`, `questionnaire.py`,
  `forms.py`, `services.py`, `views.py`.
- `apps/surveys/migrations/0003_questionnaire_configuration.py` and
  `apps/surveys/test_questionnaire.py`.
- `templates/surveys/take.html`, `question_form.html`, `manage_detail.html`,
  `manage_stats.html`, `_stats_content.html`; `static/js/survey_take.js`.
- Only `customer_report` in `apps/customers/views.py`, and
  `templates/customers/customer_report.html`.
- This document, the approval proposal and `plans.md`.

All pre-existing uncommitted Customers/Accounts/test/.env.example changes were
preserved. No Catalog, customer CRUD, authentication, feedback or shared CSS
behavior changes were made for this task. No dependency upgrades or new packages.

## Verification

- Focused Survey + Customer Report suite: 53/53 passed in 51.188s on dedicated
  MySQL `test_crm_db` after the initial MySQL DDL transaction fix.
- Migration preservation: private MySQL `test_survey_01a14afb` was taken to the
  old schema while empty; synthetic legacy content/answers were inserted, then
  migration 0003 applied. All old fields in all six survey tables, including IDs,
  options, answers and timestamps, compared exactly before/after.
- Reverse guards were exercised on the private QA database: a score of 10 blocks
  narrowing; with high fixture scores temporarily changed inside a rolled-back
  transaction, configured answers still block metadata removal. No DDL or lasting
  data changes occurred in these guard checks.
- Real browser: unchanged Survey create form → eight-question draft → edit/save
  Other configuration → preview two synthetic recipients → send → customer
  answers → stored responses → both reports. Checked max-three error, toggle/
  clear/disable Other, optional blank question 8, explicit NOT_USED, score 10,
  network disconnection retaining answers, successful retry and completion.
- Two real browser submissions were independently checked in MySQL: 1–5 mean 4;
  matrix means `[5, 3, 4, 4]`, NOT_USED counts `[1, 0, 1, 0]`; highlight percentages
  `[100%, 50%]`; one Other value and one comment; recommendation scores 1 and 10.
  The five legacy answer rows stayed intact. A third empty version showed zero
  counts/percentages, unset averages and no NaN/Infinity on both report pages.
- Desktop 1440 and mobile 390 tested. Customer form has eight fieldsets and three
  group headings; its controls stay within the viewport. Both report pages fit
  the mobile document width; existing Survey tables/bars remain in bounds.
  Screenshots were saved for management, answering and reports.
- Browser cleanup completed: three synthetic accounts, two Customer profiles,
  three surveys (legacy, version 1 and empty), their question/option/recipient/
  response/answer rows and authenticated sessions were removed from the private
  QA database. The QA server was stopped and viewport override reset.
- Initial full regression on the shared test name was invalidated when
  `test_crm_db` disappeared during execution (deadlock, missing tables/database).
  Final regression therefore uses a separate `test_survey_regression_01a14afb`
  database through temporary settings outside Git. Final results follow below.

No real customer/survey data was used for destructive testing or converted. The
shared development/demo deployment and its new migration remain unverified.
