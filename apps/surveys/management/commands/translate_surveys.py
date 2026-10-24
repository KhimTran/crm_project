from django.core.management.base import BaseCommand

from apps.surveys.models import Survey
from apps.surveys.translator import CACHE_PATH, translate_survey


# tv4: dịch sẵn tiếng Anh cho khảo sát đã có (tiêu đề, câu hỏi, lựa chọn) để Manager xem trang tiếng Anh
class Command(BaseCommand):
    help = "Translate survey text (Vietnamese -> English) into apps/surveys/translations_en.json."

    # tv4: --force dịch lại cả chuỗi đã có bản dịch
    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Re-translate strings that already have a translation.")

    # tv4: duyệt từng khảo sát và báo số chuỗi dịch mới
    def handle(self, *args, **options):
        total = 0
        for survey in Survey.objects.order_by("survey_id"):
            done = translate_survey(survey, force=options["force"])
            total += done
            self.stdout.write(f"Survey {survey.survey_id}: {done} new translation(s)")
        self.stdout.write(self.style.SUCCESS(f"Done: {total} translation(s) in {CACHE_PATH.name}."))
