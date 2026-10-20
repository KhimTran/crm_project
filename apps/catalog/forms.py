from django import forms
from django.db.models import Q
from .models import Brand, Category, Product, Status


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("category", "brand", "product_name", "description", "image_url", "price", "status")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, model in (("category", Category), ("brand", Brand)):
            active = Q(status=Status.ACTIVE)
            if self.instance.pk:
                # Keep current item even if INACTIVE to avoid data loss on edit
                active |= Q(pk=getattr(self.instance, f"{field_name}_id"))
            self.fields[field_name].queryset = model.objects.filter(active).order_by(
                {"category": "category_name", "brand": "brand_name"}[field_name]
            )
            self.fields[field_name].empty_label = "-- Select --"

    def clean_product_name(self):
        name = self.cleaned_data["product_name"].strip()
        if not name:
            raise forms.ValidationError("Product name cannot be empty.")
        return name

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("Price must be greater than 0.")
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
            raise forms.ValidationError("Category name already exists.")
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
            raise forms.ValidationError("Brand name already exists.")
        return name
