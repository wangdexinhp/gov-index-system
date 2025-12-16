"""
URL configuration for core project.

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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from apps.accounts.views import CustomSignupView, RefreshCaptchaView, SendSmsCodeView, CheckMobileView

urlpatterns = [
    # 1. 根路径重定向到 landing 首页
    path('', RedirectView.as_view(url='/landing/'), name='home'),

    # 如果 landing 应用没有空路径路由，也可以直接重定向到具体页面
    # path('', RedirectView.as_view(url='/landing/index/'), name='home'),

    # 或者使用 pattern_name（如果 landing 应用有命名路由）
    # path('', RedirectView.as_view(pattern_name='landing:index'), name='home'),

    # 2. 原有路由保持不变
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('landing/', include('apps.landing.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('subscriptions/', include('apps.subscriptions.urls')),
    path('captcha/', include('captcha.urls')),

    path('send-sms-code/', SendSmsCodeView.as_view(), name='send_sms_code'),
    path('refresh-captcha/', RefreshCaptchaView.as_view(), name='refresh_captcha'),
    path('check-mobile/', CheckMobileView.as_view(), name='check_mobile'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)