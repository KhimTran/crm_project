import re
from django import forms
from django.db.models import Q
from .models import Brand, Category, Product, Status, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("supplier_code", "supplier_name", "address", "phone", "email", "status")

    def clean_supplier_code(self):
        code = self.cleaned_data["supplier_code"].strip()
        duplicates = Supplier.objects.filter(supplier_code__iexact=code)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Mã nhà cung cấp đã tồn tại.")
        return code

    def clean_supplier_name(self):
        name = self.cleaned_data["supplier_name"].strip()
        if not name:
            raise forms.ValidationError("Tên nhà cung cấp không được để trống.")
        return name

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            return None
        digits = len(re.findall(r"[0-9]", phone))
        if not re.fullmatch(r"\+?[0-9\-\s().]+", phone) or not 9 <= digits <= 15:
            raise forms.ValidationError(
                "Số điện thoại phải có 9–15 chữ số; dấu + chỉ được ở đầu. "
                "Có thể dùng khoảng trắng, dấu gạch, dấu chấm hoặc ngoặc."
            )
        return phone


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "brand", "supplier", "product_name", "description", "price", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, model in (("category", Category), ("brand", Brand), ("supplier", Supplier)):
            active = Q(status=Status.ACTIVE)
            if self.instance.pk:
                # Khi sửa, vẫn giữ mục hiện tại dù nó đã INACTIVE để không mất dữ liệu
                active |= Q(pk=getattr(self.instance, f"{field_name}_id"))
            self.fields[field_name].queryset = model.objects.filter(active).order_by(
                {"category": "category_name", "brand": "brand_name", "supplier": "supplier_name"}[field_name]
            )
            self.fields[field_name].empty_label = "-- Chọn --"

    def clean_product_name(self):
        name = self.cleaned_data["product_name"].strip()
        if not name:
            raise forms.ValidationError("Tên sản phẩm không được để trống.")
        return name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Giá phải lớn hơn 0.")
        return price


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("category_name", "description", "status")

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
        name = self.cleaned_data["brand_name"].strip()
        duplicates = Brand.objects.filter(brand_name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("Tên thương hiệu đã tồn tại.")
        return name
