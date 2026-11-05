from django.contrib import messages
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import LibroForm
from .models import Genero, Libro


def index(request):
    lista_generos = Genero.objects.annotate(total_libros=Count('libro'))
    return render(request, 'libros/index.html', {"lista_generos": lista_generos})


def genero(request, genero_id):
    genero = get_object_or_404(Genero, pk=genero_id)
    libros = genero.libro_set.all()
    return render(request, 'libros/genero.html', {"genero": genero, "libros": libros})


def detail(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    return render(request, 'libros/detail.html', {"libro": libro})


def crear(request):
    form = LibroForm(request.POST or None)
    if form.is_valid():
        libro = form.save()
        messages.success(request, f'Se agregó «{libro.titulo}».')
        return redirect('detail', libro_id=libro.id)
    context = {"form": form, "titulo": "Agregar libro"}
    return render(request, 'libros/form.html', context)


def editar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    form = LibroForm(request.POST or None, instance=libro)
    if form.is_valid():
        form.save()
        messages.success(request, 'Los cambios se guardaron.')
        return redirect('detail', libro_id=libro.id)
    context = {"form": form, "titulo": "Editar libro", "libro": libro}
    return render(request, 'libros/form.html', context)


def eliminar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    if request.method == 'POST':
        genero_id = libro.genero_id
        titulo = libro.titulo
        libro.delete()
        messages.success(request, f'Se eliminó «{titulo}».')
        return redirect('genero', genero_id=genero_id)
    return render(request, 'libros/eliminar.html', {"libro": libro})


@require_POST
def votar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    Libro.objects.filter(pk=libro.pk).update(votos=F('votos') + 1)
    return redirect('detail', libro_id=libro.id)
