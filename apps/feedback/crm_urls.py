from django.urls import path

from . import views

# tv4: 4.1.4 route phía quản lý, gắn tại /crm/feedbacks/ (phía khách hàng 4.2.4 dùng URLconf riêng)
app_name = "crm_feedbacks"
urlpatterns = [
    path("", views.feedback_list, name="list"),
    path("<int:feedback_id>/", views.feedback_detail, name="detail"),
]
