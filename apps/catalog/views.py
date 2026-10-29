from django.contrib import messages
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.accounts.permissions import manager_required
from .forms import BrandForm, CategoryForm, ProductForm
from .models import Brand, Category, Product, Status
from .selectors import list_brand_page, list_category_page, list_product_page


def _sort_params(request):
    sort = request.GET.get("sort", "").strip()
    direction = request.GET.get("dir", "").strip().lower()
    if direction not in ("asc", "desc"):
        direction = "asc"
    return sort, direction


def _query_strings(filters, sort, direction):
    base = urlencode({k: v for k, v in filters.items() if v})
    full = urlencode({k: v for k, v in {**filters, "sort": sort, "dir": direction if sort else ""}.items() if v})
    return base, full


@manager_required
@require_GET
def product_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    if status not in Status.values:
        status = ""

    def _id_param(name):
        value = request.GET.get(name, "").strip()
        return value if value.isdecimal() else ""

    category_id = _id_param("category")
    brand_id = _id_param("brand")
    sort, direction = _sort_params(request)
    page_obj = list_product_page(
        page=request.GET.get("page", 1), q=query, status=status,
        category_id=category_id, brand_id=brand_id, sort=sort, direction=direction,
    )
    base_query, filter_query = _query_strings({
        "q": query, "status": status,
        "category": category_id, "brand": brand_id,
    }, sort, direction)
    return render(request, "catalog/admin/list.html", {
        "items": page_obj.object_list, "kind": "product", "page_obj": page_obj,
        "query": query, "status_filter": status,
        "category_id": category_id, "brand_id": brand_id,
        "categories": Category.objects.order_by("category_name"),
        "brands": Brand.objects.order_by("brand_name"),
        "sort": sort, "direction": direction,
        "base_query": base_query, "filter_query": filter_query,
    })


@manager_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    form = ProductForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product created successfully.")
        return redirect("catalog_admin:product_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Product", "back_url": reverse("catalog_admin:product_list")})


@manager_required
@require_http_methods(["GET", "POST"])
def product_edit(request, product_id):
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("catalog_admin:product_list")
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST if request.method == "POST" else None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Product updated successfully.")
        return redirect(next_url)
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Product",
        "back_url": next_url,
        "next": next_url,
    })


@manager_required
@require_POST
def product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        product.delete()
    except ProtectedError:
        messages.error(request, "Cannot delete product that is currently in use.")
    else:
        messages.success(request, "Product deleted successfully.")
    return redirect("catalog_admin:product_list")


def _simple_list(request, *, page_func, **context):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip().upper()
    if status not in Status.values:
        status = ""
    sort, direction = _sort_params(request)
    page_obj = page_func(page=request.GET.get("page", 1), q=query, status=status,
                         sort=sort, direction=direction)
    base_query, filter_query = _query_strings({"q": query, "status": status}, sort, direction)
    return render(request, "catalog/admin/simple_list.html", {
        "page_obj": page_obj, "items": page_obj.object_list, "query": query,
        "status_filter": status, "sort": sort, "direction": direction,
        "base_query": base_query, "filter_query": filter_query, **context,
    })


@manager_required
@require_GET
def category_list(request):
    return _simple_list(
        request, page_func=list_category_page, title="Categories", singular="Category",
        list_url="catalog_admin:category_list", create_url="catalog_admin:category_create",
        edit_url="catalog_admin:category_edit", delete_url="catalog_admin:category_delete",
    )


@manager_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    form = CategoryForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category created successfully.")
        return redirect("catalog_admin:category_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Category", "back_url": reverse("catalog_admin:category_list")})


@manager_required
@require_http_methods(["GET", "POST"])
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    form = CategoryForm(request.POST if request.method == "POST" else None, instance=category)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Category updated successfully.")
        return redirect("catalog_admin:category_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Category", "back_url": reverse("catalog_admin:category_list")})


@manager_required
@require_POST
def category_delete(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    try:
        category.delete()
    except ProtectedError:
        messages.error(request, "Cannot delete category that contains products.")
    else:
        messages.success(request, "Category deleted successfully.")
    return redirect("catalog_admin:category_list")


@manager_required
@require_GET
def brand_list(request):
    return _simple_list(
        request, page_func=list_brand_page, title="Brands", singular="Brand",
        list_url="catalog_admin:brand_list", create_url="catalog_admin:brand_create",
        edit_url="catalog_admin:brand_edit", delete_url="catalog_admin:brand_delete",
    )


@manager_required
@require_http_methods(["GET", "POST"])
def brand_create(request):
    form = BrandForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Brand created successfully.")
        return redirect("catalog_admin:brand_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Brand", "back_url": reverse("catalog_admin:brand_list")})


@manager_required
@require_http_methods(["GET", "POST"])
def brand_edit(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    form = BrandForm(request.POST if request.method == "POST" else None, instance=brand)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Brand updated successfully.")
        return redirect("catalog_admin:brand_list")
    return render(request, "catalog/admin/form.html", {
        "form": form, "title": "Brand", "back_url": reverse("catalog_admin:brand_list")})


@manager_required
@require_POST
def brand_delete(request, brand_id):
    brand = get_object_or_404(Brand, pk=brand_id)
    try:
        brand.delete()
    except ProtectedError:
        messages.error(request, "Cannot delete brand that contains products.")
    else:
        messages.success(request, "Brand deleted successfully.")
    return redirect("catalog_admin:brand_list")
