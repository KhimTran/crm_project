"""Owner-authorized removal; verified backup is required before applying."""
from django.db import migrations, models, transaction


def remove_play_style(apps, schema_editor):
    alias = schema_editor.connection.alias
    Preference = apps.get_model('customers', 'CustomerPreference')
    Survey = apps.get_model('surveys', 'Survey')
    retired = {'Tấn công', 'Phòng thủ', 'Toàn diện', 'Đánh đơn', 'Đánh đôi'}
    retired.update(Preference.objects.using(alias).filter(preference_type='PLAY_STYLE').values_list('preference_value', flat=True))
    with transaction.atomic(using=alias):
        for survey in Survey.objects.using(alias).all():
            audience = survey.audience or {}
            selected = audience.get('preferences') or []
            if not retired.intersection(selected):
                continue
            if audience.get('audience') == 'filter':
                raise RuntimeError(f'Survey {survey.pk} still uses a retired style segment. Freeze its matching customers as a specific audience before applying this migration.')
            audience['preferences'] = [value for value in selected if value not in retired]
            Survey.objects.using(alias).filter(pk=survey.pk).update(audience=audience)
        Preference.objects.using(alias).filter(preference_type='PLAY_STYLE').delete()


class Migration(migrations.Migration):
    atomic = False  # MySQL CHECK DDL commits independently of the data cleanup.
    dependencies = [
        ('customers', '0002_alter_customerpreference_customer_delete_customer_and_more'),
        ('surveys', '0005_alter_surveyrecipient_customer'),
    ]
    operations = [
        migrations.RunPython(remove_play_style),
        migrations.AddConstraint('customerpreference', models.CheckConstraint(
            condition=~models.Q(preference_type='PLAY_STYLE'), name='chk_preferences_no_play_style')),
    ]
