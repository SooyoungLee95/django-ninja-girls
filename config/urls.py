from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from django.views.decorators.http import require_GET

from src.api import api


@require_GET
def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health_check", health_check),
    path("api/", api.urls),
]
