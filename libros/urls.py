from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('genero/<int:genero_id>/', views.genero, name='genero'),
    path('libro/nuevo/', views.crear, name='crear'),
    path('libro/<int:libro_id>/', views.detail, name='detail'),
    path('libro/<int:libro_id>/editar/', views.editar, name='editar'),
    path('libro/<int:libro_id>/eliminar/', views.eliminar, name='eliminar'),
    path('libro/<int:libro_id>/votar/', views.votar, name='votar'),
]