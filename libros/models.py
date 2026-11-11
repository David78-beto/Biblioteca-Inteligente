from django.conf import settings
from django.db import models


class Genero(models.Model):
    nombre = models.CharField('nombre', max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'género'
        verbose_name_plural = 'géneros'

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    titulo = models.CharField('título', max_length=200)
    autor = models.CharField('autor', max_length=200)
    genero = models.ForeignKey(Genero, on_delete=models.PROTECT, verbose_name='género')
    descripcion = models.TextField('descripción', blank=True)
    votos = models.PositiveIntegerField('votos', default=0)

    class Meta:
        ordering = ['titulo']
        verbose_name = 'libro'
        verbose_name_plural = 'libros'

    def __str__(self):
        return self.titulo


class Voto(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='usuario')
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, verbose_name='libro')
    fecha = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'libro'], name='un_voto_por_usuario_y_libro'),
        ]
        verbose_name = 'voto'
        verbose_name_plural = 'votos'

    def __str__(self):
        return f'{self.usuario} → {self.libro}'
