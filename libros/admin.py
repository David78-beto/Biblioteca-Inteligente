from django.contrib import admin
from .models import Genero, Libro


@admin.register(Genero)
class GeneroAdmin(admin.ModelAdmin):
    search_fields = ['nombre']


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'autor', 'genero', 'votos']
    list_filter = ['genero']
    search_fields = ['titulo', 'autor']
