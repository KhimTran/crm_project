from django.db import migrations, models


def convert_pending(apps, schema_editor):
    feedback = apps.get_model('feedback', 'Feedback').objects.using(schema_editor.connection.alias)
    feedback.filter(status='IN_PROGRESS').update(status='NEW', resolved_at=None)


class Migration(migrations.Migration):
    dependencies = [('feedback', '0002_alter_feedback_customer_alter_feedback_handled_by')]
    operations = [
        migrations.RunPython(convert_pending, migrations.RunPython.noop),
        migrations.AlterField(model_name='feedback', name='status', field=models.CharField(max_length=20, default='NEW', choices=[('NEW','Mới'),('RESOLVED','Đã xử lý')])),
        migrations.AddConstraint(model_name='feedback', constraint=models.CheckConstraint(condition=models.Q(status__in=['NEW','RESOLVED']), name='chk_feedbacks_status')),
    ]
