from django.contrib import admin
from .models import Genero, Libro, Voto


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    search_fields = ['nombre']


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'genero', 'votos', 'dominio_publico']
    list_filter = ['genero', 'dominio_publico']
    search_fields = ['titulo', 'autor', 'descripcion']


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'libro', 'fecha']
    list_filter = ['libro__genero']
    search_fields = ['usuario__username', 'libro__titulo']
