#!/bin/sh
set -eu

APP_PORT="${APP_PORT:-8000}"

python manage.py migrate --noinput
python manage.py migrate --check
python manage.py collectstatic --noinput

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

if [ "${DJANGO_DEBUG:-false}" = "true" ]; then
    exec python manage.py runserver "0.0.0.0:${APP_PORT}"
fi

exec gunicorn yt.wsgi:application \
    --bind "0.0.0.0:${APP_PORT}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-120}"
