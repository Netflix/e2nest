"""nest_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
import os

import nest
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, re_path
from django.urls import path
from django.views.generic import RedirectView
from nest_site import settings
from third_party.ranged_response import RangedFileResponse

favicon_view = RedirectView.as_view(
    url=staticfiles_storage.url('nest/images/favicon.ico'), permanent=False)


def mp4_byterange_view(request, path):
    full_path = os.path.join(settings.MEDIA_ROOT, 'mp4', path)
    response = RangedFileResponse(request, open(full_path, 'rb'), content_type='video/mp4')
    response['Content-Disposition'] = f'attachment; filename="{full_path}"'
    return response


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('polls/', include('polls.urls'), name='polls'),
    path('', nest.site.urls, name='nest'),
    re_path(r'^favicon\.ico$', favicon_view, name='favicon'),
    re_path(r'^media/mp4/(?P<path>.*)$', mp4_byterange_view, name='mp4'),
]
