"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from .api import api

urlpatterns = [
    path('', include('apps.accounts.urls_customer')),
    path('', include('apps.customers.urls')),
    path('', include('apps.shop.urls')),

    # Django built-in admin relocated to /django-admin/ (development only)
    path('django-admin/', admin.site.urls),

    # Custom Admin UI (Role: ADMIN) mounted at /admin/
    path('admin/', include('apps.admin_portal.urls_admin')),

    # Manager UI (Role: MANAGER) mounted at /manager/
    path('manager/', include('apps.admin_portal.urls_manager')),

    # API
    path('api/', api.urls),

    # CRM – khách hàng (TV4)
    path('crm/feedbacks/', include('apps.feedback.crm_urls')),
    path('crm/reports/customers/', include('apps.customers.report_urls')),

    # Phản hồi phía khách hàng (TV4)
    path('feedbacks/', include('apps.feedback.urls')),

    # Surveys
    path('surveys/', include('apps.surveys.urls')),
]
