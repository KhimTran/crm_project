from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .constants import MANAGER_GROUP, SurveyStatus
from .models import Survey

PW = "StrongPass!2026"


# tv4: màn hình quản lý khảo sát hiển thị trong Admin Portal (tiếng Anh) khi Admin mở
class SurveyAdminPortalTests(TestCase):
    # tv4: admin đăng nhập sẵn và một khảo sát Nháp chưa có câu hỏi
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin@example.test", PW)
        self.survey = Survey.objects.create(title="Khảo sát vợt", status=SurveyStatus.DRAFT, created_by=self.admin,
                                            start_at=timezone.now(), end_at=timezone.now() + timedelta(days=7))
        self.client.force_login(self.admin)

    # tv4: admin mở các trang quản lý khảo sát trong khung Admin Portal, nội dung tiếng Anh
    def test_admin_sees_survey_pages_in_admin_portal_english(self):
        sid = self.survey.pk
        for url, text in ((reverse("surveys:manage_list"), "Create Survey"),
                          (reverse("surveys:manage_create"), "Opens At"),
                          (reverse("surveys:manage_detail", args=[sid]), "Send Survey"),
                          (reverse("surveys:manage_send", args=[sid]), "The survey has no questions yet."),
                          (reverse("surveys:manage_stats", args=[sid]), "Response Rate"),
                          (reverse("surveys:question_add", args=[sid]), "Question Type")):
            response = self.client.get(url)
            self.assertTemplateUsed(response, "admin/portal/base.html")
            self.assertContains(response, text, msg_prefix=url)

    # tv4: lỗi form và thông báo cũng sang tiếng Anh
    def test_form_errors_and_messages_are_english(self):
        response = self.client.post(reverse("surveys:manage_create"), {
            "title": "X", "start_at": "2026-10-10T10:00", "end_at": "2026-10-09T10:00"})
        self.assertContains(response, "The closing time must be after the opening time.")

        response = self.client.post(reverse("surveys:question_add", args=[self.survey.pk]), {
            "question_text": "Q", "question_type": "SINGLE_CHOICE", "options_text": "A"})
        self.assertContains(response, "Enter at least 2 different options.")

        response = self.client.post(reverse("surveys:manage_delete", args=[self.survey.pk]), follow=True)
        self.assertContains(response, "Survey deleted.")

    # tv4: Quản lý CRM vẫn thấy khung CRM tiếng Việt
    def test_crm_manager_keeps_vietnamese_crm_layout(self):
        manager = get_user_model().objects.create_user("manager@example.test", PW)
        manager.groups.add(Group.objects.get_or_create(name=MANAGER_GROUP)[0])
        self.client.force_login(manager)
        response = self.client.get(reverse("surveys:manage_list"))
        self.assertTemplateUsed(response, "layouts/base_crm.html")
        self.assertContains(response, "+ Tạo khảo sát")
        self.assertNotContains(response, "Create Survey")
