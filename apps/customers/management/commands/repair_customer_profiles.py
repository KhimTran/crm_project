from django.core.management.base import BaseCommand
from django.db import models
from django.db import connections, transaction

from apps.accounts.constants import AccountRole
from apps.accounts.models import Account
from apps.customers.provisioning import ensure_customer_profile


class Command(BaseCommand):
    help = "Preview missing CUSTOMER profiles; use --apply to create them without changing existing data."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Create the missing profiles.")
        parser.add_argument("--account-id", type=int, action="append", help="Limit to these account IDs (repeatable).")

    def handle(self, *args, **options):
        # Legacy CRM employees may have role CUSTOMER plus a staff group.
        accounts = Account.objects.filter(role=AccountRole.CUSTOMER).filter(
            models.Q(full_name__isnull=True) | models.Q(full_name="")
        ).exclude(
            groups__name__in=("CRM_MANAGER", "CUSTOMER_SERVICE"),
        ).order_by("account_id")
        if options["account_id"]:
            accounts = accounts.filter(pk__in=options["account_id"])
        ids = list(accounts.values_list("pk", flat=True))
        self.stdout.write(f"Database: {connections[accounts.db].settings_dict['NAME']}")
        self.stdout.write(f"Missing profiles: {len(ids)}; account IDs: {', '.join(map(str, ids)) or '(none)'}")
        created = 0
        if options["apply"]:
            for account_id in ids:
                with transaction.atomic():
                    # Recheck eligibility while holding the account lock.
                    account = Account.objects.select_for_update().get(pk=account_id)
                    if (account.role != AccountRole.CUSTOMER
                            or account.groups.filter(name__in=("CRM_MANAGER", "CUSTOMER_SERVICE")).exists()):
                        continue
                    _, was_created = ensure_customer_profile(account.pk)
                    created += int(was_created)
            self.stdout.write(self.style.SUCCESS(f"Created profiles: {created}. Existing profiles and passwords unchanged."))
        else:
            self.stdout.write("Preview only. Re-run with --apply after reviewing the account IDs and database settings.")
