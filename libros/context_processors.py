from .roles import rol_de


def rol(request):
    return {"rol": rol_de(request.user)}
