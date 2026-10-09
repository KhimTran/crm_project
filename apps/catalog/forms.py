import re
from django import forms
from .models import Brand, Category, Product, Supplier


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
        if phone and not re.fullmatch(r"[0-9+\-\s().]{8,20}", phone):
            raise forms.ValidationError("Số điện thoại không hợp lệ (8-20 ký tự số, + - . ( ) hoặc khoảng trắng).")
        return phone or None


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "brand", "supplier", "product_name", "description", "price", "status")

    def clean_supplier(self):
        supplier = self.cleaned_data["supplier"]
        if supplier.status != "ACTIVE":
            raise forms.ValidationError("Nhà cung cấp phải đang hoạt động.")
        return supplier


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