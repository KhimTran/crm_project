from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts.constants import AccountRole
from apps.accounts.decorators import role_required
from apps.feedback.models import Feedback

from . import reports
from .constants import CustomerStatus, PreferenceType
from .errors import CustomerNotFound, CustomerServiceError
from .forms import CustomerCreateForm, CustomerFilterForm, CustomerLockForm
from .models import Customer, CustomerPreference
from .portal_text import localize_form, localize_rows, portal_english, say, tr
from .selectors import customer_queryset, filter_customers
from .self_service_choices import CATEGORY_PREFERENCE_TYPE
from .self_service_forms import CustomerCategoryPreferencesForm, CustomerProfileForm
from .self_services import own_customer, update_own_profile
from .services import create_customer, customer_related_counts, delete_customer, lock_customer, unlock_customer

PAGE_SIZE = 10


# tv4: kiểm tra tài khoản là Admin hoặc thuộc nhóm Quản lý CRM (để hiện nút thêm/khóa/xóa; CSKH chỉ xem)
def is_crm_manager(user):
    return getattr(user, "role", None) == AccountRole.ADMIN or user.groups.filter(name="CRM_MANAGER").exists()


# tv4: danh sách khách hàng chưa xóa, tìm kiếm + bộ lọc (selectors.filter_customers), phân trang
@role_required("ADMIN", "CRM_MANAGER", "CUSTOMER_SERVICE")
@portal_english
def customer_list(request):
    form = localize_form(CustomerFilterForm(request.GET or None))
    customers = customer_queryset()
    if form.is_bound and form.is_valid():
        customers = filter_customers(customers, form.cleaned_data)
    page = Paginator(customers, PAGE_SIZE).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "customers/customer_list.html", {"form": form, "page": page, "query": query.urlencode(),
                                                            "can_manage": is_crm_manager(request.user)})


# tv4: tạo khách hàng và hiển thị mật khẩu tạm một lần.
@role_required("ADMIN", "CRM_MANAGER")
@portal_english
def customer_create(request):
    form = localize_form(CustomerCreateForm(request.POST or None))
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            customer, password = create_customer(**data)
        except CustomerServiceError as exc:
            form.add_error(None, tr(str(exc)))
        else:
            messages.success(
                request,
                say(f"Đã thêm khách hàng {customer.customer_code} – "
                    f"{customer.full_name}. "
                    f"Tài khoản: {customer.account.email} · "
                    f"Mật khẩu tạm: {password} (chỉ hiển thị một lần).",
                    f"Customer {customer.customer_code} – {customer.full_name} created. "
                    f"Account: {customer.account.email} · "
                    f"Temporary password: {password} (shown only once)."),
            )
            return redirect("customers:list")

    return render(
        request,
        "customers/customer_form.html",
        {"form": form},
    )


# tv4: lấy khách hàng chưa bị xóa.
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


# tv4: chi tiết khách hàng: thông tin, sở thích, số liệu liên quan, lịch sử phản hồi
@role_required("ADMIN", "CRM_MANAGER", "CUSTOMER_SERVICE")
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


# tv4: sau khi khóa/mở khóa thì quay lại trang đã bấm (chi tiết hoặc danh sách)
def _back_after_action(request, customer_id):
    if request.POST.get("from") == "detail":
        return redirect("customers:detail", customer_id=customer_id)
    return redirect("customers:list")


# tv4: 4.1.3 xử lý nút khóa tài khoản khách hàng (POST), kèm lý do trong thông báo
@role_required("ADMIN", "CRM_MANAGER")
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
        messages.error(request, tr(str(exc)))
    else:
        suffix = say(f" Lý do: {reason}", f" Reason: {reason}") if reason else ""
        messages.success(request, say(f"Đã khóa tài khoản {customer.customer_code} – {customer.full_name}.",
                                      f"Account {customer.customer_code} – {customer.full_name} locked.") + suffix)
    return _back_after_action(request, customer_id)


# tv4: mở khóa tài khoản khách hàng, chỉ nhận POST.
@role_required("ADMIN", "CRM_MANAGER")
@require_POST
@portal_english
def customer_unlock(request, customer_id):
    try:
        customer = unlock_customer(customer_id)
    except CustomerNotFound as exc:
        raise Http404(str(exc)) from exc
    except CustomerServiceError as exc:
        messages.error(request, tr(str(exc)))
    else:
        messages.success(request, say(f"Đã mở khóa tài khoản {customer.customer_code} – {customer.full_name}.",
                                      f"Account {customer.customer_code} – {customer.full_name} unlocked."))
    return _back_after_action(request, customer_id)


# tv4: xác nhận và thực hiện xóa mềm khách hàng.
@role_required("ADMIN", "CRM_MANAGER")
@portal_english
def customer_delete(request, customer_id):
    customer = _get_active_customer_or_404(customer_id)

    if request.method == "POST":
        try:
            delete_customer(customer.pk)
        except CustomerNotFound as exc:
            raise Http404(str(exc)) from exc
        except CustomerServiceError as exc:
            messages.error(request, tr(str(exc)))
        else:
            messages.success(
                request,
                say(f"Đã xóa khách hàng {customer.customer_code} – "
                    f"{customer.full_name}.",
                    f"Customer {customer.customer_code} – {customer.full_name} deleted."),
            )
        return redirect("customers:list")
    return render(request, "customers/customer_confirm_delete.html",
                  {"customer": customer, "counts": customer_related_counts(customer)})


# tv4: 4.1.5 trang báo cáo khách hàng: biểu đồ Chart.js + bảng số liệu, có nút In
@role_required("ADMIN", "CRM_MANAGER", "CUSTOMER_SERVICE")
@portal_english
def customer_report(request):
    charts = {
        "age": localize_rows(reports.age_group_report()),
        "gender": localize_rows(reports.gender_report()),
        "level": localize_rows(reports.playing_level_report()),
        "monthly": reports.new_customers_by_month(),
        "satisfaction": reports.satisfaction_by_product(),
        "preferences": [{**group, "label": tr(group["label"]), "rows": localize_rows(group["rows"])}
                        for group in reports.preference_report()],
        "labels": {"customers": say("Số khách hàng", "Customers"),
                   "new_customers": say("Khách hàng mới", "New customers"),
                   "avg_rating": say("Điểm hài lòng TB", "Avg. satisfaction")},
    }
    return render(request, "customers/customer_report.html", {
        "summary": reports.summary(),
        "charts": charts,
        "generated_at": timezone.localtime(),
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
