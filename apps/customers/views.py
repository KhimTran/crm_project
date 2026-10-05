from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required

from .constants import CustomerStatus
from .errors import CustomerNotFound, CustomerServiceError
from .forms import CustomerCreateForm, CustomerLockForm
from .models import Customer
from .services import create_customer, customer_related_counts, delete_customer, lock_customer, unlock_customer

PAGE_SIZE = 10


# tv4: danh sách khách hàng chưa xóa, tìm theo tên/SĐT/email, phân trang
@role_required("CRM_MANAGER")
def customer_list(request):
    q = request.GET.get("q", "").strip()
    customers = (Customer.objects.exclude(status=CustomerStatus.DELETED)
                 .select_related("account").order_by("-customer_id"))
    if q:
        customers = customers.filter(Q(full_name__icontains=q) | Q(phone__icontains=q)
                                     | Q(account__email__icontains=q))
    page = Paginator(customers, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "customers/customer_list.html", {"page": page, "q": q})


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
    return redirect("customers:list")


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
    return redirect("customers:list")


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
