"""Versioned questionnaire content; never use display order to identify old answers."""
from copy import deepcopy

TEMPLATE_KEY = "BADMINTON_SHOP_EXPERIENCE_V1"
NOT_USED = "NOT_USED"
SECTIONS = (
    "Phần 1: Phân loại khách hàng & Nhu cầu",
    "Phần 2: Đánh giá Chất lượng Sản phẩm & Dịch vụ",
    "Phần 3: Định hướng Sản phẩm & Góp ý mở",
)

_QUESTIONS = (
    {"key": "purchases", "section": SECTIONS[0], "question_type": "MULTI_CHOICE",
     "question_text": "Hôm nay bạn đã mua sản phẩm hoặc sử dụng dịch vụ nào tại shop?",
     "options": ["Vợt cầu lông.", "Giày cầu lông.", "Quần áo / Balo / Bao vợt.",
                 "Phụ kiện (Ống cầu, quấn cán, vớ, băng bảo vệ...).", "Dịch vụ đan / căng cước vợt."]},
    {"key": "playing_frequency", "section": SECTIONS[0], "question_type": "SINGLE_CHOICE",
     "question_text": "Phong cách hoặc tần suất chơi cầu lông hiện tại của bạn là gì?",
     "options": ["Người mới bắt đầu chơi (Newbie).", "Chơi phong trào, rèn luyện sức khỏe (1–3 buổi/tuần).",
                 "Chơi nâng cao / Đánh giải phong trào (> 3 buổi/tuần).", "Mua làm quà tặng cho người khác."]},
    {"key": "overall_satisfaction", "section": SECTIONS[1], "question_type": "RATING",
     "question_text": "Nhìn chung, bạn hài lòng như thế nào với trải nghiệm tại shop hôm nay?",
     "rating_min": 1, "rating_max": 5},
    {"key": "service_criteria", "section": SECTIONS[1], "question_type": "MATRIX",
     "question_text": "Bạn đánh giá chi tiết các yếu tố sau của shop ở mức độ nào?",
     "options": ["Sản phẩm: Độ đa dạng mẫu mã & cam kết chính hãng.",
                 "Tư vấn: Nhân viên hiểu rõ thông số vợt/giày, tư vấn đúng trình độ và lối đánh (công/thủ).",
                 "Dịch vụ đan vợt: Căng chuẩn số kg, đi dây đẹp, thời gian chờ lấy vợt nhanh.",
                 "Giá cả: Mức giá hợp lý, chương trình khuyến mãi/tích điểm hấp dẫn."]},
    {"key": "highlights", "section": SECTIONS[1], "question_type": "MULTI_CHOICE",
     "question_text": "Điều gì làm bạn ưng ý nhất khi mua đồ tại shop?", "max_selections": 3,
     "options": ["Hàng chuẩn chính hãng.", "Thợ đan vợt mát tay, chuẩn kg.",
                 "Tư vấn nhiệt tình, không chèo kéo.", "Giao hàng nhanh.", "Giá tốt / Tặng kèm phụ kiện xịn."]},
    {"key": "future_brands", "section": SECTIONS[2], "question_type": "MULTI_CHOICE",
     "question_text": "Bạn mong muốn shop nhập thêm nhiều mẫu mới của thương hiệu nào trong thời gian tới?",
     "other_option_index": 5,
     "options": ["Yonex.", "Lining.", "Victor.", "Mizuno.",
                 "Các hãng tầm trung/giá rẻ (Kumpoo, Felet, Vicleo, Kawasaki...).", "Khác."]},
    {"key": "recommendation", "section": SECTIONS[2], "question_type": "RATING",
     "question_text": "Bạn có sẵn sàng giới thiệu shop cho đồng đội hoặc hội nhóm đánh cầu của mình không?",
     "rating_min": 1, "rating_max": 10},
    {"key": "suggestions", "section": SECTIONS[2], "question_type": "TEXT", "is_required": False,
     "question_text": "Bạn có góp ý gì thêm để shop cải thiện dịch vụ phục vụ anh em lông thủ tốt hơn không?",
     "placeholder": "Ví dụ: Cần đan vợt lấy liền nhanh hơn, nhập thêm mẫu giày size lớn, cải thiện khâu đóng gói..."},
)


def question_definitions():
    """Return independent copies suitable for creating a new survey snapshot."""
    return deepcopy(_QUESTIONS)


# Short report labels, aligned with each question's default options. Used only while
# an option still has its default text; an edited option keeps its own wording.
SHORT_LABELS = {
    "purchases": ["Vợt cầu lông", "Giày cầu lông", "Quần áo / Balo", "Phụ kiện", "Đan / căng cước"],
    "playing_frequency": ["Người mới chơi", "Khách chơi phong trào", "Khách chơi nâng cao", "Mua làm quà tặng"],
    "service_criteria": ["Sản phẩm", "Tư vấn", "Dịch vụ đan vợt", "Giá cả"],
    "future_brands": ["Yonex", "Lining", "Victor", "Mizuno", "Hãng tầm trung / giá rẻ", "Khác"],
}
_DEFAULT_OPTIONS = {q["key"]: q.get("options", []) for q in _QUESTIONS}


# tv4: nhãn ngắn của lựa chọn cho báo cáo
def short_label(key, index, text):
    """Report label for option ``index`` (0-based) of question ``key``."""
    defaults, shorts = _DEFAULT_OPTIONS.get(key, []), SHORT_LABELS.get(key, [])
    if index < len(defaults) and index < len(shorts) and text == defaults[index]:
        return shorts[index]
    return text.strip().rstrip(".")
