from django.core.management import call_command
from django.core.management.base import BaseCommand
from libros.models import Libro


class Command(BaseCommand):
    help = 'Carga el catálogo de ejemplo solo si la base de datos no tiene libros.'

    def handle(self, *args, **options):
        if Libro.objects.exists():
            self.stdout.write('El catálogo ya tiene libros; no se cargó nada.')
            return
        call_command('loaddata', 'catalogo_inicial', verbosity=0)
        self.stdout.write(self.style.SUCCESS(f'Se cargaron {Libro.objects.count()} libros.'))
