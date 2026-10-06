from django.urls import path
from . import views

app_name = "surveys"
urlpatterns = [
    path("<int:survey_id>/send/", views.send, name="send"),
    path("<int:survey_id>/send-result/", views.send_result, name="send_result"),
    path("recipients/<int:recipient_id>/", views.take, name="take"),
    path("recipients/<int:recipient_id>/submit/", views.submit, name="submit"),
    path("recipients/<int:recipient_id>/result/", views.result, name="result"),
    # TV5 - CRM management (ADMIN or CRM_MANAGER)
    path("manage/", views.manage_list, name="manage_list"),
    path("manage/new/", views.manage_create, name="manage_create"),
    path("manage/<int:survey_id>/", views.manage_detail, name="manage_detail"),
    path("manage/<int:survey_id>/edit/", views.manage_edit, name="manage_edit"),
    path("manage/<int:survey_id>/delete/", views.manage_delete, name="manage_delete"),
    path("manage/<int:survey_id>/close/", views.manage_close, name="manage_close"),
    path("manage/<int:survey_id>/audience/", views.manage_send, name="manage_send"),
    path("manage/<int:survey_id>/stats/", views.manage_stats, name="manage_stats"),
    path("manage/<int:survey_id>/questions/new/", views.question_add, name="question_add"),
    path("manage/<int:survey_id>/questions/<int:question_id>/edit/", views.question_edit, name="question_edit"),
    path("manage/<int:survey_id>/questions/<int:question_id>/delete/", views.question_delete, name="question_delete"),
    path("manage/<int:survey_id>/questions/<int:question_id>/move/<str:direction>/", views.question_move,
         name="question_move"),
    # TV5 - customer
    path("mine/", views.my_surveys, name="my_surveys"),
]
