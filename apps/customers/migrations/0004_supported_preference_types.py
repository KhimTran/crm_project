"""Replace the retired-type exclusion with the supported preference vocabulary."""
from django.db import migrations, models


def validate_existing_types(apps, schema_editor):
    Preference = apps.get_model('customers', 'CustomerPreference')
    if Preference.objects.using(schema_editor.connection.alias).exclude(
        preference_type__in=('BRAND', 'CATEGORY', 'FAVORITE_BRAND', 'FAVORITE_BRAND_OTHER')
    ).exists():
        raise RuntimeError('Unsupported preference types exist; inspect them before changing the constraint. No preference data was deleted.')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('customers', '0003_remove_play_style')]
    operations = [
        migrations.RunPython(validate_existing_types, migrations.RunPython.noop),
        migrations.RemoveConstraint('customerpreference', 'chk_preferences_no_play_style'),
        migrations.AddConstraint('customerpreference', models.CheckConstraint(
            condition=models.Q(preference_type__in=('BRAND', 'CATEGORY', 'FAVORITE_BRAND', 'FAVORITE_BRAND_OTHER')),
            name='chk_customer_preferences_type')),
    ]
