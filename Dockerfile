FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_DEBUG=False python manage.py collectstatic --noinput \
    && useradd --create-home app \
    && chown -R app /app

USER app

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]
