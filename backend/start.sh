#!/usr/bin/env sh
# Comando de inicialização em produção (Render).
# O plano grátis do Render não tem "pre-deploy command", então as migrações
# rodam aqui, antes de subir o Gunicorn.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-180}" \
    --access-logfile -
