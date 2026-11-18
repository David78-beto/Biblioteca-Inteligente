from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from libros import views as libros_views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='index')),
    path('libros/', include('libros.urls')),
    path('api/libros/', libros_views.api_libros, name='api_libros'),
    path('api/libros/<int:libro_id>/', libros_views.api_libro, name='api_libro'),
    path('cuentas/registro/', libros_views.registro, name='registro'),
    path('cuentas/entrar/', auth_views.LoginView.as_view(), name='login'),
    path('cuentas/salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
]
