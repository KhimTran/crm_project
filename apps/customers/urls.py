from django.urls import path

from . import views

app_name = "customers"
urlpatterns = [path("account/profile/", views.profile, name="profile")]
