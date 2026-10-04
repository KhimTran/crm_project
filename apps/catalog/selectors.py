from django.core.paginator import Paginator
from django.db.models import Q

from .models import Supplier


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
