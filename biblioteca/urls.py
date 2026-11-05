from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='index')),
    path('libros/', include('libros.urls')),
    path('admin/', admin.site.urls),
]
