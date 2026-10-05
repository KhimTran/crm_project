from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.feedback.models import Feedback

from . import reports
from .constants import CustomerStatus, PreferenceType
from .errors import CustomerNotFound, CustomerServiceError
from .forms import CustomerCreateForm, CustomerFilterForm, CustomerLockForm
from .models import Customer
from .selectors import customer_queryset, filter_customers
from .services import create_customer, customer_related_counts, delete_customer, lock_customer, unlock_customer

PAGE_SIZE = 10


# tv4: kiểm tra tài khoản có thuộc nhóm Quản lý CRM không (để hiện nút thêm/khóa/xóa; CSKH chỉ xem)
def is_crm_manager(user):
    return user.groups.filter(name="CRM_MANAGER").exists()


# tv4: danh sách khách hàng chưa xóa, tìm kiếm + bộ lọc (selectors.filter_customers), phân trang
@role_required("CRM_MANAGER", "CUSTOMER_SERVICE")
def customer_list(request):
    form = CustomerFilterForm(request.GET or None)
    customers = customer_queryset()
    if form.is_bound and form.is_valid():
        customers = filter_customers(customers, form.cleaned_data)
    page = Paginator(customers, PAGE_SIZE).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "customers/customer_list.html", {"form": form, "page": page, "query": query.urlencode(),
                                                            "can_manage": is_crm_manager(request.user)})


# tv4: 4.1.1 form thêm khách hàng mới, hiển thị mật khẩu tạm một lần sau khi lưu
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
                f"Đã thêm khách hàng {customer.customer_code} – {customer.full_name}. "
                f"Tài khoản: {customer.account.email} · Mật khẩu tạm: {password} (chỉ hiển thị một lần).",
            )
            return redirect("customers:list")
    return render(request, "customers/customer_form.html", {"form": form})


# tv4: lấy khách hàng chưa xóa cho các trang thao tác, không có thì trả 404
def _get_active_customer_or_404(customer_id):
    customer = (Customer.objects.select_related("account")
                .filter(pk=customer_id).exclude(status=CustomerStatus.DELETED).first())
    if customer is None:
        raise Http404("Không tìm thấy khách hàng")
    return customer


# tv4: chi tiết khách hàng: thông tin, sở thích, số liệu liên quan, lịch sử phản hồi
@role_required("CRM_MANAGER", "CUSTOMER_SERVICE")
def customer_detail(request, customer_id):
    customer = _get_active_customer_or_404(customer_id)
    preferences = {}
    for pref in customer.customerpreference_set.order_by("preference_type", "preference_value"):
        preferences.setdefault(PreferenceType(pref.preference_type).label
                               if pref.preference_type in PreferenceType.values else pref.preference_type,
                               []).append(pref.preference_value)
    feedbacks = (Feedback.objects.filter(customer=customer).select_related("product", "handled_by")
                 .order_by("-created_at", "-feedback_id"))
    return render(request, "customers/customer_detail.html", {
        "customer": customer,
        "preferences": reports.preference_report(),
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
        messages.success(request, f"Đã khóa tài khoản {customer.customer_code} – {customer.full_name}.{suffix}")
    return _back_after_action(request, customer_id)


# tv4: 4.1.3 xử lý nút mở khóa tài khoản khách hàng (POST)
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
        messages.success(request, f"Đã mở khóa tài khoản {customer.customer_code} – {customer.full_name}.")
    return _back_after_action(request, customer_id)


# tv4: 4.1.2 GET hiện trang xác nhận + cảnh báo dữ liệu liên quan, POST thực hiện xóa mềm
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
            messages.success(request, f"Đã xóa khách hàng {customer.customer_code} – {customer.full_name}.")
        return redirect("customers:list")
    return render(request, "customers/customer_confirm_delete.html",
                  {"customer": customer, "counts": customer_related_counts(customer)})


# tv4: 4.1.5 trang báo cáo khách hàng: biểu đồ Chart.js + bảng số liệu, có nút In
@role_required("CRM_MANAGER", "CUSTOMER_SERVICE")
def customer_report(request):
    charts = {
        "age": reports.age_group_report(),
        "gender": reports.gender_report(),
        "level": reports.playing_level_report(),
        "monthly": reports.new_customers_by_month(),
        "satisfaction": reports.satisfaction_by_product(),
        "preferences": reports.preference_report(),
    }
    return render(request, "customers/customer_report.html", {
        "summary": reports.summary(),
        "charts": charts,
        "generated_at": timezone.localtime(),
    })
