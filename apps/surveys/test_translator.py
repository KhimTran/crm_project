import json
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase
from django.utils import translation

from apps.customers.portal_text import tr
from apps.surveys import translator


# tv4: bản dịch khảo sát: tra file, dịch dự phòng khi lỗi mạng, không ảnh hưởng tiếng Việt của khách hàng
class TranslatorTests(SimpleTestCase):
    # tv4: dùng file bản dịch tạm thay cho file thật
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()) / "translations_en.json"
        patcher = mock.patch.object(translator, "CACHE_PATH", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        translator._cache.update(mtime=None, data={})
        translator._failed.clear()

    # tv4: tr() chỉ dịch ở Admin Portal (tiếng Anh) và giữ nguyên tiếng Việt cho khách
    def test_tr_uses_cached_translation_only_in_english(self):
        self.tmp.write_text(json.dumps({"Bạn thích hãng nào?": "Which brand do you like?"}), encoding="utf-8")
        with translation.override("en"):
            self.assertEqual(tr("Bạn thích hãng nào?"), "Which brand do you like?")
            self.assertEqual(tr("Chưa dịch"), "Chưa dịch")
        with translation.override("vi"):
            self.assertEqual(tr("Bạn thích hãng nào?"), "Bạn thích hãng nào?")

    # tv4: chuỗi đã có không bị dịch lại; chuỗi mới được lưu vào file
    def test_ensure_translations_skips_existing_and_saves_new(self):
        self.tmp.write_text(json.dumps({"Giá": "Price"}), encoding="utf-8")
        with mock.patch.object(translator, "translate_one", return_value="Shoes") as fake:
            self.assertEqual(translator.ensure_translations(["Giá", "Giày", "  "]), 1)
        fake.assert_called_once_with("Giày")
        self.assertEqual(translator.lookup("Giày"), "Shoes")
        self.assertEqual(translator.lookup("Giá"), "Price")

    # tv4: mọi dịch vụ lỗi thì trả None, không ném lỗi và không ghi file
    def test_network_failure_is_ignored(self):
        failing = mock.Mock()
        failing.translate.side_effect = translator.TooManyRequests()
        with mock.patch.object(translator, "GoogleTranslator", return_value=failing), \
                mock.patch.object(translator, "MyMemoryTranslator", return_value=failing):
            self.assertEqual(translator.ensure_translations(["Giày"]), 0)
        self.assertFalse(self.tmp.exists())

    # tv4: từ lóng "căng cước" được đổi trước khi gửi cho dịch vụ dịch
    def test_glossary_applied_before_translating(self):
        ok = mock.Mock()
        ok.translate.return_value = "Stringing"
        with mock.patch.object(translator, "GoogleTranslator", return_value=ok):
            self.assertEqual(translator.translate_one("Dịch vụ căng cước"), "Stringing")
        ok.translate.assert_called_once_with("Dịch vụ căng dây")

    # tv4: dịch vụ không trả lời thì bị ngắt sau thời gian chờ, không treo lệnh / nút Lưu
    def test_slow_provider_times_out(self):
        import time
        with self.assertRaises(TimeoutError):
            translator._call_with_timeout(lambda _: time.sleep(2), "x", timeout=0.1)
        self.assertEqual(translator._call_with_timeout(str.upper, "ok"), "OK")
