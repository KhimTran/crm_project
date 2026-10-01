from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.permissions import account_admin_required
from .forms import ProductForm, SupplierForm
from .models import Product, Status, Supplier
from .selectors import list_supplier_page


@account_admin_required
@require_GET
def supplier_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    if status and status not in Status.values:
        return HttpResponseForbidden("Invalid status")
    page_obj = list_supplier_page(page=request.GET.get("page", 1), q=query, status=status)
    filter_query = urlencode({key: value for key, value in {"q": query, "status": status}.items() if value})
    return render(request, "catalog/admin/list.html", {
        "items": page_obj.object_list, "kind": "supplier", "query": query,
        "status_filter": status, "page_obj": page_obj, "filter_query": filter_query,
    })


@account_admin_required
@require_http_methods(["GET", "POST"])
def supplier_create(request):
    form = SupplierForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã tạo nhà cung cấp.")
        return redirect("catalog_admin:supplier_list")
    return render(request, "catalog/admin/form.html", {"form": form, "title": "Nhà cung cấp"})


@account_admin_required
@require_http_methods(["GET", "POST"])
def supplier_edit(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    form = SupplierForm(request.POST if request.method == "POST" else None, instance=supplier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật nhà cung cấp.")
        return redirect("catalog_admin:supplier_list")
    return render(request, "catalog/admin/form.html", {"form": form, "title": "Nhà cung cấp"})


@account_admin_required
@require_POST
def supplier_delete(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    try:
        supplier.delete()
    except ProtectedError:
        messages.error(request, "Không thể xóa nhà cung cấp đang được sản phẩm sử dụng.")
    else:
        messages.success(request, "Đã xóa nhà cung cấp.")
    return redirect("catalog_admin:supplier_list")


@account_admin_required
@require_GET
def product_list(request):
    products = Product.objects.select_related("category", "brand", "supplier").order_by("product_id")
    supplier_id = request.GET.get("supplier")
    if supplier_id:
        if not supplier_id.isdecimal():
            return HttpResponseForbidden("Invalid supplier")
        products = products.filter(supplier_id=supplier_id)
    query = request.GET.get("q", "").strip()
    if query:
        products = products.filter(Q(product_name__icontains=query) | Q(supplier__supplier_name__icontains=query))
    return render(request, "catalog/admin/list.html", {"items": products, "kind": "product", "suppliers": Supplier.objects.all(), "query": query, "supplier_id": supplier_id})


@account_admin_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã tạo sản phẩm.")
        return redirect("catalog_admin:product_list")
    return render(request, "catalog/admin/form.html", {"form": form, "title": "Sản phẩm"})


@account_admin_required
@require_http_methods(["GET", "POST"])
def product_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST if request.method == "POST" else None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật sản phẩm.")
        return redirect("catalog_admin:product_list")
    return render(request, "catalog/admin/form.html", {"form": form, "title": "Sản phẩm"})


@account_admin_required
@require_POST
def product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        product.delete()
    except ProtectedError:
        messages.error(request, "Không thể xóa sản phẩm đang được sử dụng.")
    else:
        messages.success(request, "Đã xóa sản phẩm.")
    return redirect("catalog_admin:product_list")
