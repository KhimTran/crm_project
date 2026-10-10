"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from .api import api
from apps.admin_portal import views as portal_views

urlpatterns = [
    path('', include('apps.accounts.urls_customer')),
    path('', include('apps.customers.urls')),
    path('', include('apps.shop.urls')),
    # Admin Portal
    path('admin-portal/', portal_views.home, name='admin_portal_home'),
    path('admin-portal/login/', portal_views.portal_login, name='login'),
    path('admin-portal/logout/', portal_views.portal_logout, name='logout'),
    path('admin-portal/', include('apps.admin_portal.urls')),

    # API
    path('api/', api.urls),

    # Django built-in admin, chỉ dùng khi phát triển
    path('admin/', admin.site.urls),

    # CRM – khách hàng (TV4)

    # Surveys
    path('surveys/', include('apps.surveys.urls')),
]
