import json
import logging
import threading
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

# El plan gratuito de Render puede tardar cerca de un minuto en despertar el servicio.
TIEMPO_CONSULTA = 75
TIEMPO_EVENTO = 75


class ServicioNoDisponible(Exception):
    pass


def _post(ruta, datos, tiempo):
    if not settings.NODE_SERVICE_URL:
        raise ServicioNoDisponible('El microservicio no está configurado.')
    peticion = Request(
        f'{settings.NODE_SERVICE_URL}{ruta}',
        data=json.dumps(datos).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'X-Servicio-Token': settings.SERVICIO_TOKEN},
        method='POST',
    )
    try:
        with urlopen(peticion, timeout=tiempo) as respuesta:
            return json.load(respuesta)
    except (URLError, TimeoutError, ValueError) as error:
        logger.warning('Falló la llamada a %s: %s', ruta, error)
        raise ServicioNoDisponible(str(error)) from error


def recomendar(libro_id, limite=3):
    return _post('/api/recomendaciones', {'libroId': libro_id, 'limite': limite}, TIEMPO_CONSULTA)['recomendaciones']


def buscar(consulta, limite=5):
    return _post('/api/busqueda', {'consulta': consulta, 'limite': limite}, TIEMPO_CONSULTA)['resultados']


def _enviar_evento(ruta, datos):
    try:
        _post(ruta, datos, TIEMPO_EVENTO)
    except ServicioNoDisponible:
        pass


def publicar_evento(ruta, datos):
    if settings.NODE_SERVICE_URL:
        threading.Thread(target=_enviar_evento, args=(ruta, datos), daemon=True).start()
