#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py bootstrap_admin --skip-if-missing
python manage.py collectstatic --noinput

exec "$@"
