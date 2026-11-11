from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import LibroForm, RegistroForm
from .models import Genero, Libro, Voto
from .roles import LECTOR


def index(request):
    # Meta.ordering is ignored in aggregation queries, so order explicitly.
    lista_generos = Genero.objects.annotate(total_libros=Count('libro')).order_by('nombre')
    return render(request, 'libros/index.html', {"lista_generos": lista_generos})


def genero(request, genero_id):
    genero = get_object_or_404(Genero, pk=genero_id)
    libros = genero.libro_set.all()
    return render(request, 'libros/genero.html', {"genero": genero, "libros": libros})


def detail(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    ya_voto = request.user.is_authenticated and Voto.objects.filter(usuario=request.user, libro=libro).exists()
    return render(request, 'libros/detail.html', {"libro": libro, "ya_voto": ya_voto})


@login_required
@permission_required('libros.add_libro', raise_exception=True)
def crear(request):
    form = LibroForm(request.POST or None)
    if form.is_valid():
        libro = form.save()
        messages.success(request, f'Se agregó «{libro.titulo}».')
        return redirect('detail', libro_id=libro.id)
    context = {"form": form, "titulo": "Agregar libro"}
    return render(request, 'libros/form.html', context)


@login_required
@permission_required('libros.change_libro', raise_exception=True)
def editar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    form = LibroForm(request.POST or None, instance=libro)
    if form.is_valid():
        form.save()
        messages.success(request, 'Los cambios se guardaron.')
        return redirect('detail', libro_id=libro.id)
    context = {"form": form, "titulo": "Editar libro", "libro": libro}
    return render(request, 'libros/form.html', context)


@login_required
@permission_required('libros.delete_libro', raise_exception=True)
def eliminar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    if request.method == 'POST':
        genero_id = libro.genero_id
        titulo = libro.titulo
        libro.delete()
        messages.success(request, f'Se eliminó «{titulo}».')
        return redirect('genero', genero_id=genero_id)
    return render(request, 'libros/eliminar.html', {"libro": libro})


@login_required
@require_POST
def votar(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    _, creado = Voto.objects.get_or_create(usuario=request.user, libro=libro)
    if creado:
        Libro.objects.filter(pk=libro.pk).update(votos=F('votos') + 1)
        messages.success(request, 'Gracias por tu voto.')
    else:
        messages.info(request, 'Ya habías votado por este libro.')
    return redirect('detail', libro_id=libro.id)


def registro(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = RegistroForm(request.POST or None)
    if form.is_valid():
        usuario = form.save()
        grupo, _ = Group.objects.get_or_create(name=LECTOR)
        usuario.groups.add(grupo)
        login(request, usuario)
        messages.success(request, f'Bienvenido, {usuario.username}. Tu cuenta quedó creada como Lector.')
        return redirect('index')
    return render(request, 'registration/registro.html', {"form": form})
