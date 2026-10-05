from django.urls import path

from . import views

# tv4: 4.1.5 route báo cáo khách hàng, gắn tại /crm/reports/customers/
app_name = "customer_reports"
urlpatterns = [
    path("", views.customer_report, name="customers"),
]
