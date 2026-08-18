"""yt URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.views.generic import RedirectView
from django.views.generic.edit import CreateView

from video.account_views import current_profile
from .forms import RegistrationForm

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='video_list', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path(
        'accounts/register/',
        CreateView.as_view(
            template_name='registration/register.html',
            form_class=RegistrationForm,
            success_url=reverse_lazy('login'),
        ),
        name='register',
    ),
    path('accounts/profile/', current_profile, name='current_profile'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('monetization/', include('monetization.urls')),
    path('videos/', include('video.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
