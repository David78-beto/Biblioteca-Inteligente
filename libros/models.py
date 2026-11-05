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
    votos = models.PositiveIntegerField('votos', default=0)

    class Meta:
        ordering = ['titulo']
        verbose_name = 'libro'
        verbose_name_plural = 'libros'

    def __str__(self):
        return self.titulo
