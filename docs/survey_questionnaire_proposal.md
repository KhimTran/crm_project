# Eight-question survey update: approval proposal

Status: the owner approved this proposal and migration testing on a separate
database on 2026-10-18. Implemented by migration 0003; not applied to the running
development/demo database. See `survey_questionnaire_update.md` for evidence.

## Verified current flow

- `/surveys/manage/`: Survey management. `SurveyForm` creates an empty DRAFT;
  `QuestionForm` stores TEXT, SINGLE_CHOICE, MULTI_CHOICE or RATING questions.
- `/surveys/mine/` and `/surveys/recipients/<recipient_id>/`: customers see their
  assigned surveys and answer them in the existing `take.html` form.
- POST `/surveys/recipients/<recipient_id>/submit/`: JSON in the `answers` form
  field, validated and stored atomically by `submit_survey`. The unique response
  and recipient lock already prevent duplicate submissions.
- `/surveys/manage/<survey_id>/stats/`: existing per-survey response statistics.
- `/crm/reports/customers/`: Customer Report currently reports demographics,
  saved preferences and product feedback. It does not consume SurveyAnswer.
- No NPS calculation was found. The requested 1–10 question will show its score
  distribution only; it will not be labelled NPS or combined with 1–5 ratings.

Live read-only inspection confirmed `surveys/0001_initial` and
`0002_schema_contract` are applied and `chk_survey_answers_rating` permits only
NULL or 1–5. A value of 6–10 currently fails at the database layer. There are no
stored question settings for matrix criteria, maximum selections, an Other
option, sections or survey-template versions.

## Proposed schema change (requires approval)

1. Add `Survey.template_key`, a nullable/blank English string identifying the
   questionnaire version, e.g. `BADMINTON_SHOP_EXPERIENCE_V1`. Existing surveys
   receive no template key and continue as legacy/custom surveys.
2. Add `SurveyQuestion.config`, a JSON object defaulting to `{}`. It stores the
   stable question key, section label, rating bounds, maximum selections, Other
   option reference, and placeholder. Existing empty settings retain all current
   question behavior, including the 1–5 rating range.
3. Add MATRIX to the application's question-type choices (the existing varchar
   column can store it). Matrix criteria use existing SurveyOption rows; each
   criterion answer uses the existing option/rating/text answer columns. A score
   is stored as 1–5; Not used is stored explicitly as `answer_text="NOT_USED"`
   with a NULL rating. No answer row means unanswered. No extra table is needed.
4. Change only the survey-answer rating CHECK to NULL or 1–10 in a new migration.
   Application validation still enforces each question's configured bounds, so
   old questions remain 1–5. Reverse migration must refuse to narrow the CHECK
   while 6–10 values exist; it must never delete or coerce those answers. It also
   refuses reversal while answers depend on nonempty question settings, avoiding
   loss of matrix/Other interpretation metadata.

No account, customer, catalog or feedback schema changes. No old migration is
edited. No existing survey questions, options, answers or recipients are replaced.
The migration is additive except for widening a CHECK range, and performs no
data conversion. It will first be reviewed and exercised on a disposable MySQL
test database; applying it to a running development/demo database remains an
explicit deployment step after approval and migration review.

## Planned behavior, preserving current forms/styles

- New surveys default to the eight-question version; the existing create form,
  detail cards, edit form, navigation and open/close flow remain in place.
  Existing surveys remain separate; upgrading one means creating a new survey
  with new IDs, never relabelling its old answers. Required flags remain editable
  for questions 1–7; question 8 stays optional. Configuration and preview read
  the stored settings rather than infer meaning from display order or text.
- Customer answers use existing checkbox/radio/rating/textarea controls. The
  matrix uses four labelled score selectors in the existing question fieldset,
  avoiding a new wide layout. Other uses the existing input styling. Client and
  server enforce maximum 3 choices, conditional Other text, distinct matrix
  states, integral 1–10 scores and optional feedback. Failed submissions retain
  input; success follows the existing result page and duplicate-send protection.
- Survey statistics and Customer Report reuse their existing cards/tables/bars.
  Customer Report gains a survey selector and question results using the current
  report components. Reports stay separated by survey ID/version. Multi-choice
  percentages use distinct valid respondents for that question, with an explicit
  note that totals can exceed 100%. Matrix averages exclude NOT_USED/unanswered;
  those states have separate counts. Other/free-text values remain escaped.
- Existing demographic/feedback report data is not reinterpreted as survey data.
  No shared styles/components or other module behavior are changed.

## Verification after approval

Test configuration → assignment → answer submission → database rows → both
reports using synthetic MySQL fixtures. Include all stated validation cases,
duplicate submission, permission/CSRF, rollback/error retention, exact counts and
denominators, empty results, mixed old/new surveys and migration preservation.
Compare existing form/style in desktop/mobile browser checks. Preserve all
uncommitted changes from the preceding Customers task.
