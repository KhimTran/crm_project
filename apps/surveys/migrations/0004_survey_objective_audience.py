"""Owner-approved on 2026-10-18: survey objective and the audience saved with a draft."""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("surveys", "0003_questionnaire_configuration")]
    operations = [
        migrations.AddField(model_name="survey", name="objective",
                            field=models.CharField(blank=True, max_length=30, null=True)),
        migrations.AddField(model_name="survey", name="audience",
                            field=models.JSONField(blank=True, default=dict)),
    ]
