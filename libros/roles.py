LECTOR = 'Lector'
BIBLIOTECARIO = 'Bibliotecario'
ADMINISTRADOR = 'Administrador'


def rol_de(usuario):
    if not usuario.is_authenticated:
        return None
    if usuario.is_superuser:
        return ADMINISTRADOR
    if usuario.groups.filter(name=BIBLIOTECARIO).exists():
        return BIBLIOTECARIO
    return LECTOR
