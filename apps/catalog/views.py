from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import urlencode
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.permissions import account_admin_required
from django.urls import reverse
from .forms import BrandForm, CategoryForm, ProductForm, SupplierForm
from .models import Brand, Category, Product, Status, Supplier
from .selectors import list_brand_page, list_category_page, list_supplier_page


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

def _simple_list(request, *, page_func, **context):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    if status not in Status.values:
        status = ""
    page_obj = page_func(page=request.GET.get("page", 1), q=query, status=status)
    filter_query = urlencode({k: v for k, v in {"q": query, "status": status}.items() if v})
    return render(request, "catalog/admin/simple_list.html", {
        "page_obj": page_obj, "items": page_obj.object_list, "query": query,
        "status_filter": status, "filter_query": filter_query, **context,
    })


@account_admin_required
@require_GET
def category_list(request):
    return _simple_list(
        request, page_func=list_category_page, title="Categories", singular="Category",
        list_url="catalog_admin:category_list", create_url="catalog_admin:category_create",
        edit_url="catalog_admin:category_edit", delete_url="catalog_admin:category_delete",
    )


@account_admin_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    form = CategoryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã tạo danh mục.")
        return redirect("catalog_admin:category_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Danh mục", "back_url": reverse("catalog_admin:category_list")})


@account_admin_required
@require_http_methods(["GET", "POST"])
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    form = CategoryForm(request.POST if request.method == "POST" else None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật danh mục.")
        return redirect("catalog_admin:category_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Danh mục", "back_url": reverse("catalog_admin:category_list")})


@account_admin_required
@require_POST
def category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    try:
        category.delete()
    except ProtectedError:
        messages.error(request, "Không thể xóa danh mục đang có sản phẩm.")
    else:
        messages.success(request, "Đã xóa danh mục.")
    return redirect("catalog_admin:category_list")


@account_admin_required
@require_GET
def brand_list(request):
    return _simple_list(
        request, page_func=list_brand_page, title="Brands", singular="Brand",
        list_url="catalog_admin:brand_list", create_url="catalog_admin:brand_create",
        edit_url="catalog_admin:brand_edit", delete_url="catalog_admin:brand_delete",
    )


@account_admin_required
@require_http_methods(["GET", "POST"])
def brand_create(request):
    form = BrandForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã tạo thương hiệu.")
        return redirect("catalog_admin:brand_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Thương hiệu", "back_url": reverse("catalog_admin:brand_list")})


@account_admin_required
@require_http_methods(["GET", "POST"])
def brand_edit(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    form = BrandForm(request.POST if request.method == "POST" else None, instance=brand)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật thương hiệu.")
        return redirect("catalog_admin:brand_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Thương hiệu", "back_url": reverse("catalog_admin:brand_list")})


@account_admin_required
@require_POST
def brand_delete(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    try:
        brand.delete()
    except ProtectedError:
        messages.error(request, "Không thể xóa thương hiệu đang có sản phẩm.")
    else:
        messages.success(request, "Đã xóa thương hiệu.")
    return redirect("catalog_admin:brand_list")
