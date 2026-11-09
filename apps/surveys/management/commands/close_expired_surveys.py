from django.core.management.base import BaseCommand

from apps.surveys.services import close_expired


class Command(BaseCommand):
    help = "Tự động đóng các khảo sát đang phát hành đã quá ngày kết thúc (chạy định kỳ bằng Task Scheduler/cron)."

    # tv4: chạy được độc lập, không cần có người mở trang quản lý
    def handle(self, *args, **options):
        count = close_expired()
        self.stdout.write(self.style.SUCCESS(f"Closed {count} expired survey(s)."))
