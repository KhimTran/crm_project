from django.core.paginator import Paginator
from django.db.models import Q

from .models import Brand, Category, Supplier


def list_supplier_page(*, page=1, q="", status="", page_size=20):
    query = Supplier.objects.order_by("supplier_name", "supplier_id")
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
    return Paginator(query, page_size).get_page(page)


def _list_simple_page(model, name_field, *, page, q, status, page_size):
    query = model.objects.order_by(name_field, "pk")
    search = q.strip()
    if search:
        query = query.filter(
            Q(**{f"{name_field}__icontains": search}) | Q(description__icontains=search)
        )
    if status:
        query = query.filter(status=status)
    return Paginator(query, page_size).get_page(page)


def list_category_page(*, page=1, q="", status="", page_size=10):
    return _list_simple_page(Category, "category_name", page=page, q=q, status=status, page_size=page_size)


def list_brand_page(*, page=1, q="", status="", page_size=10):
    return _list_simple_page(Brand, "brand_name", page=page, q=q, status=status, page_size=page_size)