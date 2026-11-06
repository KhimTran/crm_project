from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0006_contract_role_foreign_key')]
    operations = [
        migrations.AlterField('role', 'role_code', models.CharField(max_length=20)),
    ]
