from django import forms
from .models import Product, Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ("supplier_code", "supplier_name", "address", "phone", "email", "status")


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "brand", "supplier", "product_name", "description", "price", "status")

    def clean_supplier(self):
        supplier = self.cleaned_data["supplier"]
        if supplier.status != "ACTIVE":
            raise forms.ValidationError("Nhà cung cấp phải đang hoạt động.")
        return supplier
