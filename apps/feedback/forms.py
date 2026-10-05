from django import forms

from apps.catalog.models import Product

from .constants import RATING_CHOICES, FeedbackStatus
from .models import Feedback


class FeedbackFilterForm(forms.Form):
    q = forms.CharField(label="Từ khóa", required=False, max_length=100, strip=True)
    status = forms.ChoiceField(label="Trạng thái", required=False,
                               choices=[("", "Tất cả trạng thái"), *FeedbackStatus.choices])
    product = forms.ModelChoiceField(label="Sản phẩm", required=False, queryset=Product.objects.none(),
                                     empty_label="Tất cả sản phẩm")
    rating = forms.TypedChoiceField(label="Số sao", required=False, coerce=int, empty_value=None,
                                    choices=[("", "Tất cả số sao"), *RATING_CHOICES])
    date_from = forms.DateField(label="Từ ngày", required=False,
                                widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    date_to = forms.DateField(label="Đến ngày", required=False,
                              widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))

    # tv4: chỉ liệt kê sản phẩm đã có phản hồi để danh sách chọn gọn
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_ids = Feedback.objects.values("product_id")
        self.fields["product"].queryset = Product.objects.filter(pk__in=product_ids).order_by("product_name")

    # tv4: chặn khoảng ngày ngược (từ ngày sau đến ngày)
    def clean(self):
        cleaned = super().clean()
        date_from, date_to = cleaned.get("date_from"), cleaned.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "Đến ngày phải sau hoặc bằng Từ ngày.")
        return cleaned


class FeedbackHandleForm(forms.Form):
    status = forms.ChoiceField(label="Trạng thái xử lý",
                               choices=[(FeedbackStatus.IN_PROGRESS, FeedbackStatus.IN_PROGRESS.label),
                                        (FeedbackStatus.RESOLVED, FeedbackStatus.RESOLVED.label)])
    manager_note = forms.CharField(label="Trả lời khách hàng", required=False, strip=True,
                                   widget=forms.Textarea(attrs={"rows": 5}))

    # tv4: đánh dấu Đã xử lý thì bắt buộc có câu trả lời cho khách
    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == FeedbackStatus.RESOLVED and not cleaned.get("manager_note"):
            self.add_error("manager_note", "Cần nhập câu trả lời trước khi đánh dấu Đã xử lý.")
        return cleaned
