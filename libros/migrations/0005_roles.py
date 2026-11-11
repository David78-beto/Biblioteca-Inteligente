from django.contrib.auth.management import create_permissions
from django.db import migrations

PERMISOS = {
    'Lector': ['add_voto'],
    'Bibliotecario': ['add_voto', 'add_libro', 'change_libro', 'delete_libro'],
}


def crear_roles(apps, schema_editor):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    for nombre, codigos in PERMISOS.items():
        grupo, _ = Group.objects.get_or_create(name=nombre)
        grupo.permissions.set(Permission.objects.filter(content_type__app_label='libros', codename__in=codigos))


def borrar_roles(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=PERMISOS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('libros', '0004_libro_descripcion_voto'),
    ]

    operations = [
        migrations.RunPython(crear_roles, borrar_roles),
    ]
