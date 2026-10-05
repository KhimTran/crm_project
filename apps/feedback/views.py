from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required
from apps.customers.constants import CustomerStatus
from apps.customers.models import Customer

from .constants import FeedbackStatus
from .errors import FeedbackNotFound, FeedbackServiceError
from .forms import FeedbackCreateForm, FeedbackFilterForm, FeedbackHandleForm
from .models import Feedback
from .selectors import feedback_queryset, filter_feedbacks
from .services import create_feedback, handle_feedback

PAGE_SIZE = 10


# tv4: 4.1.4 danh sách phản hồi cho quản lý CRM / CSKH, có bộ lọc và phân trang
@role_required("CRM_MANAGER", "CUSTOMER_SERVICE")
def feedback_list(request):
    form = FeedbackFilterForm(request.GET or None)
    feedbacks = feedback_queryset()
    if form.is_bound and form.is_valid():
        feedbacks = filter_feedbacks(feedbacks, form.cleaned_data)
    page = Paginator(feedbacks, PAGE_SIZE).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    return render(request, "feedback/feedback_list.html", {
        "form": form,
        "page": page,
        "query": query.urlencode(),
        "new_count": feedback_queryset().filter(status=FeedbackStatus.NEW).count(),
    })


# tv4: 4.1.4 xem chi tiết phản hồi; POST cập nhật trạng thái + trả lời khách hàng
@role_required("CRM_MANAGER", "CUSTOMER_SERVICE")
def feedback_detail(request, feedback_id):
    feedback = get_object_or_404(feedback_queryset(), pk=feedback_id)
    initial = {"status": (feedback.status if feedback.status != FeedbackStatus.NEW else FeedbackStatus.IN_PROGRESS),
               "manager_note": feedback.manager_note or ""}
    form = FeedbackHandleForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            feedback = handle_feedback(feedback.pk, handled_by=request.user, **form.cleaned_data)
        except FeedbackNotFound:
            return redirect("crm_feedbacks:list")
        except FeedbackServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, f"Đã cập nhật phản hồi #{feedback.feedback_id}: "
                                      f"{feedback.status_label}.")
            return redirect("crm_feedbacks:detail", feedback_id=feedback.pk)
    return render(request, "feedback/feedback_detail.html", {"feedback": feedback, "form": form})


# tv4: 4.2.4 lấy hồ sơ khách hàng (chưa xóa) của tài khoản đang đăng nhập, không có thì trả None
def _current_customer(user):
    return Customer.objects.filter(account=user).exclude(status=CustomerStatus.DELETED).first()


# tv4: 4.2.4 khách hàng gửi phản hồi về sản phẩm (?product=<id> để chọn sẵn sản phẩm từ trang chi tiết)
@role_required("CUSTOMER")
def my_feedback_create(request):
    customer = _current_customer(request.user)
    if customer is None:
        messages.error(request, "Tài khoản chưa có hồ sơ khách hàng nên chưa thể gửi phản hồi.")
        return redirect("/")
    initial = {}
    if request.GET.get("product", "").isdigit():
        initial["product"] = int(request.GET["product"])
    form = FeedbackCreateForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            create_feedback(customer=customer, **form.cleaned_data)
        except FeedbackServiceError as exc:
            form.add_error("product", str(exc))
        else:
            messages.success(request, "Cảm ơn bạn đã gửi phản hồi! Cửa hàng sẽ phản hồi sớm nhất.")
            return redirect("feedbacks:mine")
    return render(request, "feedback/my_feedback_form.html", {"form": form})


# tv4: 4.2.4 khách hàng xem lại các phản hồi của mình kèm trạng thái và câu trả lời của cửa hàng
@role_required("CUSTOMER")
def my_feedback_list(request):
    customer = _current_customer(request.user)
    if customer is None:
        messages.error(request, "Tài khoản chưa có hồ sơ khách hàng.")
        return redirect("/")
    feedbacks = (Feedback.objects.filter(customer=customer).select_related("product")
                 .order_by("-created_at", "-feedback_id"))
    page = Paginator(feedbacks, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "feedback/my_feedback_list.html", {"page": page})
