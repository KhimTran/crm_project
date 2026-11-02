"""Repair SQL imports whose recorded 0003 migration still has the legacy CHECK."""
from django.db import migrations


def reconcile_rating_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'mysql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS '
                       'WHERE CONSTRAINT_SCHEMA=DATABASE() AND TABLE_NAME=%s AND CONSTRAINT_TYPE=%s',
                       ['survey_answers', 'CHECK'])
        names = {row[0] for row in cursor.fetchall()}
        if 'chk_survey_answers_rating_1_10' not in names:
            cursor.execute('ALTER TABLE survey_answers ADD CONSTRAINT chk_survey_answers_rating_1_10 '
                           'CHECK (rating_value IS NULL OR rating_value BETWEEN 1 AND 10)')
        if 'chk_survey_answers_rating' in names:
            cursor.execute('ALTER TABLE survey_answers DROP CHECK chk_survey_answers_rating')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('surveys', '0005_alter_surveyrecipient_customer')]
    operations = [migrations.RunPython(reconcile_rating_constraint, migrations.RunPython.noop, atomic=False)]
