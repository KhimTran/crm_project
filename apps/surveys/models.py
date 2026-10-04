from django.conf import settings
from django.db import models


class Survey(models.Model):
    survey_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, db_column="created_by")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "surveys"


class SurveyQuestion(models.Model):
    question_id = models.AutoField(primary_key=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, db_column="survey_id")
    question_text = models.TextField()
    question_type = models.CharField(max_length=30)
    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "survey_questions"
        indexes = [models.Index(fields=["survey"], name="idx_survey_questions_survey")]


class SurveyOption(models.Model):
    option_id = models.AutoField(primary_key=True)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, db_column="question_id")
    option_text = models.CharField(max_length=255)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "survey_options"
        indexes = [models.Index(fields=["question"], name="idx_survey_options_question")]


class SurveyRecipient(models.Model):
    recipient_id = models.AutoField(primary_key=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, db_column="survey_id")
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, db_column="customer_id")
    status = models.CharField(max_length=20)
    sent_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "survey_recipients"
        indexes = [
            models.Index(fields=["survey"], name="idx_survey_recipients_survey"),
            models.Index(fields=["customer"], name="idx_survey_recipients_customer"),
        ]
        constraints = [models.UniqueConstraint(fields=["survey", "customer"], name="uq_survey_recipients_survey_customer")]


class SurveyResponse(models.Model):
    response_id = models.AutoField(primary_key=True)
    recipient = models.OneToOneField(SurveyRecipient, on_delete=models.CASCADE, db_column="recipient_id", related_name="response")
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "survey_responses"
        constraints = [models.UniqueConstraint(fields=["recipient"], name="uq_survey_responses_recipient")]


class SurveyAnswer(models.Model):
    answer_id = models.AutoField(primary_key=True)
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, db_column="response_id")
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, db_column="question_id")
    option = models.ForeignKey(SurveyOption, on_delete=models.SET_NULL, null=True, blank=True, db_column="option_id")
    answer_text = models.TextField(null=True, blank=True)
    rating_value = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "survey_answers"
        indexes = [
            models.Index(fields=["response"], name="idx_survey_answers_response"),
            models.Index(fields=["question"], name="idx_survey_answers_question"),
            models.Index(fields=["option"], name="idx_survey_answers_option"),
        ]
