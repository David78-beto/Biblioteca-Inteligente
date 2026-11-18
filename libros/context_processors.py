from django.conf import settings

from .roles import rol_de


def rol(request):
    return {"rol": rol_de(request.user)}


def microservicio(request):
    return {
        "ia_disponible": bool(settings.NODE_SERVICE_URL),
        "node_public_url": settings.NODE_PUBLIC_URL,
    }
