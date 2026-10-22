from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from apps.accounts.constants import AccountRole
from apps.accounts.decorators import role_required
from apps.feedback.models import Feedback

from .constants import CustomerStatus, PreferenceType
from .errors import CustomerNotFound, CustomerServiceError, DuplicateCustomerEmail, DuplicateCustomerPhone
from .forms import CustomerCreateForm, CustomerEditForm, CustomerFilterForm, CustomerLockForm
from .models import Customer, CustomerPreference
from . import reports
from .portal_text import localize_form, localize_rows, portal_english, say, tr
from .selectors import customer_queryset, filter_customers
from .self_service_choices import CATEGORY_PREFERENCE_TYPE
from .self_service_forms import CustomerCategoryPreferencesForm, CustomerProfileForm
from .self_services import own_customer, update_own_profile
from .services import (
    create_customer, customer_related_counts, delete_customer,
    lock_customer, unlock_customer, update_customer,
)

PAGE_SIZE = 10


# tv4: kiểm tra tài khoản là Admin hoặc thuộc nhóm Quản lý CRM (để hiện nút thêm/khóa/xóa; CSKH chỉ xem)
def is_crm_manager(user):
    return getattr(user, "role", None) in (AccountRole.ADMIN, AccountRole.MANAGER) or user.groups.filter(name="CRM_MANAGER").exists()


def _customer_list_context(request):
    form = localize_form(CustomerFilterForm(request.GET or None))
    customers = customer_queryset()
    if form.is_bound and form.is_valid():
        customers = filter_customers(customers, form.cleaned_data)
    page = Paginator(customers, PAGE_SIZE).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return {"form": form, "page": page, "query": query.urlencode(),
            "can_manage": is_crm_manager(request.user)}


# The regular list and the successful create response use the same scope and rendering.
@role_required("ADMIN", "MANAGER", "CRM_MANAGER", "CUSTOMER_SERVICE")
@portal_english
def customer_list(request):
    return render(request, "customers/customer_list.html", _customer_list_context(request))


# Both HTML and asynchronous submissions use the same form and atomic service.
@never_cache
@sensitive_post_parameters("password")
@role_required("ADMIN", "MANAGER", "CRM_MANAGER")
@require_http_methods(["GET", "POST"])
@portal_english
def customer_create(request):
    form = localize_form(CustomerCreateForm(request.POST if request.method == "POST" else None))
    wants_json = "application/json" in request.headers.get("Accept", "")
    status = 400
    if request.method == "POST":
        try:
            if form.is_valid():
                # If rendering the updated list fails, do not leave an account saved
                # behind a failed response that invites the user to submit again.
                with transaction.atomic():
                    customer = create_customer(**form.cleaned_data)
                    success = f"Customer {customer.customer_code} – {customer.full_name} created."
                    if wants_json:
                        context = {**_customer_list_context(request), "created_message": success}
                        response = JsonResponse({
                            "customer_id": customer.pk,
                            "message": success,
                            "list_url": reverse("customers:list"),
                            "page_title": "Customers",
                            "html": render_to_string("customers/_customer_list.html", context, request=request),
                        }, status=201)
                if wants_json:
                    return response
                messages.success(request, success)
                return redirect("customers:list")
        except DuplicateCustomerEmail as exc:
            form.add_error("email", tr(str(exc)))
            status = 409
        except DuplicateCustomerPhone as exc:
            form.add_error("phone", tr(str(exc)))
            status = 409
        except CustomerServiceError as exc:
            form.add_error(None, tr(str(exc)))
        except ValidationError as exc:
            form.add_error("password", exc)
        except DatabaseError:
            form.add_error(None, "Unable to save the customer right now. Please try again.")
            status = 503
        if wants_json:
            return JsonResponse({"errors": {
                field: [tr(message) for message in errors]
                for field, errors in form.errors.items()
            }}, status=status)

    return render(
        request,
        "customers/customer_form.html",
        {"form": form},
    )


# Lấy khách hàng
def _get_active_customer_or_404(customer_id):
    customer = Customer.objects.filter(pk=customer_id).first()
    if customer is None:
        raise Http404("Customer not found")
    return customer


# tv4: chi tiết khách hàng: thông tin, sở thích, số liệu liên quan, lịch sử phản hồi
@role_required("ADMIN", "MANAGER", "CRM_MANAGER", "CUSTOMER_SERVICE")
@portal_english
def customer_detail(request, customer_id):
    customer = _get_active_customer_or_404(customer_id)
    preferences = {}
    for pref in customer.customerpreference_set.order_by("preference_type", "preference_value"):
        preferences.setdefault(tr(PreferenceType(pref.preference_type).label)
                               if pref.preference_type in PreferenceType.values else pref.preference_type,
                               []).append(tr(pref.preference_value))
    feedbacks = (Feedback.objects.filter(customer=customer).select_related("product", "handled_by")
                 .order_by("-created_at", "-feedback_id"))
    return render(request, "customers/customer_detail.html", {
        "customer": customer,
        "preferences": preferences,
        "feedbacks": feedbacks,
        "counts": customer_related_counts(customer),
        "can_manage": is_crm_manager(request.user),
    })


@role_required("ADMIN", "MANAGER", "CRM_MANAGER")
@require_http_methods(["GET", "POST"])
@portal_english
def customer_edit(request, customer_id):
    customer = _get_active_customer_or_404(customer_id)
    if customer.role != AccountRole.CUSTOMER:
        raise Http404("Only customer accounts can be edited here")

    if request.method == "POST":
        form = CustomerEditForm(request.POST, customer_id=customer_id)
        if form.is_valid():
            try:
                update_customer(
                    customer_id,
                    email=form.cleaned_data["email"],
                    full_name=form.cleaned_data["full_name"],
                    phone=form.cleaned_data.get("phone"),
                    date_of_birth=form.cleaned_data.get("date_of_birth"),
                    gender=form.cleaned_data.get("gender"),
                    address=form.cleaned_data.get("address"),
                    playing_level=form.cleaned_data.get("playing_level"),
                )
            except (DuplicateCustomerEmail, DuplicateCustomerPhone, CustomerServiceError) as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, f"Customer {customer.customer_code} – {customer.full_name} updated successfully.")
                return redirect("customers:detail", customer_id=customer_id)
    else:
        form = CustomerEditForm(initial={
            "full_name": customer.full_name,
            "email": customer.email,
            "phone": customer.phone or "",
            "date_of_birth": customer.date_of_birth,
            "gender": customer.gender or "",
            "address": customer.address or "",
            "playing_level": customer.playing_level or "",
        }, customer_id=customer_id)

    return render(request, "customers/customer_form.html", {
        "form": form,
        "is_edit": True,
        "customer": customer,
    })


# tv4: sau khi khóa/mở khóa thì quay lại trang đã bấm (chi tiết hoặc danh sách)
def _back_after_action(request, customer_id):
    if request.POST.get("from") == "detail":
        return redirect("customers:detail", customer_id=customer_id)
    return redirect("customers:list")


# tv4: 4.1.3 xử lý nút khóa tài khoản khách hàng (POST), kèm lý do trong thông báo
@role_required("ADMIN", "MANAGER", "CRM_MANAGER")
@require_POST
@portal_english
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
        suffix = f" Reason: {reason}" if reason else ""
        messages.success(request, f"Account {customer.customer_code} – {customer.full_name} locked.{suffix}")
    return _back_after_action(request, customer_id)


# tv4: mở khóa tài khoản khách hàng, chỉ nhận POST.
@role_required("ADMIN", "MANAGER", "CRM_MANAGER")
@require_POST
@portal_english
def customer_unlock(request, customer_id):
    try:
        customer = unlock_customer(customer_id)
    except CustomerNotFound as exc:
        raise Http404(str(exc)) from exc
    except CustomerServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Account {customer.customer_code} – {customer.full_name} unlocked.")
    return _back_after_action(request, customer_id)


# tv4: xác nhận và thực hiện xóa mềm khách hàng.
@role_required("ADMIN", "MANAGER", "CRM_MANAGER")
@portal_english
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
                f"Customer {customer.customer_code} – {customer.full_name} deleted.",
            )
        return redirect("customers:list")
    return render(request, "customers/customer_confirm_delete.html",
                  {"customer": customer, "counts": customer_related_counts(customer)})


# tv4: 4.1.5 trang báo cáo khách hàng: biểu đồ Chart.js + bảng số liệu, có nút In
@role_required("ADMIN", "MANAGER", "CRM_MANAGER", "CUSTOMER_SERVICE")
@portal_english
def customer_report(request):
    # Chỉ báo cáo khách hàng 4.1.5; kết quả khảo sát 4.1.7 nằm ở trang riêng surveys:results.
    customer_charts = {
        "age": localize_rows(reports.age_group_report()),
        "gender": localize_rows(reports.gender_report()),
        "level": localize_rows(reports.playing_level_report()),
        "monthly": reports.new_customers_by_month(),
        "labels": {"customers": say("Số khách hàng", "Customers"),
                   "new_customers": say("Khách hàng mới", "New customers"),
                   "avg_rating": say("Điểm hài lòng TB", "Avg. satisfaction")},
    }
    customer_extra = {
        "accounts": reports.account_status_report(),
        "deleted": reports.deleted_count(),
    }
    # tv4: thương hiệu yêu thích; lỗi truy vấn chỉ làm hỏng card này (error state), không làm hỏng cả báo cáo
    try:
        customer_charts["favorite_brands"] = reports.favorite_brand_report()
        favorite_brand_error = False
    except DatabaseError:
        customer_charts["favorite_brands"] = None
        favorite_brand_error = True

    return render(request, "customers/customer_report.html", {
        "generated_at": timezone.localtime(),
        "summary": reports.summary(), "customer_charts": customer_charts, "customer_extra": customer_extra,
        "favorite_brand_error": favorite_brand_error,
    })


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
                messages.success(request, "Profile and preferences updated successfully.")
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
