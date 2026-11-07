"""Explicit initialization for fresh/restored databases or transaction-test fixtures."""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Role


class Command(BaseCommand):
    help = "Create missing standard Roles only; preserve all existing roles and accounts."

    def add_arguments(self, parser):
        parser.add_argument('--database', default='default')

    def handle(self, *args, **options):
        alias = options['database']
        created = 0
        with transaction.atomic(using=alias):
            for code, name in [('ADMIN','Quản trị viên'), ('MANAGER','Quản lý'), ('CUSTOMER','Khách hàng')]:
                _, added = Role.objects.using(alias).get_or_create(role_code=code, defaults={'role_name':name})
                created += added
        self.stdout.write(f"Standard Roles initialized: {created} created; existing rows unchanged.")
