from django.urls import path

from . import views

# tv4: 4.2.4 route phía khách hàng, gắn tại /feedbacks/
app_name = "feedbacks"
urlpatterns = [
    path("new/", views.my_feedback_create, name="create"),
    path("mine/", views.my_feedback_list, name="mine"),
]
