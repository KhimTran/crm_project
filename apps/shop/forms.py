from django import forms

from apps.catalog.models import Brand, Category, Status


class ProductFilterForm(forms.Form):
    q = forms.CharField(label="Product Name", required=False, max_length=200)
    category = forms.ModelChoiceField(label="Category", required=False, queryset=Category.objects.filter(status=Status.ACTIVE).order_by("category_name"))
    brand = forms.ModelChoiceField(label="Brand", required=False, queryset=Brand.objects.filter(status=Status.ACTIVE).order_by("brand_name"))
    min_price = forms.DecimalField(label="Min Price", required=False, min_value=0, max_digits=12, decimal_places=2)
    max_price = forms.DecimalField(label="Max Price", required=False, min_value=0, max_digits=12, decimal_places=2)

    def clean(self):
        data = super().clean()
        if data.get("min_price") is not None and data.get("max_price") is not None and data["min_price"] > data["max_price"]:
            self.add_error("max_price", "Maximum price must be greater than or equal to minimum price.")
        return data
