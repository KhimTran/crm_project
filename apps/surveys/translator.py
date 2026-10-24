"""Bản dịch tiếng Anh cho nội dung khảo sát do Manager nhập (lưu tiếng Việt, khách hàng đọc tiếng Việt).

Không thêm cột vào CSDL: bản dịch nằm trong `translations_en.json` (Việt -> Anh, có thể sửa tay và commit).
`lookup` chỉ đọc file nên view không bao giờ gọi mạng; việc dịch chỉ diễn ra khi lưu khảo sát hoặc chạy
`manage.py translate_surveys`, và lỗi mạng chỉ làm bỏ qua bản dịch (trang vẫn hiện tiếng Việt).
"""
import json
import logging
import os
import re
import tempfile
import threading
from pathlib import Path

from deep_translator import GoogleTranslator, MyMemoryTranslator
from deep_translator.exceptions import BaseError, RequestError, ServerException, TooManyRequests
from requests import RequestException

logger = logging.getLogger(__name__)

CACHE_PATH = Path(__file__).with_name("translations_en.json")
_lock = threading.Lock()
_cache = {"mtime": None, "data": {}}
TIMEOUT_SECONDS = 10  # tv4: thời gian chờ tối đa cho một lần gọi dịch vụ dịch
_failed = set()  # tv4: dịch vụ đã lỗi trong tiến trình này (vd Google chặn IP) thì không thử lại, tránh chờ vô ích

# tv4: tiếng lóng cầu lông mà máy dịch hiểu sai ("căng cước" -> "freight"), đổi sang cách nói phổ thông trước khi dịch
GLOSSARY = (
    (re.compile(r"căng cước", re.I), "căng dây"),
    (re.compile(r"đan vợt", re.I), "căng dây vợt"),
    (re.compile(r"lông thủ", re.I), "người chơi cầu lông"),
)


# tv4: đọc file bản dịch; chỉ đọc lại khi file đổi (mtime) nên gọi nhiều lần vẫn rẻ
def _load():
    try:
        mtime = CACHE_PATH.stat().st_mtime
    except OSError:
        return {}
    if _cache["mtime"] != mtime:
        with _lock:
            try:
                _cache["data"] = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                logger.warning("Cannot read %s; ignoring cached translations.", CACHE_PATH.name)
                _cache["data"] = {}
            _cache["mtime"] = mtime
    return _cache["data"]


# tv4: ghi file bản dịch an toàn (file tạm rồi thay thế) để lỗi giữa chừng không làm hỏng file cũ
def _save(data):
    with _lock:
        fd, tmp = tempfile.mkstemp(dir=CACHE_PATH.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, CACHE_PATH)
        _cache["mtime"] = None


# tv4: bản dịch tiếng Anh đã lưu của một chuỗi tiếng Việt (None nếu chưa có); không bao giờ gọi mạng
def lookup(text):
    return _load().get(text.strip()) if isinstance(text, str) else None


# tv4: deep-translator gọi requests không có timeout nên có thể treo mãi; chạy ở luồng nền và chỉ chờ tối đa `timeout` giây
def _call_with_timeout(func, arg, timeout=TIMEOUT_SECONDS):
    box = {}

    def run():
        try:
            box["result"] = func(arg)
        except Exception as exc:  # chuyển lỗi về luồng gọi để xử lý như lỗi dịch bình thường
            box["error"] = exc

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise TimeoutError(f"no answer after {timeout}s")
    if "error" in box:
        raise box["error"]
    return box.get("result")


# tv4: dịch một chuỗi Việt -> Anh bằng deep-translator (Google, lỗi thì MyMemory); None nếu cả hai đều lỗi
def translate_one(text):
    prepared = text
    for pattern, replacement in GLOSSARY:
        prepared = pattern.sub(replacement, prepared)
    for provider in (GoogleTranslator(source="vi", target="en"), MyMemoryTranslator(source="vi-VN", target="en-GB")):
        if type(provider) in _failed:
            continue
        try:
            result = _call_with_timeout(provider.translate, prepared)
        except (BaseError, RequestError, ServerException, TooManyRequests, RequestException, TimeoutError) as exc:
            logger.warning("%s failed: %s", type(provider).__name__, type(exc).__name__)
            _failed.add(type(provider))
            continue
        if result and result.strip():
            return result.strip()
    return None


# tv4: dịch những chuỗi chưa có trong file rồi ghi lại; trả về số chuỗi dịch được (force=True dịch lại cả chuỗi đã có)
def ensure_translations(texts, *, force=False):
    data = dict(_load())
    done = 0
    for text in sorted({t.strip() for t in texts if isinstance(t, str) and t.strip()}):
        if text in data and not force:
            continue
        translated = translate_one(text)
        if translated:
            data[text] = translated
            done += 1
    if done:
        _save(data)
    return done


# tv4: dịch ở luồng nền để người dùng không phải chờ dịch vụ dịch (dùng khi khách gửi phản hồi)
def translate_in_background(texts):
    threading.Thread(target=ensure_translations, args=(list(texts),), daemon=True).start()


# tv4: mọi chuỗi hiển thị của một khảo sát: tiêu đề, mô tả, câu hỏi, lựa chọn, nhãn thang điểm
def survey_texts(survey):
    from .models import SurveyOption, SurveyQuestion
    texts = [survey.title, survey.description]
    for question in SurveyQuestion.objects.filter(survey=survey):
        texts.append(question.question_text)
        config = question.config or {}
        texts.extend(config.get(key) for key in ("rating_min_label", "rating_max_label", "placeholder"))
    texts.extend(SurveyOption.objects.filter(question__survey=survey).values_list("option_text", flat=True))
    return [t for t in texts if t]


# tv4: dịch toàn bộ chữ của khảo sát (bỏ qua chuỗi đã có trong từ điển bộ 8 câu)
def translate_survey(survey, *, force=False):
    from .questionnaire import EN_TEXT
    return ensure_translations([t for t in survey_texts(survey) if t not in EN_TEXT], force=force)
