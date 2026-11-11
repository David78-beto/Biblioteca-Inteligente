#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py cargar_catalogo_inicial

if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    python manage.py createsuperuser --noinput || echo "El superusuario ya existe."
fi

exec gunicorn biblioteca.wsgi:application --bind "0.0.0.0:${PORT}" --workers 2
