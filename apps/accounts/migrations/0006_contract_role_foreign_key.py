from django.db import migrations, models


def restore_codes(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    Role = apps.get_model('accounts', 'Role')
    alias = schema_editor.connection.alias
    for role in Role.objects.using(alias).all():
        Account.objects.using(alias).filter(role_link_id=role.pk).update(
            role=role.role_code, updated_at=models.F('updated_at'))


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('accounts', '0005_expand_role_foreign_key')]
    operations = [
        migrations.RemoveConstraint('account', 'chk_accounts_role'),
        migrations.RunPython(migrations.RunPython.noop, restore_codes),
        migrations.RemoveField('account', 'role'),
        migrations.RenameField('account', 'role_link', 'role'),
    ]
