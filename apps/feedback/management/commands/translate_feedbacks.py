from django.core.management.base import BaseCommand

from apps.feedback.models import Feedback
from apps.surveys.translator import CACHE_PATH, ensure_translations


# tv4: dịch sẵn tiếng Anh cho nội dung phản hồi của khách để Manager xem ở chế độ EN
class Command(BaseCommand):
    help = "Translate feedback content (Vietnamese -> English) into apps/surveys/translations_en.json."

    # tv4: --force dịch lại cả chuỗi đã có bản dịch
    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-translate strings that already have a translation.")

    # tv4: dịch toàn bộ nội dung phản hồi chưa có bản dịch
    def handle(self, *args, **options):
        texts = Feedback.objects.exclude(content__isnull=True).values_list("content", flat=True)
        done = ensure_translations(list(texts), force=options["force"])
        self.stdout.write(self.style.SUCCESS(f"Done: {done} translation(s) in {CACHE_PATH.name}."))
