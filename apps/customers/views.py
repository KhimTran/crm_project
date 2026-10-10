from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.decorators import role_required

from .constants import CustomerStatus
from .errors import CustomerNotFound, CustomerServiceError
from .forms import CustomerCreateForm, CustomerLockForm
from .models import Customer, CustomerPreference
from .self_service_choices import CATEGORY_PREFERENCE_TYPE
from .self_service_forms import CustomerCategoryPreferencesForm, CustomerProfileForm
from .self_services import own_customer, update_own_profile
from .services import (
    create_customer,
    customer_related_counts,
    delete_customer,
    lock_customer,
    unlock_customer,
)

PAGE_SIZE = 10


# TV4: danh sách khách hàng, tìm kiếm và phân trang.
@role_required("CRM_MANAGER")
def customer_list(request):
    q = request.GET.get("q", "").strip()
    customers = (
        Customer.objects.exclude(status=CustomerStatus.DELETED)
        .select_related("account")
        .order_by("-customer_id")
    )
    if q:
        customers = customers.filter(
            Q(full_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(account__email__icontains=q)
        )

    page = Paginator(customers, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(
        request,
        "customers/customer_list.html",
        {"page": page, "q": q},
    )


# TV4: tạo khách hàng và hiển thị mật khẩu tạm một lần.
@role_required("CRM_MANAGER")
def customer_create(request):
    form = CustomerCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            customer, password = create_customer(**data)
        except CustomerServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(
                request,
                f"Đã thêm khách hàng {customer.customer_code} – "
                f"{customer.full_name}. "
                f"Tài khoản: {customer.account.email} · "
                f"Mật khẩu tạm: {password} (chỉ hiển thị một lần).",
            )
            return redirect("customers:list")

    return render(
        request,
        "customers/customer_form.html",
        {"form": form},
    )


# TV4: lấy khách hàng chưa bị xóa.
def _get_active_customer_or_404(customer_id):
    customer = (
        Customer.objects.select_related("account")
        .filter(pk=customer_id)
        .exclude(status=CustomerStatus.DELETED)
        .first()
    )
    if customer is None:
        raise Http404("Không tìm thấy khách hàng")
    return customer


# TV4: khóa tài khoản khách hàng, chỉ nhận POST.
@role_required("CRM_MANAGER")
@require_POST
def customer_lock(request, customer_id):
    form = CustomerLockForm(request.POST)
    reason = form.cleaned_data["reason"] if form.is_valid() else ""

    try:
        customer = lock_customer(customer_id)
    except CustomerNotFound as exc:
        raise Http404(str(exc)) from exc
    except CustomerServiceError as exc:
        messages.error(request, str(exc))
    else:
        suffix = f" Lý do: {reason}" if reason else ""
        messages.success(
            request,
            f"Đã khóa tài khoản {customer.customer_code} – "
            f"{customer.full_name}.{suffix}",
        )

    return redirect("customers:list")


# TV4: mở khóa tài khoản khách hàng, chỉ nhận POST.
@role_required("CRM_MANAGER")
@require_POST
def customer_unlock(request, customer_id):
    try:
        customer = unlock_customer(customer_id)
    except CustomerNotFound as exc:
        raise Http404(str(exc)) from exc
    except CustomerServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(
            request,
            f"Đã mở khóa tài khoản {customer.customer_code} – "
            f"{customer.full_name}.",
        )

    return redirect("customers:list")


# TV4: xác nhận và thực hiện xóa mềm khách hàng.
@role_required("CRM_MANAGER")
def customer_delete(request, customer_id):
    customer = _get_active_customer_or_404(customer_id)

    if request.method == "POST":
        try:
            delete_customer(customer.pk)
        except CustomerNotFound as exc:
            raise Http404(str(exc)) from exc
        except CustomerServiceError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"Đã xóa khách hàng {customer.customer_code} – "
                f"{customer.full_name}.",
            )
        return redirect("customers:list")

    return render(
        request,
        "customers/customer_confirm_delete.html",
        {
            "customer": customer,
            "counts": customer_related_counts(customer),
        },
    )


# TV1: khách hàng cập nhật hồ sơ và sở thích của chính mình.
@role_required("CUSTOMER")
@require_http_methods(["GET", "POST"])
def profile(request):
    customer = own_customer(request.user)
    data = request.POST if request.method == "POST" else None
    form = CustomerProfileForm(data, instance=customer)
    preferences = CustomerCategoryPreferencesForm(customer, data)

    if request.method == "POST":
        profile_valid = form.is_valid()
        preferences_valid = preferences.is_valid()

        if profile_valid and preferences_valid:
            try:
                update_own_profile(
                    request.user,
                    profile_data=form.cleaned_data,
                    category_ids=preferences.cleaned_data["categories"],
                    remove_preference_ids=preferences.cleaned_data[
                        "remove_preferences"
                    ],
                )
            except ValidationError as exc:
                for field, errors in exc.message_dict.items():
                    target = preferences if field in preferences.fields else form
                    target.add_error(
                        field if field in target.fields else None,
                        errors,
                    )
            else:
                messages.success(request, "Đã cập nhật hồ sơ và sở thích.")
                return redirect("customers:profile")

    other_preferences = (
        CustomerPreference.objects.filter(customer=customer)
        .exclude(preference_type=CATEGORY_PREFERENCE_TYPE)
        .order_by("preference_id")
    )

    return render(
        request,
        "customers/profile.html",
        {
            "form": form,
            "preferences": preferences,
            "customer": customer,
            "other_preferences": other_preferences,
        },
    )