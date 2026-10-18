from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.managers import AccountManager
from apps.accounts.models import Account
from apps.feedback.models import Feedback
from apps.surveys.models import SurveyRecipient

from .constants import CustomerStatus, PreferenceType
from .errors import (
    CustomerAlreadyActive, CustomerAlreadyDeleted, CustomerAlreadyLocked, CustomerNotFound,
    DuplicateCustomerEmail, DuplicateCustomerPhone,
)
from .models import Customer, CustomerPreference


@transaction.atomic
def create_customer(*, email, password, full_name, phone, date_of_birth=None, gender=None, address=None,
                    playing_level=None, play_styles=(), brands=()):
    """Create a CUSTOMER account and profile atomically using Django password validation/hashing."""
    email = AccountManager.normalize_account_email(email)
    if Account.objects.filter(email=email).exists():
        raise DuplicateCustomerEmail("Email đã được sử dụng")
    if phone and Customer.objects.filter(phone=phone).exclude(status=CustomerStatus.DELETED).exists():
        raise DuplicateCustomerPhone("Số điện thoại đã được sử dụng")

    try:
        with transaction.atomic():
            account = Account.objects.create_user(email, password, role=AccountRole.CUSTOMER)
    except (IntegrityError, ValidationError) as exc:
        if Account.objects.filter(email=email).exists():
            raise DuplicateCustomerEmail("Email đã được sử dụng") from exc
        raise

    customer = Customer.objects.create(
        account=account,
        full_name=full_name,
        phone=phone or None,
        date_of_birth=date_of_birth,
        gender=gender or None,
        address=address or None,
        playing_level=playing_level or None,
        status=CustomerStatus.ACTIVE,
    )
    preferences = [CustomerPreference(customer=customer, preference_type=PreferenceType.PLAY_STYLE, preference_value=v)
                   for v in play_styles]
    preferences += [CustomerPreference(customer=customer, preference_type=PreferenceType.BRAND, preference_value=v)
                    for v in brands]
    CustomerPreference.objects.bulk_create(preferences)
    return customer


# tv4: lấy khách hàng chưa bị xóa và khóa dòng (select_for_update) để thao tác an toàn
def _active_customer_for_update(customer_id):
    customer = Customer.objects.select_for_update().select_related("account").filter(pk=customer_id).first()
    if customer is None:
        raise CustomerNotFound("Không tìm thấy khách hàng")
    if customer.status == CustomerStatus.DELETED:
        raise CustomerAlreadyDeleted("Khách hàng đã bị xóa")
    return customer


# tv4: đổi trạng thái tài khoản (ACTIVE/LOCKED) của khách hàng, cập nhật luôn updated_at
def _set_account_status(account, status):
    Account.objects.filter(pk=account.pk).update(status=status, updated_at=timezone.now())
    account.refresh_from_db()


# tv4: đếm dữ liệu liên quan (phản hồi, khảo sát) để cảnh báo trước khi xóa khách hàng
def customer_related_counts(customer):
    recipients = SurveyRecipient.objects.filter(customer=customer)
    return {
        "feedbacks": Feedback.objects.filter(customer=customer).count(),
        "surveys_sent": recipients.count(),
        "surveys_answered": recipients.filter(response__isnull=False).count(),
    }


# tv4: 4.1.3 khóa tài khoản khách hàng (accounts.status = LOCKED)
@transaction.atomic
def lock_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    if customer.account.status == AccountStatus.LOCKED:
        raise CustomerAlreadyLocked("Tài khoản khách hàng đã bị khóa")
    _set_account_status(customer.account, AccountStatus.LOCKED)
    return customer


# tv4: 4.1.3 mở khóa tài khoản khách hàng (accounts.status = ACTIVE)
@transaction.atomic
def unlock_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    if customer.account.status == AccountStatus.ACTIVE:
        raise CustomerAlreadyActive("Tài khoản khách hàng đang hoạt động")
    _set_account_status(customer.account, AccountStatus.ACTIVE)
    return customer


# tv4: 4.1.2 xóa mềm khách hàng (status DELETED + deleted_at) và khóa tài khoản; giữ lại phản hồi/khảo sát
@transaction.atomic
def delete_customer(customer_id):
    customer = _active_customer_for_update(customer_id)
    customer.status = CustomerStatus.DELETED
    customer.deleted_at = timezone.now()
    customer.save(update_fields=["status", "deleted_at", "updated_at"])
    if customer.account.status != AccountStatus.LOCKED:
        _set_account_status(customer.account, AccountStatus.LOCKED)
    return customer
