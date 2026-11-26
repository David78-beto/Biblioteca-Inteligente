from django.db import migrations

# Solo fuentes legales: obras de dominio público o su ficha en el catálogo mundial de bibliotecas.
ENLACES = {
    'Drácula': ('https://standardebooks.org/ebooks/bram-stoker/dracula', True),
    'Orgullo y prejuicio': ('https://es.wikisource.org/wiki/Orgullo_y_prejuicio', True),
    'Romeo y Julieta': ('https://es.wikisource.org/wiki/Romeo_y_Julieta_(Men%C3%A9ndez_y_Pelayo_tr.)', True),
    'El Exorcista': ('https://search.worldcat.org/search?q=El+exorcista+William+Peter+Blatty', False),
    'It': ('https://search.worldcat.org/search?q=It+Stephen+King', False),
    'Cosmos': ('https://search.worldcat.org/search?q=Cosmos+Carl+Sagan', False),
    'Breve historia del tiempo': ('https://search.worldcat.org/search?q=Breve+historia+del+tiempo+Stephen+Hawking', False),
    'Dune': ('https://search.worldcat.org/search?q=Dune+Frank+Herbert', False),
    'Fundación': ('https://search.worldcat.org/search?q=Fundacion+Isaac+Asimov', False),
    '1984': ('https://search.worldcat.org/search?q=1984+George+Orwell', False),
    'El Hobbit': ('https://search.worldcat.org/search?q=El+Hobbit+Tolkien', False),
    'Harry Potter y la piedra filosofal': ('https://search.worldcat.org/search?q=Harry+Potter+y+la+piedra+filosofal+Rowling', False),
    'Asesinato en el Orient Express': ('https://search.worldcat.org/search?q=Asesinato+en+el+Orient+Express+Agatha+Christie', False),
    'El código Da Vinci': ('https://search.worldcat.org/search?q=El+codigo+Da+Vinci+Dan+Brown', False),
}


def cargar_enlaces(apps, schema_editor):
    Libro = apps.get_model('libros', 'Libro')
    for titulo, (enlace, dominio_publico) in ENLACES.items():
        Libro.objects.filter(titulo=titulo, enlace_lectura='').update(
            enlace_lectura=enlace, dominio_publico=dominio_publico)


class Migration(migrations.Migration):

    dependencies = [
        ('libros', '0006_libro_enlace_lectura'),
    ]

    operations = [
        migrations.RunPython(cargar_enlaces, migrations.RunPython.noop),
    ]
