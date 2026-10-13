"""Chữ tiếng Anh cho màn hình khách hàng/phản hồi/báo cáo khi Admin mở trong Admin Portal.

Quản lý CRM/CSKH vẫn thấy tiếng Việt như cũ. View bọc bằng @portal_english: nếu người dùng là Admin thì chạy
trong translation.override("en"), nhờ đó lỗi mặc định của Django cũng sang tiếng Anh; chữ riêng của TV4 tra trong EN.
"""

from functools import wraps

from django.utils import translation

from apps.accounts.constants import AccountRole

PORTAL_LANGUAGE = "en"

# Chữ tiếng Việt (nhãn choices, form, lỗi, dữ liệu sở thích cố định) → tiếng Anh
EN = {
    # Trạng thái / nhãn choices
    "Hoạt động": "Active", "Đã khóa": "Locked", "Đang hoạt động": "Active", "Đã xóa": "Deleted",
    "Nam": "Male", "Nữ": "Female", "Khác": "Other",
    "Mới chơi": "Beginner", "Phong trào": "Recreational", "Thi đấu": "Competitive",
    "Lối chơi": "Play Style", "Thương hiệu": "Brand", "Nhóm sản phẩm": "Product Category",
    "Tấn công": "Attacking", "Phòng thủ": "Defensive", "Toàn diện": "All-round",
    "Đánh đơn": "Singles", "Đánh đôi": "Doubles",
    "Mới": "New", "Đang xử lý": "In Progress", "Đã xử lý": "Resolved",
    "1 sao": "1 star", "2 sao": "2 stars", "3 sao": "3 stars", "4 sao": "4 stars", "5 sao": "5 stars",
    "Dưới 18": "Under 18", "Từ 55": "55+", "Chưa khai báo": "Not specified",
    # Nhãn form
    "Họ tên": "Full Name", "Số điện thoại": "Phone", "Ngày sinh": "Date of Birth", "Giới tính": "Gender",
    "Địa chỉ": "Address", "Trình độ chơi": "Playing Level", "Thương hiệu yêu thích": "Favorite Brands",
    "-- Chọn --": "-- Select --", "Lý do khóa": "Lock Reason", "Từ khóa": "Keyword", "Tên, SĐT, email": "Name, phone, email",
    "Nhóm tuổi": "Age Group", "Trình độ": "Playing Level", "Tài khoản": "Account", "Tất cả": "All",
    "Trạng thái": "Status", "Tất cả trạng thái": "All statuses", "Sản phẩm": "Product",
    "Tất cả sản phẩm": "All products", "Số sao": "Rating", "Tất cả số sao": "All ratings",
    "Từ ngày": "From", "Đến ngày": "To", "Trạng thái xử lý": "Handling Status",
    "Trả lời khách hàng": "Reply to Customer",
    # Lỗi form / service
    "Email đã được sử dụng.": "This email is already in use.",
    "Email đã được sử dụng": "This email is already in use.",
    "Số điện thoại không hợp lệ (ví dụ 0901234567).": "Invalid phone number (e.g. 0901234567).",
    "Số điện thoại đã được sử dụng.": "This phone number is already in use.",
    "Số điện thoại đã được sử dụng": "This phone number is already in use.",
    "Ngày sinh không hợp lệ.": "Invalid date of birth.",
    "Đến ngày phải sau hoặc bằng Từ ngày.": "The To date must be on or after the From date.",
    "Cần nhập câu trả lời trước khi đánh dấu Đã xử lý.": "A reply is required before marking as Resolved.",
    "Cần nhập câu trả lời trước khi đánh dấu Đã xử lý": "A reply is required before marking as Resolved.",
    "Trạng thái xử lý không hợp lệ": "Invalid handling status.",
    "Không tìm thấy khách hàng": "Customer not found.",
    "Khách hàng đã bị xóa": "This customer has been deleted.",
    "Tài khoản khách hàng đã bị khóa": "This customer account is already locked.",
    "Tài khoản khách hàng đang hoạt động": "This customer account is already active.",
    "Không tìm thấy phản hồi": "Feedback not found.",
}


# tv4: tài khoản Admin xem màn hình TV4 trong Admin Portal (bằng tiếng Anh)
def is_portal_user(user):
    return getattr(user, "is_authenticated", False) and getattr(user, "role", None) == AccountRole.ADMIN


# tv4: đang hiển thị tiếng Anh cho Admin Portal không
def is_english():
    return translation.get_language() == PORTAL_LANGUAGE


# tv4: dịch một chuỗi tiếng Việt sang tiếng Anh khi đang ở Admin Portal; không có trong EN thì giữ nguyên
def tr(text):
    if not is_english() or not isinstance(text, str):
        return text
    return EN.get(text, text)


# tv4: chọn câu tiếng Việt hoặc tiếng Anh (dùng cho thông báo có chèn dữ liệu)
def say(vi, en):
    return en if is_english() else vi


# tv4: decorator cho view TV4: Admin thì chạy view trong ngữ cảnh tiếng Anh
def portal_english(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if is_portal_user(request.user):
            with translation.override(PORTAL_LANGUAGE):
                return view(request, *args, **kwargs)
        return view(request, *args, **kwargs)
    return wrapped


# tv4: dịch nhãn, lựa chọn, placeholder của form khi đang ở Admin Portal
def localize_form(form):
    if not is_english():
        return form
    for field in form.fields.values():
        field.label = tr(field.label)
        if getattr(field, "empty_label", None):
            field.empty_label = tr(field.empty_label)
        if hasattr(field, "choices") and not hasattr(field, "queryset"):
            field.choices = [(value, tr(label)) for value, label in field.choices]
        placeholder = field.widget.attrs.get("placeholder")
        if placeholder:
            field.widget.attrs["placeholder"] = tr(placeholder)
    return form


# tv4: dịch nhãn các dòng báo cáo [{label, ...}] khi đang ở Admin Portal
def localize_rows(rows):
    return [{**row, "label": tr(row["label"])} for row in rows]
