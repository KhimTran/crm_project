from types import SimpleNamespace

from django.test import RequestFactory, SimpleTestCase

from apps.accounts.constants import AccountRole
from apps.customers.portal_text import SESSION_KEY, chosen_language, set_portal_language


# tv4: nút đổi ngôn ngữ EN/VI của Admin/Manager ở phần Khảo sát và Phản hồi
class PortalLanguageTests(SimpleTestCase):
    # tv4: tạo request POST với user và session giả
    def post(self, role, **data):
        request = RequestFactory().post("/portal-language/", data)
        request.user = SimpleNamespace(is_authenticated=True, role=role)
        request.session = {}
        return request, set_portal_language(request)

    # tv4: Manager chọn VI thì lưu vào session và quay lại trang cũ
    def test_manager_choice_is_saved_and_redirects_back(self):
        request, response = self.post(AccountRole.MANAGER, lang="vi", next="/surveys/manage/")
        self.assertEqual(request.session[SESSION_KEY], "vi")
        self.assertEqual((response.status_code, response["Location"]), (302, "/surveys/manage/"))
        self.assertEqual(chosen_language(request), "vi")

    # tv4: ngôn ngữ lạ bị bỏ qua, mặc định là tiếng Anh
    def test_invalid_language_is_ignored(self):
        request, _ = self.post(AccountRole.MANAGER, lang="fr")
        self.assertNotIn(SESSION_KEY, request.session)
        self.assertEqual(chosen_language(request), "en")

    # tv4: next trỏ ra ngoài site thì quay về trang chủ (không open redirect)
    def test_external_next_is_rejected(self):
        _, response = self.post(AccountRole.ADMIN, lang="en", next="https://evil.example/x")
        self.assertEqual(response["Location"], "/")

    # tv4: khách hàng không được dùng nút này
    def test_customer_is_forbidden(self):
        _, response = self.post(AccountRole.CUSTOMER, lang="vi")
        self.assertEqual(response.status_code, 403)
