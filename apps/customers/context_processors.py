from apps.accounts.constants import AccountRole

ADMIN_PORTAL_LAYOUT = "admin_portal/base.html"
CRM_LAYOUT = "layouts/base_crm.html"


# tv4: chọn khung trang cho màn hình khách hàng/phản hồi: Admin ở trong Admin Portal, Quản lý CRM/CSKH dùng khung CRM
def crm_layout(request):
    user = getattr(request, "user", None)
    in_portal = getattr(user, "is_authenticated", False) and getattr(user, "role", None) == AccountRole.ADMIN
    return {
        "crm_layout": ADMIN_PORTAL_LAYOUT if in_portal else CRM_LAYOUT,
        "in_admin_portal": in_portal,
        # Admin Portal hiển thị ngày kiểu Y-m-d như trang Products
        "date_fmt": "Y-m-d" if in_portal else "d/m/Y",
        "datetime_fmt": "Y-m-d H:i" if in_portal else "d/m/Y H:i",
    }
