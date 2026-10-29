from django.db.models import Q
from apps.catalog.vocabulary import search_aliases
from apps.catalog.models import Product, Status


def visible_products():
    return Product.objects.filter(status=Status.ACTIVE).select_related("category", "brand").order_by("product_id")


def filtered_products(filters):
    products = visible_products()
    if filters.get("q"):
        search = Q()
        for term in search_aliases(filters["q"]):
            search |= Q(product_name__icontains=term) | Q(brand__brand_name__icontains=term)
        products = products.filter(search)
    for field in ("category", "brand"):
        if filters.get(field):
            products = products.filter(**{field: filters[field]})
    if filters.get("min_price") is not None:
        products = products.filter(price__gte=filters["min_price"])
    if filters.get("max_price") is not None:
        products = products.filter(price__lte=filters["max_price"])
    return products
