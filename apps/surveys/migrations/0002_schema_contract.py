"""Apply MySQL-specific constraints after all initial deferred foreign keys exist."""

from importlib import import_module

from django.db import migrations


align_mysql_schema = import_module("apps.surveys.migrations.0001_initial").align_mysql_schema


class Migration(migrations.Migration):
    dependencies = [
        ("surveys", "0001_initial"),
        ("feedback", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [migrations.RunPython(align_mysql_schema, migrations.RunPython.noop)]
