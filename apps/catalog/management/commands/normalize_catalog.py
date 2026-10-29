from django.core.management.base import BaseCommand
from apps.catalog.normalization import normalize_catalog


class Command(BaseCommand):
    help = "Preview Li-Ning normalization; use --apply after verifying an operational backup."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="Apply the previewed repair atomically.")

    def handle(self, *args, **options):
        counts = normalize_catalog(apply=options["apply"])
        mode = "Applied" if options["apply"] else "Preview (no writes)"
        self.stdout.write(f"{mode}: " + ", ".join(f"{key}={value}" for key, value in counts.items()))
