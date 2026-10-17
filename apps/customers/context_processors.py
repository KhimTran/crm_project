from apps.accounts.constants import AccountRole, AccountStatus
from apps.accounts.models import Account

ADMIN_PORTAL_LAYOUT = "admin/portal/base.html"
MANAGER_PORTAL_LAYOUT = "manager/base.html"
CRM_LAYOUT = "layouts/base_crm.html"


# Chọn khung trang cho màn hình khách hàng/phản hồi: Admin dùng Admin Portal, Manager dùng Manager Portal, Quản lý CRM/CSKH dùng khung CRM
def crm_layout(request):
    user = getattr(request, "user", None)
    is_auth = getattr(user, "is_authenticated", False)
    account = None
    if is_auth and getattr(user, "pk", None):
        account = Account.objects.filter(pk=user.pk, status=AccountStatus.ACTIVE).only("role").first()
    role = account.role if account else None
    in_portal = role in (AccountRole.ADMIN, AccountRole.MANAGER)
    if is_auth and role == AccountRole.ADMIN:
        layout = ADMIN_PORTAL_LAYOUT
    elif is_auth and role == AccountRole.MANAGER:
        layout = MANAGER_PORTAL_LAYOUT
    else:
        layout = CRM_LAYOUT
    return {
        "crm_layout": layout,
        "in_admin_portal": in_portal,
        "date_fmt": "Y-m-d" if in_portal else "d/m/Y",
        "datetime_fmt": "Y-m-d H:i" if in_portal else "d/m/Y H:i",
    }
