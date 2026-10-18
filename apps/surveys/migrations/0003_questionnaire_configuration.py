"""Add version/settings without rewriting existing survey content or answers."""
from django.db import migrations, models
from django.db.migrations.exceptions import IrreversibleError


def widen_rating(apps, schema_editor):
    if schema_editor.connection.vendor == "mysql":
        schema_editor.execute("ALTER TABLE survey_answers ADD CONSTRAINT chk_survey_answers_rating_1_10 "
                              "CHECK (rating_value IS NULL OR rating_value BETWEEN 1 AND 10)")
        schema_editor.execute("ALTER TABLE survey_answers DROP CHECK chk_survey_answers_rating")


def narrow_rating(apps, schema_editor):
    answer = apps.get_model("surveys", "SurveyAnswer")
    if answer.objects.using(schema_editor.connection.alias).filter(rating_value__gt=5).exists():
        raise IrreversibleError("Survey scores 6–10 exist; refusing to remove or change answers.")
    if answer.objects.using(schema_editor.connection.alias).exclude(question__config={}).exists():
        raise IrreversibleError("Configured survey answers exist; refusing to remove their interpretation settings.")
    if schema_editor.connection.vendor == "mysql":
        schema_editor.execute("ALTER TABLE survey_answers ADD CONSTRAINT chk_survey_answers_rating "
                              "CHECK (rating_value IS NULL OR rating_value BETWEEN 1 AND 5)")
        schema_editor.execute("ALTER TABLE survey_answers DROP CHECK chk_survey_answers_rating_1_10")


class Migration(migrations.Migration):
    atomic = False  # MySQL DDL cannot run inside RunPython's implicit transaction.
    dependencies = [("surveys", "0002_schema_contract")]
    operations = [
        migrations.AddField(model_name="survey", name="template_key",
                            field=models.CharField(blank=True, max_length=64, null=True)),
        migrations.AddField(model_name="surveyquestion", name="config",
                            field=models.JSONField(blank=True, default=dict)),
        migrations.RunPython(widen_rating, narrow_rating, atomic=False),
    ]
