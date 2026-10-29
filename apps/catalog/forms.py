from django import forms
from django.db.models import Q
from .models import Brand, Category, Product, Status
from .money import MoneyField
from .vocabulary import brand_aliases, canonical_brand, canonical_product_name


class ProductForm(forms.ModelForm):
    price = MoneyField(max_digits=12, decimal_places=2)

    class Meta:
        model = Product
        fields = ("category", "brand", "product_name", "description", "image_url", "price", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, model in (("category", Category), ("brand", Brand)):
            active = Q(status=Status.ACTIVE)
            if self.instance.pk:
                # Khi sửa, vẫn giữ mục hiện tại dù nó đã INACTIVE để không mất dữ liệu
                active |= Q(pk=getattr(self.instance, f"{field_name}_id"))
            self.fields[field_name].queryset = model.objects.filter(active).order_by(
                {"category": "category_name", "brand": "brand_name"}[field_name]
            )
            self.fields[field_name].empty_label = "-- Select --"

    def clean_product_name(self):
        name = self.cleaned_data["product_name"].strip()
        if not name:
            raise forms.ValidationError("Tên sản phẩm không được để trống.")
        brand = self.cleaned_data.get("brand")
        return canonical_product_name(name) if brand and canonical_brand(brand.brand_name) == "Li-Ning" else name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Giá phải lớn hơn 0.")
        return price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("category_name", "description", "status")
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def clean_category_name(self):
        name = self.cleaned_data["category_name"].strip()
        duplicates = Category.objects.filter(category_name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Tên danh mục đã tồn tại.")
        return name


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ("brand_name", "description", "status")

    def clean_brand_name(self):
        name = canonical_brand(self.cleaned_data["brand_name"])
        duplicates = Brand.objects.filter(brand_name__in=brand_aliases(name))
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Tên thương hiệu đã tồn tại.")
        return name


class BrandPreferenceMultipleChoiceField(forms.MultipleChoiceField):
    """Accept an old brand token only when its canonical choice is available."""
    def to_python(self, value):
        choices = dict(self.choices)
        return [canonical_brand(item) if canonical_brand(item) in choices else item
                for item in super().to_python(value)]
