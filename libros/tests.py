from django.contrib.auth.models import Group, User
from django.contrib.messages import get_messages
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from .models import Genero, Libro, Voto
from .roles import ADMINISTRADOR, BIBLIOTECARIO, LECTOR, rol_de


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.terror = Genero.objects.create(nombre='Terror')
        cls.fantasia = Genero.objects.create(nombre='Fantasía')
        cls.libro = Libro.objects.create(titulo='Drácula', autor='Bram Stoker', genero=cls.terror)
        cls.otro = Libro.objects.create(titulo='El Hobbit', autor='J. R. R. Tolkien', genero=cls.fantasia)
        cls.lector = User.objects.create_user('lectora', password='clave-de-prueba-123')
        cls.lector.groups.add(Group.objects.get(name=LECTOR))
        cls.bibliotecario = User.objects.create_user('bibliotecario', password='clave-de-prueba-123')
        cls.bibliotecario.groups.add(Group.objects.get(name=BIBLIOTECARIO))
        cls.admin = User.objects.create_superuser('admin', 'admin@example.com', 'clave-de-prueba-123')


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

    def test_detalle_muestra_el_libro_y_su_descripcion(self):
        Libro.objects.filter(pk=self.libro.pk).update(descripcion='Un conde que se alimenta de sangre.')
        response = self.client.get(reverse('detail', args=[self.libro.pk]))
        self.assertContains(response, 'Bram Stoker')
        self.assertContains(response, 'Un conde que se alimenta de sangre.')

    def test_id_inexistente_devuelve_404(self):
        self.client.force_login(self.bibliotecario)
        for nombre in ['genero', 'detail', 'editar', 'eliminar']:
            with self.subTest(vista=nombre):
                response = self.client.get(reverse(nombre, args=[9999]))
                self.assertEqual(response.status_code, 404)
                self.assertContains(response, 'Volver al catálogo', status_code=404)


class RegistroLoginTests(BaseTestCase):
    def test_registro_crea_un_lector_e_inicia_sesion(self):
        datos = {'username': 'nuevo', 'email': 'nuevo@example.com',
                 'password1': 'UnaClaveSegura-2026', 'password2': 'UnaClaveSegura-2026'}
        response = self.client.post(reverse('registro'), datos)
        self.assertRedirects(response, reverse('index'))
        usuario = User.objects.get(username='nuevo')
        self.assertTrue(usuario.groups.filter(name=LECTOR).exists())
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_registro_rechaza_claves_distintas(self):
        datos = {'username': 'nuevo', 'password1': 'UnaClaveSegura-2026', 'password2': 'OtraClave-2026'}
        response = self.client.post(reverse('registro'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuevo').exists())

    def test_login_correcto(self):
        response = self.client.post(reverse('login'), {'username': 'lectora', 'password': 'clave-de-prueba-123'})
        self.assertRedirects(response, reverse('index'))

    def test_login_con_clave_incorrecta_se_rechaza(self):
        response = self.client.post(reverse('login'), {'username': 'lectora', 'password': 'equivocada'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_salir_cierra_la_sesion(self):
        self.client.force_login(self.lector)
        self.client.post(reverse('logout'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_menu_muestra_usuario_y_rol(self):
        self.client.force_login(self.bibliotecario)
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'bibliotecario')
        self.assertContains(response, 'Agregar libro')


class RolesTests(BaseTestCase):
    def test_rol_de_cada_usuario(self):
        self.assertEqual(rol_de(self.lector), LECTOR)
        self.assertEqual(rol_de(self.bibliotecario), BIBLIOTECARIO)
        self.assertEqual(rol_de(self.admin), ADMINISTRADOR)

    def test_anonimo_debe_iniciar_sesion_para_gestionar(self):
        response = self.client.get(reverse('crear'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('crear')}")

    def test_lector_no_puede_gestionar_el_catalogo(self):
        self.client.force_login(self.lector)
        for url in [reverse('crear'), reverse('editar', args=[self.libro.pk]), reverse('eliminar', args=[self.libro.pk])]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)
        self.client.post(reverse('eliminar', args=[self.libro.pk]))
        self.assertTrue(Libro.objects.filter(pk=self.libro.pk).exists())

    def test_lector_no_ve_botones_de_gestion(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('detail', args=[self.libro.pk]))
        self.assertNotContains(response, 'Editar')
        self.assertNotContains(response, 'Agregar libro')

    def test_lector_no_entra_al_panel_de_administracion(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 302)


class GestionTests(BaseTestCase):
    def setUp(self):
        self.client.force_login(self.bibliotecario)

    def test_crear_libro(self):
        datos = {'titulo': 'It', 'autor': 'Stephen King', 'genero': self.terror.pk, 'descripcion': 'Un payaso.'}
        response = self.client.post(reverse('crear'), datos)
        libro = Libro.objects.get(titulo='It')
        self.assertRedirects(response, reverse('detail', args=[libro.pk]))
        self.assertEqual(libro.descripcion, 'Un payaso.')
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
    def test_votar_requiere_iniciar_sesion(self):
        response = self.client.post(reverse('votar', args=[self.libro.pk]))
        self.assertEqual(response.status_code, 302)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 0)

    def test_un_voto_por_usuario_y_libro(self):
        self.client.force_login(self.lector)
        url = reverse('votar', args=[self.libro.pk])
        self.client.post(url)
        self.client.post(url)
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 1)
        self.assertEqual(Voto.objects.filter(libro=self.libro).count(), 1)

    def test_usuarios_distintos_suman_votos(self):
        for usuario in [self.lector, self.bibliotecario]:
            self.client.force_login(usuario)
            self.client.post(reverse('votar', args=[self.libro.pk]))
        self.libro.refresh_from_db()
        self.assertEqual(self.libro.votos, 2)

    def test_detalle_indica_que_ya_voto(self):
        self.client.force_login(self.lector)
        self.client.post(reverse('votar', args=[self.libro.pk]))
        self.assertContains(self.client.get(reverse('detail', args=[self.libro.pk])), 'Ya votaste')

    def test_votar_con_get_no_esta_permitido(self):
        self.client.force_login(self.lector)
        response = self.client.get(reverse('votar', args=[self.libro.pk]))
        self.assertEqual(response.status_code, 405)


class AdminTests(BaseTestCase):
    def test_panel_lista_y_busca_libros(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('admin:libros_libro_changelist'), {'q': 'Drácula'})
        self.assertContains(response, 'Bram Stoker')
        self.assertNotContains(response, 'Tolkien')

    def test_panel_muestra_votos(self):
        Voto.objects.create(usuario=self.lector, libro=self.libro)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('admin:libros_voto_changelist')), 'lectora')
