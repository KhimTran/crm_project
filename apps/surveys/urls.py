from django.urls import path
from . import views

app_name = "surveys"
urlpatterns = [
    path("<int:survey_id>/send/", views.send, name="send"),
    path("<int:survey_id>/send-result/", views.send_result, name="send_result"),
    path("recipients/<int:recipient_id>/", views.take, name="take"),
    path("recipients/<int:recipient_id>/submit/", views.submit, name="submit"),
    path("recipients/<int:recipient_id>/result/", views.result, name="result"),
]
