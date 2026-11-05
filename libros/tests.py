from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from .models import Genero, Libro


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.terror = Genero.objects.create(nombre='Terror')
        cls.fantasia = Genero.objects.create(nombre='Fantasía')
        cls.libro = Libro.objects.create(titulo='Drácula', autor='Bram Stoker', genero=cls.terror)
        cls.otro = Libro.objects.create(titulo='El Hobbit', autor='J. R. R. Tolkien', genero=cls.fantasia)


class ConsultaTests(BaseTestCase):
    def test_raiz_redirige_al_catalogo(self):
        self.assertRedirects(self.client.get('/'), reverse('index'))

    def test_index_lista_generos_con_total(self):
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'Terror')
        self.assertEqual(response.context['lista_generos'].get(pk=self.terror.pk).total_libros, 1)

    def test_genero_muestra_solo_sus_libros(self):
        response = self.client.get(reverse('genero', args=[self.terror.pk]))
        self.assertContains(response, 'Drácula')
        self.assertNotContains(response, 'El Hobbit')

    def test_detalle_muestra_el_libro(self):
        response = self.client.get(reverse('detail', args=[self.libro.pk]))
        self.assertContains(response, 'Bram Stoker')

    def test_id_inexistente_devuelve_404(self):
        for nombre in ['genero', 'detail', 'editar', 'eliminar']:
            with self.subTest(vista=nombre):
                response = self.client.get(reverse(nombre, args=[9999]))
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, 'Volver al catálogo', status_code=404)


class GestionTests(BaseTestCase):
    def test_crear_libro(self):
        datos = {'titulo': 'It', 'autor': 'Stephen King', 'genero': self.terror.pk}
        response = self.client.post(reverse('crear'), datos)
        libro = Libro.objects.get(titulo='It')
        self.assertRedirects(response, reverse('detail', args=[libro.pk]))
        self.assertEqual(libro.votos, 0)
        self.assertEqual(len(get_messages(response.wsgi_request)), 1)

    def test_formulario_esta_en_espanol(self):
        self.assertContains(self.client.get(reverse('crear')), 'Selecciona un género')

    def test_crear_libro_invalido_muestra_errores(self):
        response = self.client.post(reverse('crear'), {'titulo': '', 'autor': '', 'genero': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Libro.objects.count(), 2)

    def test_editar_libro(self):
        datos = {'titulo': 'Drácula (edición anotada)', 'autor': 'Bram Stoker', 'genero': self.terror.pk}
        self.client.post(reverse('editar', args=[self.libro.pk]), datos)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.titulo, 'Drácula (edición anotada)')

    def test_editar_no_cambia_los_votos(self):
        Libro.objects.filter(pk=self.libro.pk).update(votos=7)
        datos = {'titulo': 'Drácula', 'autor': 'Bram Stoker', 'genero': self.terror.pk, 'votos': 0}
        self.client.post(reverse('editar', args=[self.libro.pk]), datos)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 7)

    def test_eliminar_pide_confirmacion(self):
        self.client.get(reverse('eliminar', args=[self.libro.pk]))
        self.assertTrue(Libro.objects.filter(pk=self.libro.pk).exists())

    def test_eliminar_con_post_borra_el_libro(self):
        response = self.client.post(reverse('eliminar', args=[self.libro.pk]))
        self.assertRedirects(response, reverse('genero', args=[self.terror.pk]))
        self.assertFalse(Libro.objects.filter(pk=self.libro.pk).exists())

    def test_genero_con_libros_no_se_puede_borrar(self):
        with self.assertRaises(ProtectedError):
            self.terror.delete()


class VotoTests(BaseTestCase):
    def test_votar_suma_uno(self):
        url = reverse('votar', args=[self.libro.pk])
        self.client.post(url)
        self.client.post(url)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 2)

    def test_votar_con_get_no_esta_permitido(self):
        response = self.client.get(reverse('votar', args=[self.libro.pk]))
        self.assertEqual(response.status_code, 405)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 0)


class AdminTests(BaseTestCase):
    def test_panel_lista_y_busca_libros(self):
        admin = get_user_model().objects.create_superuser('admin', 'admin@example.com', 'clave-de-prueba')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:libros_libro_changelist'), {'q': 'Drácula'})
        self.assertContains(response, 'Bram Stoker')
        self.assertNotContains(response, 'Tolkien')
