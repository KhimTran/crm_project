from django.db import migrations, models
import django.db.models.deletion


def backfill(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    Role = apps.get_model('accounts', 'Role')
    alias = schema_editor.connection.alias
    accounts = Account.objects.using(alias)
    roles = Role.objects.using(alias)
    codes = {'ADMIN': 'Quản trị viên', 'MANAGER': 'Quản lý', 'CUSTOMER': 'Khách hàng'}
    if accounts.exclude(role__in=codes).exists() or roles.exclude(role_code__in=codes).exists():
        raise RuntimeError('Invalid role data; migration stopped before backfill')
    for code, name in codes.items():
        role, _ = roles.get_or_create(role_code=code, defaults={'role_name': name})
        roles.filter(pk=role.pk).update(role_name=name)
        # Imported MySQL schemas may have ON UPDATE CURRENT_TIMESTAMP.
        accounts.filter(role=code).update(role_link_id=role.pk, updated_at=models.F('updated_at'))
    if accounts.filter(role_link__isnull=True).exists():
        raise RuntimeError('Unmapped account roles')
    if accounts.exclude(role=models.F('role_link__role_code')).exists():
        raise RuntimeError('Account role mapping differs')


class Migration(migrations.Migration):
    atomic = False
    dependencies = [('accounts', '0004_remove_staff_account_account_address_and_more')]
    operations = [
        migrations.AddField('account', 'role_link', models.ForeignKey(
            to='accounts.role', db_column='role_id', null=True, db_constraint=False,
            on_delete=django.db.models.deletion.PROTECT)),
        migrations.RunPython(backfill, migrations.RunPython.noop),
        migrations.AlterField('account', 'role_link', models.ForeignKey(
            to='accounts.role', db_column='role_id', on_delete=django.db.models.deletion.PROTECT)),
    ]
