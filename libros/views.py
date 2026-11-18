from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group
from django.db.models import Count, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from . import servicios
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
        servicios.publicar_evento('/api/eventos/libro', {"libroId": libro.id, "titulo": libro.titulo, "autor": libro.autor})
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
        libro.refresh_from_db(fields=['votos'])
        servicios.publicar_evento('/api/eventos/voto', {"libroId": libro.id, "titulo": libro.titulo, "votos": libro.votos})
        messages.success(request, 'Gracias por tu voto.')
    else:
        messages.info(request, 'Ya habías votado por este libro.')
    return redirect('detail', libro_id=libro.id)


def _sugerencias(resultados):
    existentes = set(Libro.objects.filter(pk__in=[r['id'] for r in resultados]).values_list('pk', flat=True))
    return [
        {**r, "url": reverse('detail', args=[r['id']])}
        for r in resultados if r['id'] in existentes
    ]


@require_GET
def recomendaciones(request, libro_id):
    libro = get_object_or_404(Libro, pk=libro_id)
    try:
        resultados = servicios.recomendar(libro.id)
    except servicios.ServicioNoDisponible:
        return JsonResponse({"recomendaciones": [], "error": "Las recomendaciones no están disponibles."}, status=503)
    return JsonResponse({"recomendaciones": _sugerencias(resultados)})


@require_GET
def buscar(request):
    consulta = request.GET.get('q', '').strip()[:200]
    context = {"consulta": consulta, "resultados": [], "error": None}
    if len(consulta) >= 3:
        try:
            context["resultados"] = _sugerencias(servicios.buscar(consulta))
        except servicios.ServicioNoDisponible:
            context["error"] = 'La búsqueda con IA no está disponible en este momento. Intenta de nuevo en un minuto.'
    elif consulta:
        context["error"] = 'Escribe al menos 3 caracteres.'
    return render(request, 'libros/buscar.html', context)


def _libro_json(libro):
    return {
        "id": libro.id,
        "titulo": libro.titulo,
        "autor": libro.autor,
        "genero": libro.genero.nombre,
        "descripcion": libro.descripcion,
        "votos": libro.votos,
    }


@require_GET
def api_libros(request):
    libros = Libro.objects.select_related('genero')
    return JsonResponse({"libros": [_libro_json(libro) for libro in libros]}, json_dumps_params={"ensure_ascii": False})


@require_GET
def api_libro(request, libro_id):
    libro = Libro.objects.select_related('genero').filter(pk=libro_id).first()
    if libro is None:
        return JsonResponse({"error": "El libro no existe."}, status=404)
    return JsonResponse(_libro_json(libro), json_dumps_params={"ensure_ascii": False})


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
