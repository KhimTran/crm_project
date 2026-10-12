from django import forms

from apps.catalog.models import Brand, Category, Status


class ProductFilterForm(forms.Form):
    q = forms.CharField(label="Tên sản phẩm", required=False, max_length=200)
    category = forms.ModelChoiceField(label="Danh mục", required=False, queryset=Category.objects.filter(status=Status.ACTIVE).order_by("category_name"))
    brand = forms.ModelChoiceField(label="Thương hiệu", required=False, queryset=Brand.objects.filter(status=Status.ACTIVE).order_by("brand_name"))
    min_price = forms.DecimalField(label="Giá từ", required=False, min_value=0, max_digits=12, decimal_places=2)
    max_price = forms.DecimalField(label="Giá đến", required=False, min_value=0, max_digits=12, decimal_places=2)

    def clean(self):
        data = super().clean()
        if data.get("min_price") is not None and data.get("max_price") is not None and data["min_price"] > data["max_price"]:
            self.add_error("max_price", "Giá đến phải lớn hơn hoặc bằng giá từ.")
        return data
