from django.core.paginator import Paginator
from django.db.models import Q

from .models import Brand, Category, Product, Supplier

SUPPLIER_SORTS = {
    "id": "supplier_id",
    "code": "supplier_code",
    "name": "supplier_name",
    "status": "status",
    "created": "created_at",
}

PRODUCT_SORTS = {
    "id": "product_id",
    "name": "product_name",
    "category": "category__category_name",
    "brand": "brand__brand_name",
    "supplier": "supplier__supplier_name",
    "price": "price",
    "status": "status",
    "created": "created_at",
}


def _order(query, sorts, sort, direction, default_key, tie_breaker):
    field = sorts.get(sort) or sorts[default_key]
    if direction == "desc":
        field = f"-{field}"
    return query.order_by(field, tie_breaker)


def list_supplier_page(*, page=1, q="", status="", sort="", direction="", page_size=20):
    query = Supplier.objects.all()
    search = q.strip()
    if search:
        query = query.filter(
            Q(supplier_code__icontains=search)
            | Q(supplier_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )
    if status:
        query = query.filter(status=status)
    query = _order(query, SUPPLIER_SORTS, sort, direction, "name", "supplier_id")
    return Paginator(query, page_size).get_page(page)


def list_product_page(*, page=1, q="", status="", supplier_id="", category_id="",
                      brand_id="", sort="", direction="", page_size=10):
    query = Product.objects.select_related("category", "brand", "supplier")
    search = q.strip()
    if search:
        query = query.filter(
            Q(product_name__icontains=search)
            | Q(supplier__supplier_name__icontains=search)
            | Q(brand__brand_name__icontains=search)
            | Q(category__category_name__icontains=search)
        )
    if status:
        query = query.filter(status=status)
    if supplier_id:
        query = query.filter(supplier_id=supplier_id)
    if category_id:
        query = query.filter(category_id=category_id)
    if brand_id:
        query = query.filter(brand_id=brand_id)
    query = _order(query, PRODUCT_SORTS, sort, direction, "id", "product_id")
    return Paginator(query, page_size).get_page(page)


def _list_simple_page(model, name_field, *, page, q, status, sort, direction, page_size):
    sorts = {"id": "pk", "name": name_field, "status": "status", "created": "created_at"}
    query = model.objects.all()
    search = q.strip()
    if search:
        query = query.filter(
            Q(**{f"{name_field}__icontains": search}) | Q(description__icontains=search)
        )
    if status:
        query = query.filter(status=status)
    query = _order(query, sorts, sort, direction, "name", "pk")
    return Paginator(query, page_size).get_page(page)


def list_category_page(*, page=1, q="", status="", sort="", direction="", page_size=10):
    return _list_simple_page(Category, "category_name", page=page, q=q, status=status,
                             sort=sort, direction=direction, page_size=page_size)


def list_brand_page(*, page=1, q="", status="", sort="", direction="", page_size=10):
    return _list_simple_page(Brand, "brand_name", page=page, q=q, status=status,
                             sort=sort, direction=direction, page_size=page_size)