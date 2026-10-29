from django.core.paginator import Paginator
from django.db.models import Q

from .models import Brand, Category, Product
from .vocabulary import search_aliases

PRODUCT_SORTS = {
    "id": "product_id",
    "name": "product_name",
    "category": "category__category_name",
    "brand": "brand__brand_name",
    "price": "price",
    "status": "status",
    "created": "created_at",
}


def _order(query, sorts, sort, direction, default_key, tie_breaker):
    field = sorts.get(sort) or sorts[default_key]
    if direction == "desc":
        field = f"-{field}"
    return query.order_by(field, tie_breaker)


def list_product_page(*, page=1, q="", status="", category_id="",
                      brand_id="", sort="", direction="", page_size=10):
    query = Product.objects.select_related("category", "brand")
    search = q.strip()
    if search:
        condition = Q(category__category_name__icontains=search)
        for term in search_aliases(search):
            condition |= Q(product_name__icontains=term) | Q(brand__brand_name__icontains=term)
        query = query.filter(condition)
    if status:
        query = query.filter(status=status)
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
        condition = Q(description__icontains=search)
        for term in search_aliases(search) if model is Brand else (search,):
            condition |= Q(**{f"{name_field}__icontains": term})
        query = query.filter(condition)
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