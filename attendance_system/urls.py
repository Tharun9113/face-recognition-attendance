"""
URL configuration for attendance_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.contrib.auth import views as auth_views
from attendance import views
from attendance.views import CustomLoginView

# Override admin password reset URLs
admin.site.password_reset = views.request_password_reset
admin.site.password_reset_done = views.request_password_reset
admin.site.password_reset_confirm = views.verify_otp
admin.site.password_reset_complete = views.request_password_reset

urlpatterns = [
    # Custom password reset URLs - these must come before admin URLs
    path('admin/password_reset/', views.request_password_reset),
    path('admin/password_reset/done/', views.request_password_reset),
    path('reset/<uidb64>/<token>/', views.request_password_reset),
    path('reset/done/', views.request_password_reset),
    
    # Main password reset URLs
    path('password_reset/', views.request_password_reset, name='password_reset'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    
    # Authentication URLs
    path('', CustomLoginView.as_view(), name='login'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Main app URLs
    path('', include('attendance.urls')),
    
    # Admin URLs should come last
    path('admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
