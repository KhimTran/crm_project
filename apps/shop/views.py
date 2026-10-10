from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .forms import ProductFilterForm
from .selectors import filtered_products, visible_products


@require_GET
def home(request):
    return render(request, "shop/home.html", {"products": visible_products()[:6]})


@require_GET
def products(request):
    form = ProductFilterForm(request.GET)
    valid = form.is_valid()
    queryset = filtered_products(form.cleaned_data) if valid else visible_products().none()
    page = Paginator(queryset, 12).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "shop/products.html", {
        "form": form, "page": page, "filter_query": query.urlencode(),
    }, status=200 if valid else 400)


@require_GET
def product_detail(request, product_id):
    product = get_object_or_404(visible_products(), pk=product_id)
    return render(request, "shop/product_detail.html", {"product": product})
